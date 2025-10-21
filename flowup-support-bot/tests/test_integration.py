"""
Integration tests for flowup-support-bot.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.core.ticket_processor import TicketProcessor
from src.core.intent_analyzer import IntentAnalyzer
from src.core.response_generator import ResponseGenerator
from src.models.ticket import Ticket
from src.models.customer import Customer


class TestTicketProcessor:
    """Integration tests for TicketProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a TicketProcessor instance for testing."""
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'test_db',
                'user': 'test_user',
                'password': 'test_pass'
            },
            'max_concurrent_tickets': 5
        }
        return TicketProcessor(config)
    
    @pytest.fixture
    def sample_ticket_data(self):
        """Create sample ticket data for testing."""
        return {
            'id': 'TEST-001',
            'customer_id': 'CUST-123',
            'message': 'Où est ma commande SO-456789 ?',
            'created_at': datetime.utcnow().isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_process_ticket_integration(self, processor, sample_ticket_data):
        """Test complete ticket processing workflow."""
        with patch.object(processor.intent_analyzer, 'analyze_intent') as mock_intent:
            mock_intent.return_value = {
                'intent': 'delivery',
                'confidence': 0.9,
                'sentiment': 'neutral',
                'urgency': 'medium',
                'entities': {'order_numbers': ['SO-456789']},
                'keywords': ['commande', 'où'],
                'context': {}
            }
            
            with patch.object(processor.response_generator, 'generate_response') as mock_response:
                mock_response.return_value = {
                    'content': 'Voici les informations concernant votre commande SO-456789...',
                    'escalation_required': False,
                    'metadata': {'handler': 'delivery'}
                }
                
                with patch.object(processor.db, 'save_ticket') as mock_save:
                    mock_save.return_value = True
                    
                    result = await processor.process_ticket(sample_ticket_data)
                    
                    assert result['ticket_id'] == 'TEST-001'
                    assert result['intent'] == 'delivery'
                    assert result['confidence'] == 0.9
                    assert result['escalation_required'] is False
                    assert 'processing_time' in result
    
    @pytest.mark.asyncio
    async def test_batch_process_tickets(self, processor):
        """Test batch processing of multiple tickets."""
        tickets_data = [
            {
                'id': 'TEST-001',
                'customer_id': 'CUST-123',
                'message': 'Où est ma commande ?',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 'TEST-002',
                'customer_id': 'CUST-456',
                'message': 'Problème technique',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        with patch.object(processor, 'process_ticket') as mock_process:
            mock_process.side_effect = [
                {'ticket_id': 'TEST-001', 'intent': 'delivery'},
                {'ticket_id': 'TEST-002', 'intent': 'technical'}
            ]
            
            results = await processor.batch_process_tickets(tickets_data)
            
            assert len(results) == 2
            assert results[0]['ticket_id'] == 'TEST-001'
            assert results[1]['ticket_id'] == 'TEST-002'
    
    @pytest.mark.asyncio
    async def test_get_ticket_status(self, processor):
        """Test getting ticket status."""
        with patch.object(processor.db, 'get_ticket') as mock_get:
            mock_ticket = Ticket(
                id='TEST-001',
                customer_id='CUST-123',
                message='Test message',
                intent='delivery',
                confidence=0.9,
                sentiment='neutral',
                urgency='medium',
                status='processed'
            )
            mock_get.return_value = mock_ticket
            
            status = await processor.get_ticket_status('TEST-001')
            
            assert status['id'] == 'TEST-001'
            assert status['intent'] == 'delivery'
            assert status['confidence'] == 0.9
            assert status['status'] == 'processed'
    
    @pytest.mark.asyncio
    async def test_escalate_ticket(self, processor):
        """Test ticket escalation."""
        with patch.object(processor.db, 'get_ticket') as mock_get:
            mock_ticket = Ticket(
                id='TEST-001',
                customer_id='CUST-123',
                message='Test message'
            )
            mock_get.return_value = mock_ticket
            
            with patch.object(processor.db, 'update_ticket') as mock_update:
                mock_update.return_value = True
                
                with patch.object(processor, '_notify_escalation') as mock_notify:
                    mock_notify.return_value = None
                    
                    result = await processor.escalate_ticket('TEST-001', 'High priority issue')
                    
                    assert result is True
                    assert mock_ticket.escalation_required is True
                    assert mock_ticket.escalation_reason == 'High priority issue'


class TestIntentAnalyzer:
    """Integration tests for IntentAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an IntentAnalyzer instance for testing."""
        config = {
            'rag': {
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2'
            }
        }
        return IntentAnalyzer(config)
    
    @pytest.mark.asyncio
    async def test_analyze_intent_delivery(self, analyzer):
        """Test intent analysis for delivery requests."""
        message = "Où est ma commande SO-456789 ?"
        
        with patch.object(analyzer, '_get_context') as mock_context:
            mock_context.return_value = {}
            
            result = await analyzer.analyze_intent(message)
            
            assert result['intent'] == 'delivery'
            assert result['confidence'] > 0.7
            assert result['sentiment'] in ['positive', 'neutral', 'negative']
            assert result['urgency'] in ['low', 'medium', 'high']
            assert 'SO-456789' in result['entities']['order_numbers']
    
    @pytest.mark.asyncio
    async def test_analyze_intent_technical(self, analyzer):
        """Test intent analysis for technical requests."""
        message = "Je n'arrive pas à me connecter, j'ai une erreur 500"
        
        with patch.object(analyzer, '_get_context') as mock_context:
            mock_context.return_value = {}
            
            result = await analyzer.analyze_intent(message)
            
            assert result['intent'] == 'technical'
            assert result['confidence'] > 0.7
            assert result['sentiment'] == 'negative'
            assert result['urgency'] == 'high'
            assert 'erreur 500' in result['entities'].get('error_details', [])
    
    @pytest.mark.asyncio
    async def test_analyze_intent_sales(self, analyzer):
        """Test intent analysis for sales requests."""
        message = "Combien coûte la version Pro ?"
        
        with patch.object(analyzer, '_get_context') as mock_context:
            mock_context.return_value = {}
            
            result = await analyzer.analyze_intent(message)
            
            assert result['intent'] == 'sales'
            assert result['confidence'] > 0.7
            assert result['sentiment'] == 'neutral'
            assert result['urgency'] == 'low'
    
    @pytest.mark.asyncio
    async def test_analyze_intent_refund(self, analyzer):
        """Test intent analysis for refund requests."""
        message = "Je veux annuler ma commande et me faire rembourser"
        
        with patch.object(analyzer, '_get_context') as mock_context:
            mock_context.return_value = {}
            
            result = await analyzer.analyze_intent(message)
            
            assert result['intent'] == 'refund'
            assert result['confidence'] > 0.7
            assert result['sentiment'] == 'neutral'
            assert result['urgency'] == 'medium'
    
    def test_extract_entities(self, analyzer):
        """Test entity extraction."""
        message = "Ma commande SO-456789 avec le suivi 1Z999AA1234567890"
        
        entities = analyzer._extract_entities(message)
        
        assert 'SO-456789' in entities['order_numbers']
        assert '1Z999AA1234567890' in entities['tracking_numbers']
    
    def test_analyze_sentiment(self, analyzer):
        """Test sentiment analysis."""
        positive_message = "Merci beaucoup, c'est parfait !"
        negative_message = "Je suis très mécontent, ça ne marche pas"
        
        positive_result = analyzer._analyze_sentiment(positive_message)
        negative_result = analyzer._analyze_sentiment(negative_message)
        
        assert positive_result['sentiment'] == 'positive'
        assert negative_result['sentiment'] == 'negative'
    
    def test_classify_intent(self, analyzer):
        """Test intent classification."""
        message = "Où est ma commande ?"
        entities = {'order_numbers': ['SO-456789']}
        
        result = analyzer._classify_intent(message, entities)
        
        assert result['category'] == 'delivery'
        assert result['score'] > 0
        assert 'commande' in result['keywords']
    
    def test_calculate_confidence(self, analyzer):
        """Test confidence calculation."""
        intent_result = {'score': 5}
        sentiment_result = {'sentiment': 'negative', 'urgent_score': 1}
        
        confidence = analyzer._calculate_confidence(intent_result, sentiment_result)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be high due to negative sentiment and urgency
    
    def test_determine_urgency(self, analyzer):
        """Test urgency determination."""
        urgent_message = "URGENT ! Mon système est cassé !"
        normal_message = "Bonjour, j'ai une question"
        
        urgent_result = analyzer._determine_urgency(urgent_message, {'urgent_score': 2})
        normal_result = analyzer._determine_urgency(normal_message, {'urgent_score': 0})
        
        assert urgent_result == 'high'
        assert normal_result == 'low'


class TestResponseGenerator:
    """Integration tests for ResponseGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create a ResponseGenerator instance for testing."""
        config = {
            'rag': {
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2'
            }
        }
        return ResponseGenerator(config)
    
    @pytest.fixture
    def sample_ticket(self):
        """Create a sample ticket for testing."""
        return Ticket(
            id="TEST-001",
            customer_id="CUST-123",
            message="Où est ma commande ?",
            intent="delivery",
            confidence=0.9,
            sentiment="neutral",
            urgency="medium"
        )
    
    @pytest.mark.asyncio
    async def test_generate_response_delivery(self, generator, sample_ticket):
        """Test response generation for delivery intent."""
        intent_result = {
            'intent': 'delivery',
            'confidence': 0.9,
            'entities': {'order_numbers': ['SO-456789']}
        }
        
        context = {
            'ticket': sample_ticket.to_dict(),
            'intent': intent_result
        }
        
        with patch.object(generator, '_get_response_context') as mock_context:
            mock_context.return_value = context
            
            with patch.object(generator, '_get_handler_for_intent') as mock_handler:
                mock_handler_instance = Mock()
                mock_handler_instance.generate_response.return_value = {
                    'content': 'Voici les informations concernant votre commande...',
                    'escalation_required': False
                }
                mock_handler.return_value = mock_handler_instance
                
                response = await generator.generate_response(sample_ticket, intent_result)
                
                assert 'content' in response
                assert response['escalation_required'] is False
                assert 'metadata' in response
    
    @pytest.mark.asyncio
    async def test_generate_response_escalation(self, generator, sample_ticket):
        """Test response generation with escalation."""
        intent_result = {
            'intent': 'technical',
            'confidence': 0.5,
            'sentiment': 'negative',
            'urgency': 'high'
        }
        
        context = {
            'ticket': sample_ticket.to_dict(),
            'intent': intent_result
        }
        
        with patch.object(generator, '_get_response_context') as mock_context:
            mock_context.return_value = context
            
            with patch.object(generator, '_get_handler_for_intent') as mock_handler:
                mock_handler_instance = Mock()
                mock_handler_instance.generate_response.return_value = {
                    'content': 'Votre demande nécessite une attention particulière...',
                    'escalation_required': True
                }
                mock_handler.return_value = mock_handler_instance
                
                response = await generator.generate_response(sample_ticket, intent_result)
                
                assert 'content' in response
                assert response['escalation_required'] is True
                assert 'escalation_required' in response['metadata']
    
    def test_check_escalation_requirements(self, generator, sample_ticket):
        """Test escalation requirement checking."""
        intent_result = {
            'confidence': 0.5,
            'sentiment': 'negative',
            'urgency': 'high'
        }
        
        response = {
            'content': 'Test response',
            'escalation_required': False
        }
        
        should_escalate = generator._check_escalation_requirements(
            sample_ticket, intent_result, response
        )
        
        assert should_escalate is True
    
    def test_format_response(self, generator):
        """Test response formatting."""
        response_data = {
            'content': 'Bonjour, voici votre réponse.'
        }
        
        formatted = generator.format_response(response_data)
        
        assert 'Bonjour' in formatted
        assert 'Cordialement' in formatted
        assert 'L\'équipe Flowup Support' in formatted
    
    @pytest.mark.asyncio
    async def test_generate_follow_up_questions(self, generator, sample_ticket):
        """Test follow-up question generation."""
        response = {
            'content': 'Voici votre réponse',
            'metadata': {'handler': 'delivery'}
        }
        
        questions = await generator.generate_follow_up_questions(sample_ticket, response)
        
        assert len(questions) <= 3
        assert any('aide' in q.lower() for q in questions)
        assert any('question' in q.lower() for q in questions)
