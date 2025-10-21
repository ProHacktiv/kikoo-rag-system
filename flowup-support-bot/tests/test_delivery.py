"""
Tests for delivery functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from src.handlers.delivery_handler import DeliveryHandler
from src.models.ticket import Ticket
from src.models.customer import Customer


class TestDeliveryHandler:
    """Test cases for DeliveryHandler."""
    
    @pytest.fixture
    def handler(self):
        """Create a DeliveryHandler instance for testing."""
        config = {
            'odoo': {
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass'
            },
            'ups': {
                'api_url': 'https://test.ups.com',
                'access_key': 'test_key',
                'username': 'test_user',
                'password': 'test_pass',
                'account_number': 'test_account'
            }
        }
        return DeliveryHandler(config)
    
    @pytest.fixture
    def sample_ticket(self):
        """Create a sample ticket for testing."""
        return Ticket(
            id="TEST-001",
            customer_id="CUST-123",
            message="Où est ma commande SO-456789 ?",
            intent="delivery",
            confidence=0.9,
            sentiment="neutral",
            urgency="medium"
        )
    
    @pytest.fixture
    def sample_customer(self):
        """Create a sample customer for testing."""
        return Customer(
            id="CUST-123",
            name="Test Customer",
            email="test@example.com",
            phone="0123456789"
        )
    
    @pytest.mark.asyncio
    async def test_generate_response_with_order_number(self, handler, sample_ticket):
        """Test response generation with order number."""
        intent_result = {
            'intent': 'delivery',
            'confidence': 0.9,
            'entities': {
                'order_numbers': ['SO-456789']
            }
        }
        
        context = {
            'ticket': sample_ticket.to_dict(),
            'intent': intent_result
        }
        
        with patch.object(handler, '_handle_order_query') as mock_order:
            mock_order.return_value = {
                'id': 1,
                'name': 'SO-456789',
                'state': 'sale',
                'date_order': '2024-01-10',
                'amount_total': 150.0
            }
            
            response = await handler.generate_response(sample_ticket, intent_result, context)
            
            assert 'content' in response
            assert 'SO-456789' in response['content']
            assert response['escalation_required'] is False
    
    @pytest.mark.asyncio
    async def test_generate_response_with_tracking_number(self, handler, sample_ticket):
        """Test response generation with tracking number."""
        intent_result = {
            'intent': 'delivery',
            'confidence': 0.9,
            'entities': {
                'tracking_numbers': ['1Z999AA1234567890']
            }
        }
        
        context = {
            'ticket': sample_ticket.to_dict(),
            'intent': intent_result
        }
        
        with patch.object(handler, '_handle_tracking_query') as mock_tracking:
            mock_tracking.return_value = {
                'tracking_number': '1Z999AA1234567890',
                'status': 'In Transit',
                'delivery_date': '2024-01-15',
                'location': 'Paris, France'
            }
            
            response = await handler.generate_response(sample_ticket, intent_result, context)
            
            assert 'content' in response
            assert '1Z999AA1234567890' in response['content']
            assert response['escalation_required'] is False
    
    @pytest.mark.asyncio
    async def test_generate_response_general_delivery(self, handler, sample_ticket):
        """Test response generation for general delivery questions."""
        intent_result = {
            'intent': 'delivery',
            'confidence': 0.8,
            'entities': {}
        }
        
        context = {
            'ticket': sample_ticket.to_dict(),
            'intent': intent_result
        }
        
        response = await handler.generate_response(sample_ticket, intent_result, context)
        
        assert 'content' in response
        assert 'livraison' in response['content'].lower()
        assert response['escalation_required'] is False
    
    def test_should_escalate_high_urgency(self, handler, sample_ticket):
        """Test escalation for high urgency tickets."""
        intent_result = {
            'confidence': 0.9,
            'sentiment': 'negative',
            'urgency': 'high',
            'emotion_level': 4
        }
        
        context = {}
        
        should_escalate = handler._should_escalate(sample_ticket, intent_result, context)
        assert should_escalate is True
    
    def test_should_escalate_low_confidence(self, handler, sample_ticket):
        """Test escalation for low confidence tickets."""
        intent_result = {
            'confidence': 0.5,
            'sentiment': 'neutral',
            'urgency': 'medium'
        }
        
        context = {}
        
        should_escalate = handler._should_escalate(sample_ticket, intent_result, context)
        assert should_escalate is True
    
    def test_should_not_escalate_normal_ticket(self, handler, sample_ticket):
        """Test that normal tickets are not escalated."""
        intent_result = {
            'confidence': 0.8,
            'sentiment': 'neutral',
            'urgency': 'medium'
        }
        
        context = {}
        
        should_escalate = handler._should_escalate(sample_ticket, intent_result, context)
        assert should_escalate is False
    
    def test_format_order_response(self, handler):
        """Test order response formatting."""
        order_info = {
            'name': 'SO-456789',
            'state': 'sale',
            'date_order': '2024-01-10',
            'amount_total': 150.0,
            'delivery_status': {
                'last_delivery': {
                    'state': 'In Transit',
                    'tracking_number': '1Z999AA1234567890'
                }
            }
        }
        
        response = handler._format_order_response(order_info)
        
        assert 'SO-456789' in response
        assert 'Confirmé' in response
        assert '150.0' in response
        assert '1Z999AA1234567890' in response
    
    def test_format_tracking_response(self, handler):
        """Test tracking response formatting."""
        tracking_info = {
            'tracking_number': '1Z999AA1234567890',
            'status': 'In Transit',
            'service': 'UPS Standard',
            'delivery_date': '2024-01-15',
            'location': 'Paris, France',
            'activities': [
                {
                    'date': '2024-01-14',
                    'status': 'Package picked up',
                    'location': 'Lyon, France'
                }
            ]
        }
        
        response = handler._format_tracking_response(tracking_info)
        
        assert '1Z999AA1234567890' in response
        assert 'In Transit' in response
        assert 'UPS Standard' in response
        assert 'Paris, France' in response
    
    def test_translate_order_status(self, handler):
        """Test order status translation."""
        assert handler._translate_order_status('sale') == 'Confirmé'
        assert handler._translate_order_status('draft') == 'Brouillon'
        assert handler._translate_order_status('done') == 'Terminé'
        assert handler._translate_order_status('cancel') == 'Annulé'
        assert handler._translate_order_status('unknown') == 'unknown'
    
    def test_get_escalation_triggers(self, handler, sample_ticket):
        """Test escalation trigger detection."""
        intent_result = {
            'confidence': 0.5,
            'sentiment': 'negative',
            'urgency': 'high'
        }
        
        triggers = handler._get_escalation_triggers(sample_ticket, intent_result)
        
        assert 'low_confidence' in triggers
        assert 'negative_sentiment' in triggers
        assert 'high_urgency' in triggers
