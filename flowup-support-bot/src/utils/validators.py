"""
Validation utilities for the flowup-support-bot.
"""

import re
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import email.utils
import phonenumbers
from urllib.parse import urlparse


class ValidationError(Exception):
    """
    Custom validation error.
    """
    pass


class Validator:
    """
    Base validator class.
    """
    
    def __init__(self, field_name: str, required: bool = True):
        """
        Initialize validator.
        
        Args:
            field_name: Name of the field being validated
            required: Whether the field is required
        """
        self.field_name = field_name
        self.required = required
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a value.
        
        Args:
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None and self.required:
            return False, f"{self.field_name} is required"
        
        if value is None and not self.required:
            return True, None
        
        return self._validate_value(value)
    
    def _validate_value(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate the actual value.
        
        Args:
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        raise NotImplementedError("Subclasses must implement _validate_value")


class EmailValidator(Validator):
    """
    Email address validator.
    """
    
    def _validate_value(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address.
        
        Args:
            value: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, f"{self.field_name} must be a string"
        
        try:
            email.utils.parseaddr(value)
            if '@' not in value or '.' not in value.split('@')[1]:
                return False, f"{self.field_name} is not a valid email address"
            return True, None
        except Exception:
            return False, f"{self.field_name} is not a valid email address"


class PhoneValidator(Validator):
    """
    Phone number validator.
    """
    
    def __init__(self, field_name: str, required: bool = True, country_code: str = 'FR'):
        """
        Initialize phone validator.
        
        Args:
            field_name: Name of the field being validated
            required: Whether the field is required
            country_code: Country code for validation
        """
        super().__init__(field_name, required)
        self.country_code = country_code
    
    def _validate_value(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate phone number.
        
        Args:
            value: Phone number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, f"{self.field_name} must be a string"
        
        try:
            parsed_number = phonenumbers.parse(value, self.country_code)
            if not phonenumbers.is_valid_number(parsed_number):
                return False, f"{self.field_name} is not a valid phone number"
            return True, None
        except Exception:
            return False, f"{self.field_name} is not a valid phone number"


class URLValidator(Validator):
    """
    URL validator.
    """
    
    def _validate_value(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL.
        
        Args:
            value: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, f"{self.field_name} must be a string"
        
        try:
            result = urlparse(value)
            if not all([result.scheme, result.netloc]):
                return False, f"{self.field_name} is not a valid URL"
            return True, None
        except Exception:
            return False, f"{self.field_name} is not a valid URL"


class StringValidator(Validator):
    """
    String validator.
    """
    
    def __init__(self, field_name: str, required: bool = True, min_length: int = 0, max_length: int = None):
        """
        Initialize string validator.
        
        Args:
            field_name: Name of the field being validated
            required: Whether the field is required
            min_length: Minimum string length
            max_length: Maximum string length
        """
        super().__init__(field_name, required)
        self.min_length = min_length
        self.max_length = max_length
    
    def _validate_value(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate string.
        
        Args:
            value: String to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, f"{self.field_name} must be a string"
        
        if len(value) < self.min_length:
            return False, f"{self.field_name} must be at least {self.min_length} characters long"
        
        if self.max_length and len(value) > self.max_length:
            return False, f"{self.field_name} must be at most {self.max_length} characters long"
        
        return True, None


class NumberValidator(Validator):
    """
    Number validator.
    """
    
    def __init__(self, field_name: str, required: bool = True, min_value: float = None, max_value: float = None):
        """
        Initialize number validator.
        
        Args:
            field_name: Name of the field being validated
            required: Whether the field is required
            min_value: Minimum value
            max_value: Maximum value
        """
        super().__init__(field_name, required)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_value(self, value: Union[int, float]) -> Tuple[bool, Optional[str]]:
        """
        Validate number.
        
        Args:
            value: Number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, (int, float)):
            return False, f"{self.field_name} must be a number"
        
        if self.min_value is not None and value < self.min_value:
            return False, f"{self.field_name} must be at least {self.min_value}"
        
        if self.max_value is not None and value > self.max_value:
            return False, f"{self.field_name} must be at most {self.max_value}"
        
        return True, None


class DateValidator(Validator):
    """
    Date validator.
    """
    
    def __init__(self, field_name: str, required: bool = True, date_format: str = '%Y-%m-%d'):
        """
        Initialize date validator.
        
        Args:
            field_name: Name of the field being validated
            required: Whether the field is required
            date_format: Expected date format
        """
        super().__init__(field_name, required)
        self.date_format = date_format
    
    def _validate_value(self, value: Union[str, datetime]) -> Tuple[bool, Optional[str]]:
        """
        Validate date.
        
        Args:
            value: Date to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if isinstance(value, datetime):
            return True, None
        
        if not isinstance(value, str):
            return False, f"{self.field_name} must be a string or datetime"
        
        try:
            datetime.strptime(value, self.date_format)
            return True, None
        except ValueError:
            return False, f"{self.field_name} must be in format {self.date_format}"


class ChoiceValidator(Validator):
    """
    Choice validator.
    """
    
    def __init__(self, field_name: str, choices: List[Any], required: bool = True):
        """
        Initialize choice validator.
        
        Args:
            field_name: Name of the field being validated
            choices: List of valid choices
            required: Whether the field is required
        """
        super().__init__(field_name, required)
        self.choices = choices
    
    def _validate_value(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate choice.
        
        Args:
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value not in self.choices:
            return False, f"{self.field_name} must be one of {self.choices}"
        
        return True, None


class RegexValidator(Validator):
    """
    Regex validator.
    """
    
    def __init__(self, field_name: str, pattern: str, required: bool = True):
        """
        Initialize regex validator.
        
        Args:
            field_name: Name of the field being validated
            pattern: Regex pattern
            required: Whether the field is required
        """
        super().__init__(field_name, required)
        self.pattern = re.compile(pattern)
    
    def _validate_value(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate regex pattern.
        
        Args:
            value: String to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, f"{self.field_name} must be a string"
        
        if not self.pattern.match(value):
            return False, f"{self.field_name} does not match required pattern"
        
        return True, None


class CompositeValidator:
    """
    Composite validator for multiple fields.
    """
    
    def __init__(self):
        """
        Initialize composite validator.
        """
        self.validators = {}
    
    def add_validator(self, field_name: str, validator: Validator) -> None:
        """
        Add a validator for a field.
        
        Args:
            field_name: Name of the field
            validator: Validator instance
        """
        self.validators[field_name] = validator
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate all fields.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        for field_name, validator in self.validators.items():
            value = data.get(field_name)
            is_valid, error_message = validator.validate(value)
            
            if not is_valid:
                errors.append(error_message)
        
        return len(errors) == 0, errors


# Convenience functions
def validate_email(email: str) -> bool:
    """
    Validate email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid
    """
    validator = EmailValidator('email')
    is_valid, _ = validator.validate(email)
    return is_valid


def validate_phone(phone: str, country_code: str = 'FR') -> bool:
    """
    Validate phone number.
    
    Args:
        phone: Phone number to validate
        country_code: Country code
        
    Returns:
        True if valid
    """
    validator = PhoneValidator('phone', country_code=country_code)
    is_valid, _ = validator.validate(phone)
    return is_valid


def validate_url(url: str) -> bool:
    """
    Validate URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid
    """
    validator = URLValidator('url')
    is_valid, _ = validator.validate(url)
    return is_valid


def validate_order_number(order_number: str) -> bool:
    """
    Validate order number format.
    
    Args:
        order_number: Order number to validate
        
    Returns:
        True if valid
    """
    # Common order number patterns
    patterns = [
        r'^SO\d+$',  # SO123456
        r'^COMMANDE-\d+$',  # COMMANDE-123456
        r'^ORD\d+$',  # ORD123456
        r'^REF\d+$'  # REF123456
    ]
    
    for pattern in patterns:
        if re.match(pattern, order_number, re.IGNORECASE):
            return True
    
    return False


def validate_tracking_number(tracking_number: str) -> bool:
    """
    Validate UPS tracking number format.
    
    Args:
        tracking_number: Tracking number to validate
        
    Returns:
        True if valid
    """
    # UPS tracking number format: 1Z followed by 16 alphanumeric characters
    pattern = r'^1Z[0-9A-Z]{16}$'
    return bool(re.match(pattern, tracking_number))


def validate_customer_data(customer_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate customer data.
    
    Args:
        customer_data: Customer data to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = CompositeValidator()
    
    # Add validators
    validator.add_validator('name', StringValidator('name', min_length=1, max_length=100))
    validator.add_validator('email', EmailValidator('email', required=False))
    validator.add_validator('phone', PhoneValidator('phone', required=False))
    validator.add_validator('company', StringValidator('company', required=False, max_length=100))
    
    return validator.validate(customer_data)


def validate_ticket_data(ticket_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate ticket data.
    
    Args:
        ticket_data: Ticket data to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = CompositeValidator()
    
    # Add validators
    validator.add_validator('id', StringValidator('id', min_length=1))
    validator.add_validator('customer_id', StringValidator('customer_id', min_length=1))
    validator.add_validator('message', StringValidator('message', min_length=1, max_length=5000))
    validator.add_validator('intent', ChoiceValidator('intent', ['delivery', 'technical', 'sales', 'refund'], required=False))
    validator.add_validator('confidence', NumberValidator('confidence', required=False, min_value=0.0, max_value=1.0))
    validator.add_validator('sentiment', ChoiceValidator('sentiment', ['positive', 'neutral', 'negative'], required=False))
    validator.add_validator('urgency', ChoiceValidator('urgency', ['low', 'medium', 'high'], required=False))
    validator.add_validator('status', ChoiceValidator('status', ['pending', 'processed', 'escalated'], required=False))
    
    return validator.validate(ticket_data)


def validate_order_data(order_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate order data.
    
    Args:
        order_data: Order data to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = CompositeValidator()
    
    # Add validators
    validator.add_validator('id', StringValidator('id', min_length=1))
    validator.add_validator('customer_id', StringValidator('customer_id', min_length=1))
    validator.add_validator('order_number', StringValidator('order_number', min_length=1))
    validator.add_validator('status', ChoiceValidator('status', ['draft', 'sent', 'sale', 'done', 'cancel'], required=False))
    validator.add_validator('amount', NumberValidator('amount', required=False, min_value=0.0))
    
    return validator.validate(order_data)


def sanitize_input(text: str) -> str:
    """
    Sanitize user input.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text.strip()


def validate_and_sanitize_input(text: str, max_length: int = 1000) -> Tuple[str, bool]:
    """
    Validate and sanitize user input.
    
    Args:
        text: Text to validate and sanitize
        max_length: Maximum length
        
    Returns:
        Tuple of (sanitized_text, is_valid)
    """
    if not isinstance(text, str):
        return str(text), False
    
    # Sanitize
    sanitized = sanitize_input(text)
    
    # Validate length
    if len(sanitized) > max_length:
        return sanitized[:max_length], False
    
    # Check for empty input
    if not sanitized.strip():
        return sanitized, False
    
    return sanitized, True
