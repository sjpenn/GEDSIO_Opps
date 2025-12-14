import logging
import logging.config
from datetime import datetime
import json
from pathlib import Path
import os

def setup_logging(config_file: str = "config/fedops_config.yaml"):
    """Configure logging for FedOps pipeline"""
    
    # Simple setup if config file doesn't exist
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/fedops_{datetime.now().strftime('%Y%m%d')}.log")
        ]
    )
    
    return logging.getLogger("fedops")

def audit_log(event_type: str, document_id: str, details: dict):
    """Write audit trail entry (required for federal compliance)"""
    
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "document_id": document_id,
        "details": details
    }
    
    Path("logs").mkdir(exist_ok=True)
    with open("logs/audit_trail.jsonl", "a") as f:
        f.write(json.dumps(audit_entry) + "\n")
