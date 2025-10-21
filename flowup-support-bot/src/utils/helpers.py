"""
Helper utilities for the flowup-support-bot.
"""

import re
import json
import hashlib
import uuid
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import asyncio
import aiohttp
import yaml
import os


def format_response(response_data: Dict[str, Any], template: str = 'default') -> str:
    """
    Format response data into a readable string.
    
    Args:
        response_data: Response data to format
        template: Template to use for formatting
        
    Returns:
        Formatted response string
    """
    if template == 'default':
        return _format_default_response(response_data)
    elif template == 'ticket':
        return _format_ticket_response(response_data)
    elif template == 'order':
        return _format_order_response(response_data)
    else:
        return str(response_data)


def _format_default_response(response_data: Dict[str, Any]) -> str:
    """
    Format default response.
    
    Args:
        response_data: Response data
        
    Returns:
        Formatted string
    """
    if 'content' in response_data:
        return response_data['content']
    
    if 'message' in response_data:
        return response_data['message']
    
    return json.dumps(response_data, indent=2)


def _format_ticket_response(response_data: Dict[str, Any]) -> str:
    """
    Format ticket response.
    
    Args:
        response_data: Response data
        
    Returns:
        Formatted string
    """
    parts = []
    
    if 'ticket_id' in response_data:
        parts.append(f"Ticket ID: {response_data['ticket_id']}")
    
    if 'intent' in response_data:
        parts.append(f"Intent: {response_data['intent']}")
    
    if 'confidence' in response_data:
        parts.append(f"Confidence: {response_data['confidence']:.2f}")
    
    if 'response' in response_data:
        parts.append(f"Response: {response_data['response']}")
    
    return '\n'.join(parts)


def _format_order_response(response_data: Dict[str, Any]) -> str:
    """
    Format order response.
    
    Args:
        response_data: Response data
        
    Returns:
        Formatted string
    """
    parts = []
    
    if 'order_number' in response_data:
        parts.append(f"Order: {response_data['order_number']}")
    
    if 'status' in response_data:
        parts.append(f"Status: {response_data['status']}")
    
    if 'amount' in response_data:
        parts.append(f"Amount: {response_data['amount']} €")
    
    if 'delivery_date' in response_data:
        parts.append(f"Delivery: {response_data['delivery_date']}")
    
    return '\n'.join(parts)


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract entities from text.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        Dictionary of extracted entities
    """
    entities = {
        'order_numbers': [],
        'tracking_numbers': [],
        'emails': [],
        'phone_numbers': [],
        'urls': [],
        'dates': []
    }
    
    # Extract order numbers
    order_patterns = [
        r'\b(?:so|commande|order|ord)\s*[:\-]?\s*(\d+)\b',
        r'\b(?:ref|réf|reference)\s*[:\-]?\s*(\d+)\b'
    ]
    for pattern in order_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities['order_numbers'].extend(matches)
    
    # Extract tracking numbers
    tracking_pattern = r'\b1Z[0-9A-Z]{16}\b'
    entities['tracking_numbers'] = re.findall(tracking_pattern, text)
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities['emails'] = re.findall(email_pattern, text)
    
    # Extract phone numbers
    phone_pattern = r'\b(?:\+33|0)[1-9](?:[0-9]{8})\b'
    entities['phone_numbers'] = re.findall(phone_pattern, text)
    
    # Extract URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    entities['urls'] = re.findall(url_pattern, text)
    
    # Extract dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b'
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        entities['dates'].extend(matches)
    
    return entities


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?]', '', text)
    
    # Normalize case
    text = text.strip().lower()
    
    return text


def generate_id(prefix: str = '') -> str:
    """
    Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    if prefix:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    return uuid.uuid4().hex


