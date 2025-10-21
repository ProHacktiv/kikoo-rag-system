"""
Response generation module for the flowup-support-bot.
"""

import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models.ticket import Ticket
from ..rag.retriever import ContextRetriever
from ..utils.logger import get_logger


class ResponseGenerator:
    """
    Generates responses for customer tickets.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the response generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.context_retriever = ContextRetriever(config)
        
        # Load prompts and templates
        self._load_prompts()
        self._load_response_templates()
    
    def _load_prompts(self) -> None:
        """Load prompt templates from configuration."""
        try:
            with open('config/prompts.yaml', 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading prompts: {str(e)}")
            self.prompts = {}
    
    def _load_response_templates(self) -> None:
        """Load response templates from configuration."""
        try:
            with open('config/categories_mapping.json', 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.response_templates = data.get('response_templates', {})
        except Exception as e:
            self.logger.error(f"Error loading response templates: {str(e)}")
            self.response_templates = {}
    
    async def generate_response(self, ticket: Ticket, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response for a ticket.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            
        Returns:
            Generated response with metadata
        """
        try:
            # Get context for the response
            context = await self._get_response_context(ticket, intent_result)
            
            # Select appropriate handler based on intent
            handler = self._get_handler_for_intent(intent_result['intent'])
            
            # Generate response using the handler
            response = await handler.generate_response(ticket, intent_result, context)
            
            # Check if escalation is needed
            escalation_required = self._check_escalation_requirements(
                ticket, intent_result, response
            )
            
            # Add metadata
            response['metadata'] = {
                'generated_at': datetime.utcnow().isoformat(),
                'intent': intent_result['intent'],
                'confidence': intent_result['confidence'],
                'escalation_required': escalation_required,
                'handler_used': handler.__class__.__name__,
                'context_sources': context.get('sources', [])
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response for ticket {ticket.id}: {str(e)}")
            return self._generate_fallback_response(ticket, str(e))
    
    async def _get_response_context(self, ticket: Ticket, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get context information for response generation.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            
        Returns:
            Context information
        """
        context = {
            'ticket': ticket.to_dict(),
            'intent': intent_result,
            'sources': []
        }
        
        # Get relevant knowledge base entries
        kb_context = await self.context_retriever.retrieve_context(ticket.message)
        context['knowledge_base'] = kb_context
        context['sources'].extend(kb_context.get('sources', []))
        
        # Get customer information if available
        if ticket.customer_id:
            customer_context = await self._get_customer_context(ticket.customer_id)
            context['customer'] = customer_context
        
        # Get order information if available
        if intent_result.get('entities', {}).get('order_numbers'):
            order_context = await self._get_order_context(
                intent_result['entities']['order_numbers'][0]
            )
            context['order'] = order_context
        
        return context
    
    def _get_handler_for_intent(self, intent: str):
        """
        Get the appropriate handler for the intent.
        
        Args:
            intent: Intent category
            
        Returns:
            Handler instance
        """
        # Import handlers dynamically to avoid circular imports
        if intent == 'delivery':
            from ..handlers.delivery_handler import DeliveryHandler
            return DeliveryHandler(self.config)
        elif intent == 'technical':
            from ..handlers.technical_handler import TechnicalHandler
            return TechnicalHandler(self.config)
        elif intent == 'sales':
            from ..handlers.sales_handler import SalesHandler
            return SalesHandler(self.config)
        elif intent == 'refund':
            from ..handlers.refund_handler import RefundHandler
            return RefundHandler(self.config)
        else:
            # Generic handler for unknown intents
            from ..handlers.generic_handler import GenericHandler
            return GenericHandler(self.config)
    
    def _check_escalation_requirements(self, ticket: Ticket, intent_result: Dict[str, Any], response: Dict[str, Any]) -> bool:
        """
        Check if the ticket requires escalation.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            response: Generated response
            
        Returns:
            True if escalation is required
        """
        # Check confidence threshold
        if intent_result['confidence'] < 0.7:
            return True
        
        # Check sentiment
        if intent_result['sentiment'] == 'negative' and intent_result.get('emotion_level', 0) > 3:
            return True
        
        # Check urgency
        if intent_result['urgency'] == 'high':
            return True
        
        # Check if response indicates escalation needed
        if response.get('escalation_required', False):
            return True
        
        # Check for specific escalation triggers
        escalation_triggers = [
            'escalate', 'manager', 'supervisor', 'human', 'personne',
            'impossible', 'ne sais pas', 'don\'t know', 'complex'
        ]
        
        response_text = response.get('content', '').lower()
        if any(trigger in response_text for trigger in escalation_triggers):
            return True
        
        return False
    
    def _generate_fallback_response(self, ticket: Ticket, error: str) -> Dict[str, Any]:
        """
        Generate a fallback response when normal generation fails.
        
        Args:
            ticket: The ticket object
            error: Error message
            
        Returns:
            Fallback response
        """
        fallback_message = """
        Bonjour,
        
        Je vous remercie pour votre message. Je suis actuellement en train de traiter votre demande.
        
        En raison d'une difficulté technique temporaire, je ne peux pas vous fournir une réponse complète pour le moment.
        
        Votre demande a été enregistrée et sera traitée par notre équipe de support dans les plus brefs délais.
        
        Si votre demande est urgente, n'hésitez pas à nous contacter directement.
        
        Cordialement,
        L'équipe Flowup Support
        """
        
        return {
            'content': fallback_message,
            'escalation_required': True,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'fallback': True,
                'error': error,
                'escalation_required': True
            }
        }
    
    async def _get_customer_context(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer context information.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer context
        """
        # This would typically query the database
        # For now, return empty dict
        return {}
    
    async def _get_order_context(self, order_number: str) -> Dict[str, Any]:
        """
        Get order context information.
        
        Args:
            order_number: Order number
            
        Returns:
            Order context
        """
        # This would typically query Odoo or database
        # For now, return empty dict
        return {}
    
    def format_response(self, response: Dict[str, Any], template_type: str = 'default') -> str:
        """
        Format a response using templates.
        
        Args:
            response: Response data
            template_type: Type of template to use
            
        Returns:
            Formatted response string
        """
        content = response.get('content', '')
        
        # Add greeting if not present
        if not content.startswith(('Bonjour', 'Hello', 'Hi')):
            greeting = "Bonjour,\n\n"
            content = greeting + content
        
        # Add closing if not present
        if not content.endswith(('Cordialement', 'Best regards', 'Sincerely')):
            closing = "\n\nCordialement,\nL'équipe Flowup Support"
            content = content + closing
        
        return content
    
    async def generate_follow_up_questions(self, ticket: Ticket, response: Dict[str, Any]) -> List[str]:
        """
        Generate follow-up questions based on the response.
        
        Args:
            ticket: The ticket object
            response: Generated response
            
        Returns:
            List of follow-up questions
        """
        questions = []
        
        # Add generic follow-up questions
        questions.extend([
            "Y a-t-il autre chose avec laquelle je peux vous aider ?",
            "Avez-vous d'autres questions concernant votre commande ?",
            "Souhaitez-vous des informations supplémentaires ?"
        ])
        
        # Add intent-specific questions
        intent = ticket.intent
        if intent == 'delivery':
            questions.extend([
                "Souhaitez-vous recevoir des notifications de suivi ?",
                "Avez-vous des questions sur les délais de livraison ?"
            ])
        elif intent == 'technical':
            questions.extend([
                "Avez-vous essayé les solutions proposées ?",
                "Le problème persiste-t-il ?"
            ])
        elif intent == 'sales':
            questions.extend([
                "Souhaitez-vous un devis personnalisé ?",
                "Avez-vous des questions sur nos autres produits ?"
            ])
        elif intent == 'refund':
            questions.extend([
                "Avez-vous des questions sur le processus de remboursement ?",
                "Souhaitez-vous des informations sur nos politiques de retour ?"
            ])
        
        return questions[:3]  # Return maximum 3 questions
