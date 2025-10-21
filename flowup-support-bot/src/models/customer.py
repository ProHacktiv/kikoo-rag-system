"""
Customer data model for the flowup-support-bot.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class Customer:
    """
    Customer data model.
    """
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Customer':
        """
        Create Customer instance from dictionary.
        
        Args:
            data: Dictionary containing customer data
            
        Returns:
            Customer instance
        """
        # Handle datetime fields
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Customer instance to dictionary.
        
        Returns:
            Dictionary representation
        """
        data = asdict(self)
        
        # Convert datetime fields to ISO format
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        
        return data
    
    def to_json(self) -> str:
        """
        Convert Customer instance to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Customer':
        """
        Create Customer instance from JSON string.
        
        Args:
            json_str: JSON string containing customer data
            
        Returns:
            Customer instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def has_email(self) -> bool:
        """
        Check if customer has email.
        
        Returns:
            True if customer has email
        """
        return self.email is not None and self.email.strip() != ''
    
    def has_phone(self) -> bool:
        """
        Check if customer has phone.
        
        Returns:
            True if customer has phone
        """
        return self.phone is not None and self.phone.strip() != ''
    
    def has_company(self) -> bool:
        """
        Check if customer has company.
        
        Returns:
            True if customer has company
        """
        return self.company is not None and self.company.strip() != ''
    
    def is_company(self) -> bool:
        """
        Check if customer is a company.
        
        Returns:
            True if customer is a company
        """
        return self.has_company()
    
    def is_individual(self) -> bool:
        """
        Check if customer is an individual.
        
        Returns:
            True if customer is an individual
        """
        return not self.is_company()
    
    def get_display_name(self) -> str:
        """
        Get display name for customer.
        
        Returns:
            Display name
        """
        if self.is_company():
            return f"{self.name} ({self.company})"
        return self.name
    
    def get_contact_info(self) -> Dict[str, str]:
        """
        Get contact information.
        
        Returns:
            Dictionary with contact information
        """
        contact_info = {}
        
        if self.has_email():
            contact_info['email'] = self.email
        
        if self.has_phone():
            contact_info['phone'] = self.phone
        
        return contact_info
    
    def get_age_days(self) -> float:
        """
        Get customer age in days.
        
        Returns:
            Customer age in days
        """
        return (datetime.utcnow() - self.created_at).total_seconds() / 86400
    
    def is_new_customer(self, days: int = 30) -> bool:
        """
        Check if customer is new.
        
        Args:
            days: Age threshold in days
            
        Returns:
            True if customer is new
        """
        return self.get_age_days() < days
    
    def is_old_customer(self, days: int = 365) -> bool:
        """
        Check if customer is old.
        
        Args:
            days: Age threshold in days
            
        Returns:
            True if customer is old
        """
        return self.get_age_days() > days
    
    def update_contact_info(self, email: Optional[str] = None, phone: Optional[str] = None) -> None:
        """
        Update contact information.
        
        Args:
            email: New email address
            phone: New phone number
        """
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        
        self.updated_at = datetime.utcnow()
    
    def update_company(self, company: Optional[str] = None) -> None:
        """
        Update company information.
        
        Args:
            company: New company name
        """
        self.company = company
        self.updated_at = datetime.utcnow()
    
    def get_validation_status(self) -> Dict[str, bool]:
        """
        Get validation status for customer data.
        
        Returns:
            Dictionary with validation status
        """
        return {
            'has_name': bool(self.name and self.name.strip()),
            'has_email': self.has_email(),
            'has_phone': self.has_phone(),
            'has_company': self.has_company(),
            'is_valid': bool(self.name and self.name.strip()) and (self.has_email() or self.has_phone())
        }
    
    def is_valid(self) -> bool:
        """
        Check if customer data is valid.
        
        Returns:
            True if customer data is valid
        """
        validation = self.get_validation_status()
        return validation['is_valid']
    
    def get_missing_fields(self) -> List[str]:
        """
        Get list of missing required fields.
        
        Returns:
            List of missing fields
        """
        missing = []
        
        if not self.name or not self.name.strip():
            missing.append('name')
        
        if not self.has_email() and not self.has_phone():
            missing.append('contact_info')
        
        return missing
    
    def get_summary(self) -> str:
        """
        Get customer summary.
        
        Returns:
            Customer summary
        """
        summary = f"Customer {self.id}: {self.get_display_name()}"
        
        if self.is_company():
            summary += " (Company)"
        else:
            summary += " (Individual)"
        
        if self.is_new_customer():
            summary += " (New)"
        elif self.is_old_customer():
            summary += " (Long-term)"
        
        return summary
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get customer metadata.
        
        Returns:
            Customer metadata
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'is_company': self.is_company(),
            'is_individual': self.is_individual(),
            'has_email': self.has_email(),
            'has_phone': self.has_phone(),
            'has_company': self.has_company(),
            'is_valid': self.is_valid(),
            'is_new': self.is_new_customer(),
            'is_old': self.is_old_customer(),
            'age_days': self.get_age_days(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'validation_status': self.get_validation_status(),
            'missing_fields': self.get_missing_fields()
        }
    
    def __str__(self) -> str:
        """
        String representation of Customer.
        
        Returns:
            String representation
        """
        return f"Customer(id={self.id}, name={self.name}, email={self.email})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation of Customer.
        
        Returns:
            Detailed string representation
        """
        return f"Customer(id='{self.id}', name='{self.name}', email='{self.email}', phone='{self.phone}', company='{self.company}')"
