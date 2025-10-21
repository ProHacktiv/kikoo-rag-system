"""
Order data model for the flowup-support-bot.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class Order:
    """
    Order data model.
    """
    id: str
    customer_id: str
    order_number: str
    status: str
    amount: float
    created_at: datetime
    updated_at: datetime
    order_data: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.order_data is None:
            self.order_data = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """
        Create Order instance from dictionary.
        
        Args:
            data: Dictionary containing order data
            
        Returns:
            Order instance
        """
        # Handle datetime fields
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Order instance to dictionary.
        
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
        Convert Order instance to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Order':
        """
        Create Order instance from JSON string.
        
        Args:
            json_str: JSON string containing order data
            
        Returns:
            Order instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_active(self) -> bool:
        """
        Check if order is active.
        
        Returns:
            True if order is active
        """
        active_statuses = ['sale', 'done', 'sent']
        return self.status in active_statuses
    
    def is_cancelled(self) -> bool:
        """
        Check if order is cancelled.
        
        Returns:
            True if order is cancelled
        """
        return self.status == 'cancel'
    
    def is_completed(self) -> bool:
        """
        Check if order is completed.
        
        Returns:
            True if order is completed
        """
        return self.status == 'done'
    
    def get_delivery_status(self) -> Optional[str]:
        """
        Get delivery status from order data.
        
        Returns:
            Delivery status or None
        """
        return self.order_data.get('delivery_status')
    
    def get_tracking_number(self) -> Optional[str]:
        """
        Get tracking number from order data.
        
        Returns:
            Tracking number or None
        """
        return self.order_data.get('tracking_number')
    
    def get_delivery_date(self) -> Optional[datetime]:
        """
        Get delivery date from order data.
        
        Returns:
            Delivery date or None
        """
        delivery_date = self.order_data.get('delivery_date')
        if delivery_date:
            if isinstance(delivery_date, str):
                return datetime.fromisoformat(delivery_date.replace('Z', '+00:00'))
            return delivery_date
        return None
    
    def get_items(self) -> List[Dict[str, Any]]:
        """
        Get order items from order data.
        
        Returns:
            List of order items
        """
        return self.order_data.get('items', [])
    
    def get_total_items(self) -> int:
        """
        Get total number of items in order.
        
        Returns:
            Total number of items
        """
        items = self.get_items()
        return sum(item.get('quantity', 0) for item in items)
    
    def get_shipping_address(self) -> Optional[Dict[str, Any]]:
        """
        Get shipping address from order data.
        
        Returns:
            Shipping address or None
        """
        return self.order_data.get('shipping_address')
    
    def get_billing_address(self) -> Optional[Dict[str, Any]]:
        """
        Get billing address from order data.
        
        Returns:
            Billing address or None
        """
        return self.order_data.get('billing_address')
    
    def get_payment_method(self) -> Optional[str]:
        """
        Get payment method from order data.
        
        Returns:
            Payment method or None
        """
        return self.order_data.get('payment_method')
    
    def get_payment_status(self) -> Optional[str]:
        """
        Get payment status from order data.
        
        Returns:
            Payment status or None
        """
        return self.order_data.get('payment_status')
    
    def is_paid(self) -> bool:
        """
        Check if order is paid.
        
        Returns:
            True if order is paid
        """
        return self.get_payment_status() == 'paid'
    
    def get_discount_amount(self) -> float:
        """
        Get discount amount from order data.
        
        Returns:
            Discount amount
        """
        return self.order_data.get('discount_amount', 0.0)
    
    def get_tax_amount(self) -> float:
        """
        Get tax amount from order data.
        
        Returns:
            Tax amount
        """
        return self.order_data.get('tax_amount', 0.0)
    
    def get_shipping_cost(self) -> float:
        """
        Get shipping cost from order data.
        
        Returns:
            Shipping cost
        """
        return self.order_data.get('shipping_cost', 0.0)
    
    def get_total_with_taxes(self) -> float:
        """
        Get total amount including taxes and shipping.
        
        Returns:
            Total amount with taxes and shipping
        """
        return self.amount + self.get_tax_amount() + self.get_shipping_cost() - self.get_discount_amount()
    
    def get_currency(self) -> str:
        """
        Get currency from order data.
        
        Returns:
            Currency code
        """
        return self.order_data.get('currency', 'EUR')
    
    def get_notes(self) -> Optional[str]:
        """
        Get order notes from order data.
        
        Returns:
            Order notes or None
        """
        return self.order_data.get('notes')
    
    def get_tags(self) -> List[str]:
        """
        Get order tags from order data.
        
        Returns:
            List of tags
        """
        return self.order_data.get('tags', [])
    
    def has_tag(self, tag: str) -> bool:
        """
        Check if order has specific tag.
        
        Args:
            tag: Tag to check
            
        Returns:
            True if order has the tag
        """
        return tag in self.get_tags()
    
    def get_priority(self) -> str:
        """
        Get order priority from order data.
        
        Returns:
            Order priority
        """
        return self.order_data.get('priority', 'normal')
    
    def is_high_priority(self) -> bool:
        """
        Check if order is high priority.
        
        Returns:
            True if order is high priority
        """
        return self.get_priority() in ['high', 'urgent']
    
    def get_estimated_delivery_date(self) -> Optional[datetime]:
        """
        Get estimated delivery date from order data.
        
        Returns:
            Estimated delivery date or None
        """
        estimated_date = self.order_data.get('estimated_delivery_date')
        if estimated_date:
            if isinstance(estimated_date, str):
                return datetime.fromisoformat(estimated_date.replace('Z', '+00:00'))
            return estimated_date
        return None
    
    def is_delivery_overdue(self) -> bool:
        """
        Check if delivery is overdue.
        
        Returns:
            True if delivery is overdue
        """
        estimated_date = self.get_estimated_delivery_date()
        if estimated_date:
            return datetime.utcnow() > estimated_date
        return False
    
    def get_delivery_delay_days(self) -> Optional[int]:
        """
        Get delivery delay in days.
        
        Returns:
            Number of days delayed or None
        """
        estimated_date = self.get_estimated_delivery_date()
        if estimated_date:
            delay = datetime.utcnow() - estimated_date
            return delay.days if delay.days > 0 else 0
        return None
    
    def update_status(self, new_status: str) -> None:
        """
        Update order status.
        
        Args:
            new_status: New status
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def add_note(self, note: str) -> None:
        """
        Add note to order.
        
        Args:
            note: Note to add
        """
        if 'notes' not in self.order_data:
            self.order_data['notes'] = ''
        
        if self.order_data['notes']:
            self.order_data['notes'] += f"\n{note}"
        else:
            self.order_data['notes'] = note
        
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """
        Add tag to order.
        
        Args:
            tag: Tag to add
        """
        if 'tags' not in self.order_data:
            self.order_data['tags'] = []
        
        if tag not in self.order_data['tags']:
            self.order_data['tags'].append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove tag from order.
        
        Args:
            tag: Tag to remove
        """
        if 'tags' in self.order_data and tag in self.order_data['tags']:
            self.order_data['tags'].remove(tag)
            self.updated_at = datetime.utcnow()
    
    def set_delivery_info(self, tracking_number: str, delivery_date: Optional[datetime] = None) -> None:
        """
        Set delivery information.
        
        Args:
            tracking_number: Tracking number
            delivery_date: Delivery date
        """
        self.order_data['tracking_number'] = tracking_number
        if delivery_date:
            self.order_data['delivery_date'] = delivery_date.isoformat()
        
        self.updated_at = datetime.utcnow()
    
    def set_payment_info(self, payment_method: str, payment_status: str) -> None:
        """
        Set payment information.
        
        Args:
            payment_method: Payment method
            payment_status: Payment status
        """
        self.order_data['payment_method'] = payment_method
        self.order_data['payment_status'] = payment_status
        
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        """
        String representation of Order.
        
        Returns:
            String representation
        """
        return f"Order(id={self.id}, order_number={self.order_number}, status={self.status}, amount={self.amount})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation of Order.
        
        Returns:
            Detailed string representation
        """
        return f"Order(id='{self.id}', customer_id='{self.customer_id}', order_number='{self.order_number}', status='{self.status}', amount={self.amount}, created_at={self.created_at}, updated_at={self.updated_at})"