def generate_hash(text: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash for text.
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm to use
        
    Returns:
        Hash string
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


def format_timestamp(timestamp: Union[datetime, str], format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format timestamp.
    
    Args:
        timestamp: Timestamp to format
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return timestamp
    
    return timestamp.strftime(format_str)


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse timestamp string.
    
    Args:
        timestamp_str: Timestamp string to parse
        
    Returns:
        Parsed datetime or None if invalid
    """
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        return None


def calculate_time_difference(start_time: datetime, end_time: datetime) -> timedelta:
    """
    Calculate time difference.
    
    Args:
        start_time: Start time
        end_time: End time
        
    Returns:
        Time difference
    """
    return end_time - start_time


def format_duration(duration: timedelta) -> str:
    """
    Format duration as human-readable string.
    
    Args:
        duration: Duration to format
        
    Returns:
        Formatted duration string
    """
    total_seconds = int(duration.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def merge_dictionaries(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    result.update(dict2)
    return result


def deep_merge_dictionaries(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Deep merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dictionaries(result[key], value)
        else:
            result[key] = value
    
    return result


def filter_dict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    Filter dictionary to only include specified keys.
    
    Args:
        data: Dictionary to filter
        keys: Keys to include
        
    Returns:
        Filtered dictionary
    """
    return {key: data[key] for key in keys if key in data}


def exclude_dict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    Exclude specified keys from dictionary.
    
    Args:
        data: Dictionary to filter
        keys: Keys to exclude
        
    Returns:
        Filtered dictionary
    """
    return {key: value for key, value in data.items() if key not in keys}


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary.
    
    Args:
        data: Dictionary to get value from
        key: Key to get (supports dot notation)
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    keys = key.split('.')
    current = data
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current


def safe_set(data: Dict[str, Any], key: str, value: Any) -> None:
    """
    Safely set value in dictionary.
    
    Args:
        data: Dictionary to set value in
        key: Key to set (supports dot notation)
        value: Value to set
    """
    keys = key.split('.')
    current = data
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """
    Flatten nested list.
    
    Args:
        nested_list: Nested list to flatten
        
    Returns:
        Flattened list
    """
    return [item for sublist in nested_list for item in sublist]


def remove_duplicates(items: List[Any]) -> List[Any]:
    """
    Remove duplicates from list while preserving order.
    
    Args:
        items: List to remove duplicates from
        
    Returns:
        List without duplicates
    """
    seen = set()
    result = []
    
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result


def group_by(items: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group items by a key.
    
    Args:
        items: List of dictionaries to group
        key: Key to group by
        
    Returns:
        Grouped dictionary
    """
    groups = {}
    
    for item in items:
        group_key = item.get(key)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)
    
    return groups


def sort_by(items: List[Dict[str, Any]], key: str, reverse: bool = False) -> List[Dict[str, Any]]:
    """
    Sort items by a key.
    
    Args:
        items: List of dictionaries to sort
        key: Key to sort by
        reverse: Whether to sort in reverse order
        
    Returns:
        Sorted list
    """
    return sorted(items, key=lambda x: x.get(key, 0), reverse=reverse)


async def make_async_request(url: str, method: str = 'GET', headers: Dict[str, str] = None, data: Any = None) -> Tuple[int, Dict[str, Any]]:
    """
    Make an async HTTP request.
    
    Args:
        url: URL to request
        method: HTTP method
        headers: Request headers
        data: Request data
        
    Returns:
        Tuple of (status_code, response_data)
    """
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, json=data) as response:
            try:
                response_data = await response.json()
            except:
                response_data = {'text': await response.text()}
            
            return response.status, response_data


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load YAML file.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Loaded YAML data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Save data to YAML file.
    
    Args:
        data: Data to save
        file_path: Path to save to
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, indent=2)


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded JSON data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save to
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def retry_async(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator for retrying async functions.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    return decorator


def timeout_async(timeout_seconds: float):
    """
    Decorator for adding timeout to async functions.
    
    Args:
        timeout_seconds: Timeout in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
        return wrapper
    return decorator


def create_async_context_manager(resource):
    """
    Create an async context manager for a resource.
    
    Args:
        resource: Resource to manage
        
    Returns:
        Async context manager
    """
    class AsyncContextManager:
        async def __aenter__(self):
            return resource
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if hasattr(resource, 'close'):
                await resource.close()
    
    return AsyncContextManager()


def format_currency(amount: float, currency: str = 'EUR') -> str:
    """
    Format currency amount.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if currency == 'EUR':
        return f"{amount:.2f} €"
    elif currency == 'USD':
        return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format percentage value.
    
    Args:
        value: Value to format (0.0 to 1.0)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def capitalize_words(text: str) -> str:
    """
    Capitalize words in text.
    
    Args:
        text: Text to capitalize
        
    Returns:
        Capitalized text
    """
    return ' '.join(word.capitalize() for word in text.split())


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    return re.sub(r'\s+', ' ', text).strip()


def extract_numbers(text: str) -> List[float]:
    """
    Extract numbers from text.
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of numbers
    """
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches]


def extract_words(text: str) -> List[str]:
    """
    Extract words from text.
    
    Args:
        text: Text to extract words from
        
    Returns:
        List of words
    """
    return re.findall(r'\b\w+\b', text.lower())


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Text to count words in
        
    Returns:
        Number of words
    """
    return len(extract_words(text))


def count_characters(text: str) -> int:
    """
    Count characters in text.
    
    Args:
        text: Text to count characters in
        
    Returns:
        Number of characters
    """
    return len(text)


def count_sentences(text: str) -> int:
    """
    Count sentences in text.
    
    Args:
        text: Text to count sentences in
        
    Returns:
        Number of sentences
    """
    pattern = r'[.!?]+'
    return len(re.findall(pattern, text))


def get_text_statistics(text: str) -> Dict[str, int]:
    """
    Get text statistics.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of statistics
    """
    return {
        'characters': count_characters(text),
        'words': count_words(text),
        'sentences': count_sentences(text),
        'lines': len(text.split('\n'))
    }
