import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fedops_core.db.models import Resume, StoredFile, Entity
from fedops_core.schemas.resume_schemas import ResumeData
from fedops_core.services.ai_service import AIService
from unstructured.partition.auto import partition
import os

logger = logging.getLogger(__name__)

class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def create_resume_entry(self, stored_file_id: int, user_id: str = None) -> Resume:
        """Creates a new Resume entry in the database."""
        resume = Resume(
            stored_file_id=stored_file_id,
            user_id=user_id,
            status="UPLOADED"
        )
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

    async def parse_resume(self, resume_id: int) -> Resume:
        """
        Parses the resume file using unstructured and then processing with AI.
        """
        # Fetch resume and file
        result = await self.db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise ValueError("Resume not found")

        result_file = await self.db.execute(select(StoredFile).where(StoredFile.id == resume.stored_file_id))
        stored_file = result_file.scalar_one_or_none()
        
        if not stored_file or not stored_file.file_path or not os.path.exists(stored_file.file_path):
             resume.status = "FAILED"
             resume.error_message = "File not found"
             await self.db.commit()
             return resume

        try:
            resume.status = "PROCESSING"
            await self.db.commit()

            # 1. Extract text using Unstructured
            elements = partition(filename=stored_file.file_path)
            raw_text = "\n\n".join([str(el) for el in elements])
            resume.raw_text = raw_text
            
            # 2. Parse with AI
            prompt = f"""
            You are an expert Resume Parser.
            Extract structured data from the following resume text.
            
            RESUME TEXT:
            {raw_text[:30000]} # Limit context window if needed
            
            TASK: Return a valid JSON object matching the following structure:
            - contact_info (name, email, phone, address, linkedin, website)
            - summary
            - experience (list of company, title, start_date, end_date, description)
            - education (list of institution, degree, etc.)
            - skills (grouped by category)
            - certifications (list of strings)
            - security_clearance (level, status)
            
            Ensure dates are standardized (YYYY-MM) if possible.
            """
            
            # Use analyze_with_schema for strict Pydantic validation
            parsed_data_model = await self.ai_service.analyze_with_schema(prompt, ResumeData)
            
            if parsed_data_model:
                resume.parsed_data = parsed_data_model.model_dump(mode='json')
                resume.status = "PARSED"
            else:
                resume.status = "FAILED"
                resume.error_message = "AI Parsing failed"

        except Exception as e:
            logger.error(f"Error parsing resume {resume_id}: {e}")
            resume.status = "FAILED"
            resume.error_message = str(e)
        
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

    async def generate_formatted_resume(self, resume_id: int, include_signature: bool = False) -> Resume:
        """
        Generates an HTML formatted resume based on parsed data and Primary Entity branding.
        """
        result = await self.db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()
        
        if not resume or not resume.parsed_data:
            raise ValueError("Resume not available or not parsed")
            
        # Get Primary Entity for Letterhead
        result_entity = await self.db.execute(select(Entity).where(Entity.is_primary == True))
        primary_entity = result_entity.scalar_one_or_none()
        
        data = ResumeData(**resume.parsed_data)
        
        # Simple HTML Template Construction
        # In a real scenario, this might use Jinja2. For now, f-strings are fine for proof of concept.
        
        # Header
        header_html = ""
        if primary_entity:
            logo_img = f'<img src="{primary_entity.logo_url}" style="max-height: 80px;">' if primary_entity.logo_url else ""
            header_html = f"""
            <div style="border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 style="margin: 0; color: #1a202c;">{primary_entity.legal_business_name}</h1>
                    <p style="margin: 5px 0; color: #4a5568;">Providing Excellence in Government Services</p>
                </div>
                {logo_img}
            </div>
            """
        
        # Resume HTML
        contact_links = []
        if data.contact_info.email: contact_links.append(f'<a href="mailto:{data.contact_info.email}">{data.contact_info.email}</a>')
        if data.contact_info.phone: contact_links.append(data.contact_info.phone)
        if data.contact_info.linkedin: contact_links.append(f'<a href="{data.contact_info.linkedin}">LinkedIn</a>')
        
        content_html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #333; line-height: 1.6;">
            {header_html}
            
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="margin: 0; font-size: 28px; text-transform: uppercase; letter-spacing: 1px;">{data.contact_info.name}</h2>
                <div style="margin-top: 10px; font-size: 14px;">{' | '.join(contact_links)}</div>
                 {f'<div style="margin-top: 5px;">{data.contact_info.address}</div>' if data.contact_info.address else ''}
            </div>
            
            {f'<div style="margin-bottom: 25px;"><h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; text-transform: uppercase; font-size: 16px; color: #2d3748;">Professional Summary</h3><p>{data.summary}</p></div>' if data.summary else ''}
            
            <div style="margin-bottom: 25px;">
                <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; text-transform: uppercase; font-size: 16px; color: #2d3748;">Experience</h3>
                {''.join([self._format_experience(exp) for exp in data.experience])}
            </div>
            
             <div style="margin-bottom: 25px;">
                <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; text-transform: uppercase; font-size: 16px; color: #2d3748;">Education</h3>
                {''.join([self._format_education(edu) for edu in data.education])}
            </div>
            
            {self._format_skills(data.skills)}
            
            {self._format_signature(include_signature, data.contact_info.name)}
            
        </div>
        """
        
        resume.formatted_content_html = content_html
        await self.db.commit()
        return resume

    def _format_experience(self, exp):
        description_bullets = "".join([f"<li>{item}</li>" for item in (exp.description or [])])
        return f"""
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; font-weight: bold;">
                <span>{exp.title}</span>
                <span>{exp.start_date or ''} - {exp.end_date or 'Present'}</span>
            </div>
            <div style="font-style: italic; color: #555;">{exp.company}, {exp.location or ''}</div>
            <ul style="margin-top: 5px; padding-left: 20px;">
                {description_bullets}
            </ul>
        </div>
        """

    def _format_education(self, edu):
        return f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-weight: bold;">
                <span>{edu.institution}</span>
                <span>{edu.end_date or ''}</span>
            </div>
            <div>{edu.degree}{f', {edu.field_of_study}' if edu.field_of_study else ''}</div>
        </div>
        """

    def _format_skills(self, skills):
        if not skills: return ""
        items = []
        for cat in skills:
            items.append(f"<p><strong>{cat.category or 'Skills'}:</strong> {', '.join(cat.skills)}</p>")
        
        return f"""
        <div style="margin-bottom: 25px;">
            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; text-transform: uppercase; font-size: 16px; color: #2d3748;">Skills</h3>
            {''.join(items)}
        </div>
        """

    def _format_signature(self, include_signature, name):
        if not include_signature: return ""
        return f"""
        <div style="margin-top: 50px; page-break-inside: avoid;">
            <p style="margin-bottom: 40px; border-bottom: 1px solid #000; width: 300px;"></p>
            <p><strong>{name}</strong></p>
            <p>Date: _________________</p>
        </div>
        """
