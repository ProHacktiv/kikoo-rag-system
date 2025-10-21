"""
Ticket data model for the flowup-support-bot.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class Ticket:
    """
    Ticket data model.
    """
    id: str
    customer_id: str
    message: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    sentiment: Optional[str] = None
    urgency: Optional[str] = None
    response: Optional[str] = None
    status: str = 'pending'
    created_at: datetime = None
    processed_at: Optional[datetime] = None
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    escalated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ticket':
        """
        Create Ticket instance from dictionary.
        
        Args:
            data: Dictionary containing ticket data
            
        Returns:
            Ticket instance
        """
        # Handle datetime fields
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if isinstance(data.get('processed_at'), str):
            data['processed_at'] = datetime.fromisoformat(data['processed_at'].replace('Z', '+00:00'))
        if isinstance(data.get('escalated_at'), str):
            data['escalated_at'] = datetime.fromisoformat(data['escalated_at'].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Ticket instance to dictionary.
        
        Returns:
            Dictionary representation
        """
        data = asdict(self)
        
        # Convert datetime fields to ISO format
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data['processed_at'], datetime):
            data['processed_at'] = data['processed_at'].isoformat()
        if isinstance(data['escalated_at'], datetime):
            data['escalated_at'] = data['escalated_at'].isoformat()
        
        return data
    
    def to_json(self) -> str:
        """
        Convert Ticket instance to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Ticket':
        """
        Create Ticket instance from JSON string.
        
        Args:
            json_str: JSON string containing ticket data
            
        Returns:
            Ticket instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_pending(self) -> bool:
        """
        Check if ticket is pending.
        
        Returns:
            True if ticket is pending
        """
        return self.status == 'pending'
    
    def is_processed(self) -> bool:
        """
        Check if ticket is processed.
        
        Returns:
            True if ticket is processed
        """
        return self.status == 'processed'
    
    def is_escalated(self) -> bool:
        """
        Check if ticket is escalated.
        
        Returns:
            True if ticket is escalated
        """
        return self.escalation_required
    
    def is_high_urgency(self) -> bool:
        """
        Check if ticket is high urgency.
        
        Returns:
            True if ticket is high urgency
        """
        return self.urgency == 'high'
    
    def is_negative_sentiment(self) -> bool:
        """
        Check if ticket has negative sentiment.
        
        Returns:
            True if ticket has negative sentiment
        """
        return self.sentiment == 'negative'
    
    def has_response(self) -> bool:
        """
        Check if ticket has a response.
        
        Returns:
            True if ticket has a response
        """
        return self.response is not None and self.response.strip() != ''
    
    def get_processing_time(self) -> Optional[float]:
        """
        Get ticket processing time in seconds.
        
        Returns:
            Processing time in seconds or None
        """
        if self.processed_at and self.created_at:
            return (self.processed_at - self.created_at).total_seconds()
        return None
    
    def get_escalation_time(self) -> Optional[float]:
        """
        Get time to escalation in seconds.
        
        Returns:
            Time to escalation in seconds or None
        """
        if self.escalated_at and self.created_at:
            return (self.escalated_at - self.created_at).total_seconds()
        return None
    
    def get_confidence_level(self) -> str:
        """
        Get confidence level as string.
        
        Returns:
            Confidence level
        """
        if self.confidence is None:
            return 'unknown'
        elif self.confidence >= 0.8:
            return 'high'
        elif self.confidence >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def is_high_confidence(self) -> bool:
        """
        Check if ticket has high confidence.
        
        Returns:
            True if ticket has high confidence
        """
        return self.confidence is not None and self.confidence >= 0.8
    
    def is_low_confidence(self) -> bool:
        """
        Check if ticket has low confidence.
        
        Returns:
            True if ticket has low confidence
        """
        return self.confidence is not None and self.confidence < 0.6
    
    def get_intent_category(self) -> str:
        """
        Get intent category.
        
        Returns:
            Intent category
        """
        return self.intent or 'unknown'
    
    def is_delivery_intent(self) -> bool:
        """
        Check if ticket is delivery-related.
        
        Returns:
            True if ticket is delivery-related
        """
        return self.intent == 'delivery'
    
    def is_technical_intent(self) -> bool:
        """
        Check if ticket is technical-related.
        
        Returns:
            True if ticket is technical-related
        """
        return self.intent == 'technical'
    
    def is_sales_intent(self) -> bool:
        """
        Check if ticket is sales-related.
        
        Returns:
            True if ticket is sales-related
        """
        return self.intent == 'sales'
    
    def is_refund_intent(self) -> bool:
        """
        Check if ticket is refund-related.
        
        Returns:
            True if ticket is refund-related
        """
        return self.intent == 'refund'
    
    def get_age_hours(self) -> float:
        """
        Get ticket age in hours.
        
        Returns:
            Ticket age in hours
        """
        return (datetime.utcnow() - self.created_at).total_seconds() / 3600
    
    def is_old(self, hours: int = 24) -> bool:
        """
        Check if ticket is old.
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            True if ticket is older than threshold
        """
        return self.get_age_hours() > hours
    
    def is_stale(self, hours: int = 72) -> bool:
        """
        Check if ticket is stale.
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            True if ticket is older than threshold
        """
        return self.get_age_hours() > hours
    
    def update_status(self, new_status: str) -> None:
        """
        Update ticket status.
        
        Args:
            new_status: New status
        """
        self.status = new_status
        if new_status == 'processed':
            self.processed_at = datetime.utcnow()
    
    def escalate(self, reason: str) -> None:
        """
        Escalate ticket.
        
        Args:
            reason: Escalation reason
        """
        self.escalation_required = True
        self.escalation_reason = reason
        self.escalated_at = datetime.utcnow()
    
    def set_response(self, response: str) -> None:
        """
        Set ticket response.
        
        Args:
            response: Response content
        """
        self.response = response
        self.update_status('processed')
    
    def set_intent_analysis(self, intent: str, confidence: float, sentiment: str, urgency: str) -> None:
        """
        Set intent analysis results.
        
        Args:
            intent: Intent category
            confidence: Confidence score
            sentiment: Sentiment analysis
            urgency: Urgency level
        """
        self.intent = intent
        self.confidence = confidence
        self.sentiment = sentiment
        self.urgency = urgency
    
    def get_priority_score(self) -> int:
        """
        Get priority score for sorting.
        
        Returns:
            Priority score (higher = more urgent)
        """
        score = 0
        
        # Base score by urgency
        urgency_scores = {'low': 1, 'medium': 2, 'high': 3}
        score += urgency_scores.get(self.urgency, 0)
        
        # Bonus for negative sentiment
        if self.sentiment == 'negative':
            score += 2
        
        # Bonus for escalation
        if self.escalation_required:
            score += 3
        
        # Bonus for high confidence
        if self.is_high_confidence():
            score += 1
        
        # Penalty for low confidence
        if self.is_low_confidence():
            score -= 1
        
        return score
    
    def get_summary(self) -> str:
        """
        Get ticket summary.
        
        Returns:
            Ticket summary
        """
        summary = f"Ticket {self.id}: {self.intent or 'unknown'} intent"
        
        if self.urgency:
            summary += f", {self.urgency} urgency"
        
        if self.sentiment:
            summary += f", {self.sentiment} sentiment"
        
        if self.escalation_required:
            summary += ", ESCALATED"
        
        return summary
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get ticket metadata.
        
        Returns:
            Ticket metadata
        """
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'intent': self.intent,
            'confidence': self.confidence,
            'sentiment': self.sentiment,
            'urgency': self.urgency,
            'status': self.status,
            'escalation_required': self.escalation_required,
            'escalation_reason': self.escalation_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'escalated_at': self.escalated_at.isoformat() if self.escalated_at else None,
            'processing_time': self.get_processing_time(),
            'age_hours': self.get_age_hours(),
            'priority_score': self.get_priority_score()
        }
    
    def __str__(self) -> str:
        """
        String representation of Ticket.
        
        Returns:
            String representation
        """
        return f"Ticket(id={self.id}, intent={self.intent}, status={self.status}, urgency={self.urgency})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation of Ticket.
        
        Returns:
            Detailed string representation
        """
        return f"Ticket(id='{self.id}', customer_id='{self.customer_id}', intent='{self.intent}', status='{self.status}', urgency='{self.urgency}', escalation_required={self.escalation_required})"
