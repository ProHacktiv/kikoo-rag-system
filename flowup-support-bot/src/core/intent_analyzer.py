"""
Intent analysis module for the flowup-support-bot.
"""

import re
from typing import Dict, Any, List, Tuple
import yaml
from datetime import datetime

from ..utils.logger import get_logger
from ..rag.retriever import ContextRetriever


class IntentAnalyzer:
    """
    Analyzes customer intent from messages.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the intent analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.context_retriever = ContextRetriever(config)
        
        # Load category mappings
        self._load_category_mappings()
        
    def _load_category_mappings(self) -> None:
        """Load category mappings from configuration."""
        try:
            with open('config/categories_mapping.json', 'r', encoding='utf-8') as f:
                self.category_mappings = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading category mappings: {str(e)}")
            self.category_mappings = {}
    
    async def analyze_intent(self, message: str, customer_id: str = None) -> Dict[str, Any]:
        """
        Analyze the intent of a customer message.
        
        Args:
            message: Customer message to analyze
            customer_id: ID of the customer (optional)
            
        Returns:
            Intent analysis results
        """
        try:
            # Clean and preprocess message
            cleaned_message = self._preprocess_message(message)
            
            # Extract entities
            entities = self._extract_entities(cleaned_message)
            
            # Analyze sentiment
            sentiment_result = self._analyze_sentiment(cleaned_message)
            
            # Determine intent category
            intent_result = self._classify_intent(cleaned_message, entities)
            
            # Calculate confidence
            confidence = self._calculate_confidence(intent_result, sentiment_result)
            
            # Determine urgency
            urgency = self._determine_urgency(cleaned_message, sentiment_result)
            
            # Get context if available
            context = await self._get_context(cleaned_message, customer_id)
            
            return {
                'intent': intent_result['category'],
                'confidence': confidence,
                'sentiment': sentiment_result['sentiment'],
                'urgency': urgency,
                'entities': entities,
                'keywords': intent_result['keywords'],
                'context': context,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing intent: {str(e)}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'sentiment': 'neutral',
                'urgency': 'low',
                'entities': {},
                'keywords': [],
                'context': {},
                'error': str(e)
            }
    
    def _preprocess_message(self, message: str) -> str:
        """
        Preprocess the message for analysis.
        
        Args:
            message: Raw message
            
        Returns:
            Cleaned message
        """
        # Convert to lowercase
        cleaned = message.lower().strip()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove special characters but keep basic punctuation
        cleaned = re.sub(r'[^\w\s.,!?]', '', cleaned)
        
        return cleaned
    
    def _extract_entities(self, message: str) -> Dict[str, List[str]]:
        """
        Extract entities from the message.
        
        Args:
            message: Cleaned message
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {
            'order_numbers': [],
            'tracking_numbers': [],
            'emails': [],
            'phone_numbers': [],
            'products': [],
            'dates': []
        }
        
        # Extract order numbers (patterns like SO001, COMMANDE-123, etc.)
        order_patterns = [
            r'\b(?:so|commande|order|ord)\s*[:\-]?\s*(\d+)\b',
            r'\b(?:ref|réf|reference)\s*[:\-]?\s*(\d+)\b'
        ]
        for pattern in order_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            entities['order_numbers'].extend(matches)
        
        # Extract tracking numbers (UPS format)
        tracking_pattern = r'\b1Z[0-9A-Z]{16}\b'
        entities['tracking_numbers'] = re.findall(tracking_pattern, message)
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, message)
        
        # Extract phone numbers
        phone_pattern = r'\b(?:\+33|0)[1-9](?:[0-9]{8})\b'
        entities['phone_numbers'] = re.findall(phone_pattern, message)
        
        # Extract product mentions
        product_keywords = ['flowup', 'module', 'plugin', 'extension', 'addon']
        for keyword in product_keywords:
            if keyword in message:
                entities['products'].append(keyword)
        
        return entities
    
    def _analyze_sentiment(self, message: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of the message.
        
        Args:
            message: Cleaned message
            
        Returns:
            Sentiment analysis results
        """
        # Simple keyword-based sentiment analysis
        positive_keywords = [
            'merci', 'thanks', 'thank you', 'parfait', 'perfect', 'excellent',
            'génial', 'great', 'super', 'fantastic', 'satisfait', 'satisfied'
        ]
        
        negative_keywords = [
            'problème', 'problem', 'erreur', 'error', 'bug', 'dysfonctionnement',
            'malfunction', 'frustré', 'frustrated', 'mécontent', 'unhappy',
            'déçu', 'disappointed', 'énervé', 'angry', 'fâché', 'mad'
        ]
        
        urgent_keywords = [
            'urgent', 'urgent', 'asap', 'immédiatement', 'immediately',
            'critique', 'critical', 'bloqué', 'blocked', 'cassé', 'broken'
        ]
        
        message_lower = message.lower()
        
        positive_score = sum(1 for keyword in positive_keywords if keyword in message_lower)
        negative_score = sum(1 for keyword in negative_keywords if keyword in message_lower)
        urgent_score = sum(1 for keyword in urgent_keywords if keyword in message_lower)
        
        if negative_score > positive_score:
            sentiment = 'negative'
        elif positive_score > negative_score:
            sentiment = 'positive'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'positive_score': positive_score,
            'negative_score': negative_score,
            'urgent_score': urgent_score,
            'emotion_level': min(5, max(1, negative_score + urgent_score))
        }
    
    def _classify_intent(self, message: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Classify the intent category of the message.
        
        Args:
            message: Cleaned message
            entities: Extracted entities
            
        Returns:
            Intent classification results
        """
        categories = self.category_mappings.get('categories', {})
        scores = {}
        
        for category, config in categories.items():
            score = 0
            keywords = config.get('keywords', [])
            patterns = config.get('intent_patterns', [])
            
            # Check keyword matches
            for keyword in keywords:
                if keyword.lower() in message:
                    score += 1
            
            # Check pattern matches
            for pattern in patterns:
                if pattern.lower() in message:
                    score += 2
            
            # Boost score for specific entities
            if category == 'delivery' and entities['tracking_numbers']:
                score += 3
            if category == 'delivery' and entities['order_numbers']:
                score += 2
            if category == 'technical' and any(word in message for word in ['bug', 'erreur', 'problème']):
                score += 2
            if category == 'sales' and any(word in message for word in ['prix', 'coût', 'devis']):
                score += 2
            if category == 'refund' and any(word in message for word in ['retour', 'remboursement', 'annuler']):
                score += 2
            
            scores[category] = score
        
        # Find the category with highest score
        if scores:
            best_category = max(scores, key=scores.get)
            best_score = scores[best_category]
        else:
            best_category = 'generic'
            best_score = 0
        
        return {
            'category': best_category,
            'score': best_score,
            'keywords': [kw for kw in categories.get(best_category, {}).get('keywords', []) if kw in message],
            'all_scores': scores
        }
    
    def _calculate_confidence(self, intent_result: Dict[str, Any], sentiment_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the intent analysis.
        
        Args:
            intent_result: Intent classification results
            sentiment_result: Sentiment analysis results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = min(1.0, intent_result['score'] / 10.0)
        
        # Adjust based on sentiment
        if sentiment_result['sentiment'] == 'negative':
            base_confidence += 0.1
        elif sentiment_result['sentiment'] == 'positive':
            base_confidence += 0.05
        
        # Adjust based on urgency
        if sentiment_result['urgent_score'] > 0:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_urgency(self, message: str, sentiment_result: Dict[str, Any]) -> str:
        """
        Determine the urgency level of the message.
        
        Args:
            message: Cleaned message
            sentiment_result: Sentiment analysis results
            
        Returns:
            Urgency level (low, medium, high)
        """
        urgent_keywords = [
            'urgent', 'urgent', 'asap', 'immédiatement', 'immediately',
            'critique', 'critical', 'bloqué', 'blocked', 'cassé', 'broken',
            'perte', 'loss', 'données', 'data', 'sécurité', 'security'
        ]
        
        message_lower = message.lower()
        urgent_count = sum(1 for keyword in urgent_keywords if keyword in message_lower)
        
        if urgent_count >= 2 or sentiment_result['urgent_score'] >= 2:
            return 'high'
        elif urgent_count >= 1 or sentiment_result['urgent_score'] >= 1:
            return 'medium'
        else:
            return 'low'
    
    async def _get_context(self, message: str, customer_id: str = None) -> Dict[str, Any]:
        """
        Get additional context for the message.
        
        Args:
            message: Cleaned message
            customer_id: Customer ID if available
            
        Returns:
            Context information
        """
        context = {}
        
        if customer_id:
            # Get customer history
            context['customer_history'] = await self._get_customer_history(customer_id)
        
        # Get relevant knowledge base entries
        context['knowledge_base'] = await self.context_retriever.retrieve_context(message)
        
        return context
    
    async def _get_customer_history(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer interaction history.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer history information
        """
        # This would typically query the database
        # For now, return empty dict
        return {}
