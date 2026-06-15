from datetime import datetime
from sqlalchemy.sql import func
from app.extensions import db

class Secret(db.Model):
    __tablename__ = "secrets"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = db.Column(db.String(255), nullable=False)
    encrypted_value = db.Column(db.LargeBinary, nullable=False)  # Ciphertext
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(255), nullable=True)  # Comma-separated tags
    expiry_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Healthcheck configuration
    healthcheck_url = db.Column(db.Text, nullable=True)
    healthcheck_method = db.Column(db.String(10), default="GET")
    healthcheck_auth_style = db.Column(db.String(50), default="bearer")  # "bearer", "header", "query_param", "none"
    healthcheck_auth_field = db.Column(db.String(100), nullable=True)  # e.g., "Authorization" or "api_key"
    last_check_status = db.Column(db.String(50), default="unchecked")  # "valid", "invalid", "error", "unchecked"
    last_checked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationship to user
    user = db.relationship("User", backref=db.backref("secrets", cascade="all, delete-orphan"))

    def to_dict(self, masked_value=None):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "service_name": self.service_name,
            "masked_value": masked_value or "••••••••",
            "notes": self.notes,
            "tags": [tag.strip() for tag in self.tags.split(",") if tag.strip()] if self.tags else [],
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "healthcheck_url": self.healthcheck_url,
            "healthcheck_method": self.healthcheck_method,
            "healthcheck_auth_style": self.healthcheck_auth_style,
            "healthcheck_auth_field": self.healthcheck_auth_field,
            "last_check_status": self.last_check_status,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None
        }
