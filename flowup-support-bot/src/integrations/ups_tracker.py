"""
UPS tracking integration for the flowup-support-bot.
"""

import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import hmac
import base64

from ..utils.logger import get_logger


class UPSTracker:
    """
    Client for UPS tracking API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the UPS tracker.
        
        Args:
            config: UPS configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        self.api_url = config['api_url']
        self.access_key = config['access_key']
        self.username = config['username']
        self.password = config['password']
        self.account_number = config['account_number']
        
        # API endpoints
        self.track_endpoint = f"{self.api_url}/api/track/v1/details"
        self.rate_endpoint = f"{self.api_url}/api/rating/v1/Rate"
        
    def _generate_access_token(self) -> Optional[str]:
        """
        Generate UPS API access token.
        
        Returns:
            Access token or None if failed
        """
        try:
            # UPS OAuth endpoint
            oauth_url = f"{self.api_url}/security/v1/oauth/token"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'x-merchant-id': self.username
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            auth = (self.username, self.password)
            
            response = requests.post(oauth_url, headers=headers, data=data, auth=auth)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token')
            
        except Exception as e:
            self.logger.error(f"Error generating UPS access token: {str(e)}")
            return None
    
    async def track_package(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Track a UPS package.
        
        Args:
            tracking_number: UPS tracking number
            
        Returns:
            Tracking information or None if not found
        """
        try:
            access_token = self._generate_access_token()
            if not access_token:
                return None
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'transId': f'trans_{datetime.utcnow().timestamp()}',
                'transactionSrc': 'flowup-support-bot'
            }
            
            payload = {
                'TrackRequest': {
                    'Request': {
                        'RequestOption': '1',
                        'TransactionReference': {
                            'CustomerContext': 'Flowup Support Bot'
                        }
                    },
                    'InquiryNumber': tracking_number,
                    'TrackingOption': '02'
                }
            }
            
            response = requests.post(
                self.track_endpoint,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            tracking_data = response.json()
            return self._parse_tracking_response(tracking_data)
            
        except Exception as e:
            self.logger.error(f"Error tracking UPS package {tracking_number}: {str(e)}")
            return None
    
    def _parse_tracking_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse UPS tracking response.
        
        Args:
            response_data: Raw response from UPS API
            
        Returns:
            Parsed tracking information
        """
        try:
            track_response = response_data.get('TrackResponse', {})
            shipment = track_response.get('Shipment', [])
            
            if not shipment:
                return {'error': 'No shipment information found'}
            
            shipment_info = shipment[0]
            
            # Extract package information
            package = shipment_info.get('Package', [])
            if not package:
                return {'error': 'No package information found'}
            
            package_info = package[0]
            
            # Extract tracking details
            tracking_info = {
                'tracking_number': shipment_info.get('InquiryNumber', {}).get('Number'),
                'service': shipment_info.get('Service', {}).get('Description'),
                'status': package_info.get('Activity', [{}])[0].get('Status', {}).get('Description'),
                'delivery_date': package_info.get('Activity', [{}])[0].get('Date'),
                'delivery_time': package_info.get('Activity', [{}])[0].get('Time'),
                'location': package_info.get('Activity', [{}])[0].get('Location', {}).get('Address', {}).get('City'),
                'activities': []
            }
            
            # Extract all activities
            activities = package_info.get('Activity', [])
            for activity in activities:
                activity_info = {
                    'date': activity.get('Date'),
                    'time': activity.get('Time'),
                    'status': activity.get('Status', {}).get('Description'),
                    'location': activity.get('Location', {}).get('Address', {}).get('City'),
                    'details': activity.get('Status', {}).get('Type')
                }
                tracking_info['activities'].append(activity_info)
            
            return tracking_info
            
        except Exception as e:
            self.logger.error(f"Error parsing UPS tracking response: {str(e)}")
            return {'error': 'Failed to parse tracking information'}
    
    async def get_delivery_estimate(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get delivery estimate for a package.
        
        Args:
            tracking_number: UPS tracking number
            
        Returns:
            Delivery estimate information
        """
        try:
            tracking_info = await self.track_package(tracking_number)
            if not tracking_info or 'error' in tracking_info:
                return None
            
            # Extract delivery information
            delivery_info = {
                'tracking_number': tracking_number,
                'estimated_delivery': tracking_info.get('delivery_date'),
                'delivery_time': tracking_info.get('delivery_time'),
                'current_status': tracking_info.get('status'),
                'service': tracking_info.get('service'),
                'location': tracking_info.get('location')
            }
            
            return delivery_info
            
        except Exception as e:
            self.logger.error(f"Error getting delivery estimate for {tracking_number}: {str(e)}")
            return None
    
    async def get_tracking_history(self, tracking_number: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get complete tracking history for a package.
        
        Args:
            tracking_number: UPS tracking number
            
        Returns:
            List of tracking events
        """
        try:
            tracking_info = await self.track_package(tracking_number)
            if not tracking_info or 'error' in tracking_info:
                return None
            
            return tracking_info.get('activities', [])
            
        except Exception as e:
            self.logger.error(f"Error getting tracking history for {tracking_number}: {str(e)}")
            return None
    
    async def validate_tracking_number(self, tracking_number: str) -> bool:
        """
        Validate UPS tracking number format.
        
        Args:
            tracking_number: Tracking number to validate
            
        Returns:
            True if valid format
        """
        try:
            # UPS tracking number format: 1Z followed by 16 alphanumeric characters
            if len(tracking_number) != 18:
                return False
            
            if not tracking_number.startswith('1Z'):
                return False
            
            # Check if remaining characters are alphanumeric
            remaining = tracking_number[2:]
            if not remaining.isalnum():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating tracking number {tracking_number}: {str(e)}")
            return False
    
    async def get_service_info(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get service information for a package.
        
        Args:
            tracking_number: UPS tracking number
            
        Returns:
            Service information
        """
        try:
            tracking_info = await self.track_package(tracking_number)
            if not tracking_info or 'error' in tracking_info:
                return None
            
            return {
                'service': tracking_info.get('service'),
                'tracking_number': tracking_number,
                'status': tracking_info.get('status'),
                'delivery_date': tracking_info.get('delivery_date'),
                'delivery_time': tracking_info.get('delivery_time')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting service info for {tracking_number}: {str(e)}")
            return None
    
    async def check_delivery_status(self, tracking_number: str) -> str:
        """
        Check if package has been delivered.
        
        Args:
            tracking_number: UPS tracking number
            
        Returns:
            Delivery status (delivered, in_transit, exception, unknown)
        """
        try:
            tracking_info = await self.track_package(tracking_number)
            if not tracking_info or 'error' in tracking_info:
                return 'unknown'
            
            status = tracking_info.get('status', '').lower()
            
            if 'delivered' in status:
                return 'delivered'
            elif 'exception' in status or 'problem' in status:
                return 'exception'
            elif 'in transit' in status or 'out for delivery' in status:
                return 'in_transit'
            else:
                return 'unknown'
                
        except Exception as e:
            self.logger.error(f"Error checking delivery status for {tracking_number}: {str(e)}")
            return 'unknown'
