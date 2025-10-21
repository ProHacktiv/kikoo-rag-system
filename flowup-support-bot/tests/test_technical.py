"""
Tests for technical support functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from src.handlers.technical_handler import TechnicalHandler
from src.models.ticket import Ticket


class TestTechnicalHandler:
    """Test cases for TechnicalHandler."""
    
    @pytest.fixture
    def handler(self):
        """Create a TechnicalHandler instance for testing."""
        config = {
            'rag': {
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
                'similarity_threshold': 0.7,
                'max_results': 5
            }
        }
        return TechnicalHandler(config)
    
    @pytest.fixture
    def sample_ticket(self):
        """Create a sample ticket for testing."""
        return Ticket(
            id="TEST-002",
            customer_id="CUST-456",
            message="Je n'arrive pas à me connecter à l'interface, j'ai une erreur 500",
            intent="technical",
            confidence=0.9,
            sentiment="negative",
            urgency="high"
        )
    
    @pytest.mark.asyncio
    async def test_generate_response_with_solutions(self, handler, sample_ticket):
        """Test response generation when solutions are found."""
        intent_result = {
            'intent': 'technical',
            'confidence': 0.9,
            'entities': {}
        }
        
        context = {
            'ticket': sample_ticket.to_dict(),
            'intent': intent_result,
            'knowledge_base': {
                'solutions': [
                    {
                        'content': 'Videz le cache de votre navigateur et redémarrez l\'application.',
                        'similarity': 0.8
                    }
                ]
            }
        }
        
        with patch.object(handler, '_analyze_technical_issue') as mock_analysis:
            mock_analysis.return_value = {
                'issue_type': 'connection',
                'complexity': 'low',
                'error_details': ['erreur 500']
            }
            
            with patch.object(handler, '_search_solutions') as mock_search:
                mock_search.return_value = [
                    {
                        'content': 'Videz le cache de votre navigateur et redémarrez l\'application.',
                        'similarity': 0.8
                    }
                ]
                
                response = await handler.generate_response(sample_ticket, intent_result, context)
                
                assert 'content' in response
                assert 'cache' in response['content'].lower()
                assert response['escalation_required'] is False
    
    @pytest.mark.asyncio
    async def test_generate_response_no_solutions(self, handler, sample_ticket):
        """Test response generation when no solutions are found."""
        intent_result = {
            'intent': 'technical',
            'confidence': 0.9,
            'entities': {}
        }
        
        context = {
            'ticket': sample_ticket.to_dict(),
            'intent': intent_result
        }
        
        with patch.object(handler, '_analyze_technical_issue') as mock_analysis:
            mock_analysis.return_value = {
                'issue_type': 'unknown',
                'complexity': 'high',
                'error_details': []
            }
            
            with patch.object(handler, '_search_solutions') as mock_search:
                mock_search.return_value = []
                
                response = await handler.generate_response(sample_ticket, intent_result, context)
                
                assert 'content' in response
                assert 'transférer' in response['content'].lower()
                assert response['escalation_required'] is True
    
    def test_analyze_technical_issue(self, handler):
        """Test technical issue analysis."""
        message = "Je n'arrive pas à me connecter, j'ai une erreur 500"
        
        with patch.object(handler, '_get_context') as mock_context:
            mock_context.return_value = {}
            
            issue_analysis = handler._analyze_technical_issue(message, {})
            
            assert issue_analysis['issue_type'] == 'bug'
            assert issue_analysis['complexity'] == 'medium'
            assert 'erreur 500' in issue_analysis['error_details']
    
    def test_assess_complexity_low(self, handler):
        """Test complexity assessment for low complexity issues."""
        message = "L'interface est lente"
        detected_issues = ['performance']
        
        complexity = handler._assess_complexity(message, detected_issues)
        assert complexity == 'medium'
    
    def test_assess_complexity_high(self, handler):
        """Test complexity assessment for high complexity issues."""
        message = "J'ai perdu toutes mes données, le système a planté"
        detected_issues = ['data', 'system_crash']
        
        complexity = handler._assess_complexity(message, detected_issues)
        assert complexity == 'high'
    
    def test_extract_error_details(self, handler):
        """Test error details extraction."""
        message = "J'ai une erreur 500 lors de la connexion"
        
        error_details = handler._extract_error_details(message)
        assert 'erreur 500' in error_details
    
    def test_should_escalate_high_complexity(self, handler, sample_ticket):
        """Test escalation for high complexity issues."""
        intent_result = {
            'confidence': 0.9,
            'sentiment': 'negative',
            'urgency': 'high'
        }
        
        issue_analysis = {
            'complexity': 'high',
            'all_issues': ['data', 'security']
        }
        
        should_escalate = handler._should_escalate(sample_ticket, intent_result, issue_analysis)
        assert should_escalate is True
    
    def test_should_escalate_critical_issue(self, handler, sample_ticket):
        """Test escalation for critical issues."""
        intent_result = {
            'confidence': 0.9,
            'sentiment': 'negative',
            'urgency': 'high'
        }
        
        issue_analysis = {
            'complexity': 'medium',
            'all_issues': ['data', 'security']
        }
        
        should_escalate = handler._should_escalate(sample_ticket, intent_result, issue_analysis)
        assert should_escalate is True
    
    def test_should_not_escalate_normal_issue(self, handler, sample_ticket):
        """Test that normal issues are not escalated."""
        intent_result = {
            'confidence': 0.9,
            'sentiment': 'neutral',
            'urgency': 'medium'
        }
        
        issue_analysis = {
            'complexity': 'low',
            'all_issues': ['performance']
        }
        
        should_escalate = handler._should_escalate(sample_ticket, intent_result, issue_analysis)
        assert should_escalate is False
    
    def test_get_escalation_triggers(self, handler, sample_ticket):
        """Test escalation trigger detection."""
        intent_result = {
            'confidence': 0.5,
            'sentiment': 'negative',
            'urgency': 'high'
        }
        
        issue_analysis = {
            'complexity': 'high',
            'all_issues': ['data', 'security']
        }
        
        triggers = handler._get_escalation_triggers(sample_ticket, intent_result, issue_analysis)
        
        assert 'high_complexity' in triggers
        assert 'critical_issue' in triggers
        assert 'low_confidence' in triggers
        assert 'negative_sentiment' in triggers
    
    def test_format_solution_response(self, handler):
        """Test solution response formatting."""
        issue_analysis = {
            'issue_type': 'connection',
            'message': 'Problème de connexion'
        }
        
        solutions = [
            {
                'content': 'Videz le cache de votre navigateur',
                'similarity': 0.8
            },
            {
                'content': 'Redémarrez l\'application',
                'similarity': 0.7
            }
        ]
        
        response = handler._format_solution_response(issue_analysis, solutions)
        
        assert 'connection' in response.lower()
        assert 'cache' in response.lower()
        assert 'redémarrez' in response.lower()
        assert 'Solution 1' in response
        assert 'Solution 2' in response
    
    def test_format_no_solution_response(self, handler):
        """Test no solution response formatting."""
        issue_analysis = {
            'issue_type': 'unknown',
            'message': 'Problème inconnu'
        }
        
        response = handler._format_no_solution_response(issue_analysis)
        
        assert 'unknown' in response.lower()
        assert 'transférer' in response.lower()
        assert 'équipe technique' in response.lower()
    
    def test_format_escalation_response(self, handler):
        """Test escalation response formatting."""
        response = handler._format_escalation_response()
        
        assert 'expertise technique' in response.lower()
        assert 'développeurs' in response.lower()
        assert 'solution personnalisée' in response.lower()
    
    def test_format_error_response(self, handler):
        """Test error response formatting."""
        response = handler._format_error_response()
        
        assert 'difficulté technique' in response.lower()
        assert 'équipe technique' in response.lower()
        assert 'enregistrée' in response.lower()
