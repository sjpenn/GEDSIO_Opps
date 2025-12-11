from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import date

class ResumeContactInfo(BaseModel):
    name: str = Field(..., description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address or location")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    website: Optional[str] = Field(None, description="Personal website or portfolio")

class ResumeEducation(BaseModel):
    institution: str = Field(..., description="Name of the university or school")
    degree: str = Field(..., description="Degree obtained (e.g., BS, MS)")
    field_of_study: Optional[str] = Field(None, description="Major or field of study")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or YYYY)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM or YYYY)")
    gpa: Optional[str] = Field(None, description="GPA if listed")

class ResumeExperience(BaseModel):
    company: str = Field(default="Unknown", description="Company or organization name")
    title: str = Field(..., description="Job title")
    location: Optional[str] = Field(None, description="Location of the job")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or YYYY)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM or YYYY, or 'Present')")
    description: Optional[List[str]] = Field(None, description="List of responsibilities or achievements")
    
    @field_validator('company', mode='before')
    @classmethod
    def convert_none_company(cls, v):
        """Convert None company to 'Unknown'"""
        if v is None:
            return "Unknown"
        return v
    
    @field_validator('description', mode='before')
    @classmethod
    def convert_description_to_list(cls, v):
        """Convert string description to list, or handle None"""
        if v is None:
            return None
        if isinstance(v, str):
            # Split by newlines or bullet points if present, otherwise return as single-item list
            if '\n' in v:
                return [line.strip() for line in v.split('\n') if line.strip()]
            return [v]
        return v

class ResumeSkill(BaseModel):
    category: Optional[str] = Field(None, description="Category of skill (e.g., Programming, Languages)")
    skills: List[str] = Field(..., description="List of skills in this category")

class ResumeSecurityClearance(BaseModel):
    level: str = Field(..., description="Clearance level (e.g., Secret, Top Secret)")
    status: Optional[str] = Field(None, description="Status (e.g., Active, Expired)")
    agency: Optional[str] = Field(None, description="Issuing agency")

class ResumeData(BaseModel):
    contact_info: ResumeContactInfo
    summary: Optional[str] = Field(None, description="Professional summary or objective")
    experience: List[ResumeExperience] = Field(default_factory=list)
    education: List[ResumeEducation] = Field(default_factory=list)
    skills: List[ResumeSkill] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list, description="List of certifications")
    security_clearance: Optional[List[ResumeSecurityClearance]] = Field(None, description="Security clearances held")
    languages: Optional[List[str]] = Field(None, description="Languages spoken")
    
    @field_validator('skills', mode='before')
    @classmethod
    def convert_skills_to_list(cls, v):
        """Convert dict skills to list format"""
        if v is None:
            return []
        if isinstance(v, dict):
            # Convert dict to list of ResumeSkill objects
            return [{"category": k, "skills": [v[k]] if isinstance(v[k], str) else v[k]} for k in v]
        return v
    
    @field_validator('security_clearance', mode='before')
    @classmethod
    def convert_security_clearance_to_list(cls, v):
        """Convert dict or single clearance to list format"""
        if v is None:
            return None
        if isinstance(v, dict):
            # If it's a single dict, wrap it in a list
            # But only if it has actual data
            if v.get('level') or v.get('status') or v.get('agency'):
                return [v]
            return None
        return v
