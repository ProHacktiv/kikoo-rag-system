"""
Refund handler for the flowup-support-bot.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..models.ticket import Ticket
from ..integrations.odoo_client import OdooClient
from ..utils.logger import get_logger


class RefundHandler:
    """
    Handler for refund and return requests.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the refund handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.odoo_client = OdooClient(config['odoo'])
    
    async def generate_response(self, ticket: Ticket, intent_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response for refund-related tickets.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            context: Context information
            
        Returns:
            Generated response
        """
        try:
            # Analyze the refund request
            refund_analysis = await self._analyze_refund_request(ticket.message, context)
            
            # Check eligibility
            eligibility_result = await self._check_refund_eligibility(refund_analysis)
            
            # Generate response based on eligibility
            if eligibility_result['eligible']:
                response = self._format_eligible_refund_response(eligibility_result)
                escalation_required = False
            else:
                response = self._format_ineligible_refund_response(eligibility_result)
                escalation_required = self._should_escalate_ineligible(eligibility_result)
            
            # Check for escalation triggers
            if self._should_escalate(ticket, intent_result, refund_analysis):
                escalation_required = True
                response += "\n\n" + self._format_escalation_response()
            
            return {
                'content': response,
                'escalation_required': escalation_required,
                'metadata': {
                    'handler': 'refund',
                    'refund_type': refund_analysis.get('refund_type'),
                    'eligibility': eligibility_result,
                    'escalation_triggers': self._get_escalation_triggers(ticket, intent_result, refund_analysis)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating refund response: {str(e)}")
            return {
                'content': self._format_error_response(),
                'escalation_required': True,
                'metadata': {'error': str(e)}
            }
    
    async def _analyze_refund_request(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the refund request.
        
        Args:
            message: Customer message
            context: Context information
            
        Returns:
            Refund analysis
        """
        message_lower = message.lower()
        
        # Detect refund type
        refund_type = 'general'
        if any(keyword in message_lower for keyword in ['annuler', 'cancel', 'annulation', 'cancellation']):
            refund_type = 'cancellation'
        elif any(keyword in message_lower for keyword in ['retourner', 'return', 'retour', 'send back']):
            refund_type = 'return'
        elif any(keyword in message_lower for keyword in ['remboursement', 'refund', 'argent', 'money']):
            refund_type = 'refund'
        
        # Extract order information
        order_numbers = self._extract_order_numbers(message)
        
        # Detect urgency
        urgency = 'normal'
        if any(keyword in message_lower for keyword in ['urgent', 'urgent', 'asap', 'rapidement']):
            urgency = 'high'
        
        # Detect reason
        reason = self._extract_refund_reason(message)
        
        return {
            'refund_type': refund_type,
            'order_numbers': order_numbers,
            'urgency': urgency,
            'reason': reason,
            'message': message
        }
    
    def _extract_order_numbers(self, message: str) -> List[str]:
        """
        Extract order numbers from the message.
        
        Args:
            message: Customer message
            
        Returns:
            List of order numbers
        """
        import re
        
        # Look for order number patterns
        order_patterns = [
            r'\b(?:so|commande|order|ord)\s*[:\-]?\s*(\d+)\b',
            r'\b(?:ref|réf|reference)\s*[:\-]?\s*(\d+)\b'
        ]
        
        order_numbers = []
        for pattern in order_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            order_numbers.extend(matches)
        
        return order_numbers
    
    def _extract_refund_reason(self, message: str) -> str:
        """
        Extract refund reason from the message.
        
        Args:
            message: Customer message
            
        Returns:
            Refund reason
        """
        message_lower = message.lower()
        
        # Common refund reasons
        reasons = {
            'defective': ['défectueux', 'defective', 'cassé', 'broken', 'ne marche pas', 'doesn\'t work'],
            'wrong_item': ['mauvais', 'wrong', 'pas le bon', 'not the right', 'erreur', 'mistake'],
            'not_as_described': ['pas comme décrit', 'not as described', 'différent', 'different'],
            'changed_mind': ['changement d\'avis', 'changed mind', 'plus besoin', 'no longer need'],
            'delivery_issue': ['livraison', 'delivery', 'problème', 'problem', 'retard', 'delay']
        }
        
        for reason, keywords in reasons.items():
            if any(keyword in message_lower for keyword in keywords):
                return reason
        
        return 'other'
    
    async def _check_refund_eligibility(self, refund_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check refund eligibility.
        
        Args:
            refund_analysis: Refund analysis results
            
        Returns:
            Eligibility result
        """
        eligibility = {
            'eligible': False,
            'reasons': [],
            'conditions': [],
            'timeline': None,
            'amount': None
        }
        
        # Check order information
        if refund_analysis.get('order_numbers'):
            order_number = refund_analysis['order_numbers'][0]
            order_info = await self.odoo_client.get_order(order_number)
            
            if order_info:
                eligibility['order_found'] = True
                eligibility['order_info'] = order_info
                
                # Check order status
                if order_info['state'] in ['sale', 'done']:
                    eligibility['order_status'] = 'valid'
                    
                    # Check delivery date for return window
                    if self._check_return_window(order_info):
                        eligibility['within_window'] = True
                        eligibility['eligible'] = True
                        eligibility['timeline'] = '5-7 jours ouvrés'
                    else:
                        eligibility['within_window'] = False
                        eligibility['reasons'].append('Délai de retour dépassé')
                else:
                    eligibility['order_status'] = 'invalid'
                    eligibility['reasons'].append('Commande non confirmée')
            else:
                eligibility['order_found'] = False
                eligibility['reasons'].append('Commande non trouvée')
        else:
            eligibility['reasons'].append('Numéro de commande manquant')
        
        # Check refund type specific conditions
        refund_type = refund_analysis.get('refund_type')
        if refund_type == 'cancellation':
            eligibility['conditions'].append('Annulation possible avant expédition')
        elif refund_type == 'return':
            eligibility['conditions'].append('Retour possible dans les 30 jours')
        elif refund_type == 'refund':
            eligibility['conditions'].append('Remboursement selon conditions')
        
        return eligibility
    
    def _check_return_window(self, order_info: Dict[str, Any]) -> bool:
        """
        Check if order is within return window.
        
        Args:
            order_info: Order information
            
        Returns:
            True if within return window
        """
        try:
            # Check if order is within 30 days
            order_date = datetime.fromisoformat(order_info['date_order'].replace('Z', '+00:00'))
            current_date = datetime.utcnow()
            
            # 30 days return window
            return_window = timedelta(days=30)
            
            return (current_date - order_date) <= return_window
            
        except Exception as e:
            self.logger.error(f"Error checking return window: {str(e)}")
            return False
    
    def _format_eligible_refund_response(self, eligibility_result: Dict[str, Any]) -> str:
        """
        Format response for eligible refunds.
        
        Args:
            eligibility_result: Eligibility result
            
        Returns:
            Formatted response
        """
        response = "Votre demande de remboursement est **éligible** !\n\n"
        
        response += "**Processus de remboursement :**\n"
        response += "1. **Validation** : Votre demande sera vérifiée\n"
        response += "2. **Traitement** : Remboursement sous 5-7 jours ouvrés\n"
        response += "3. **Confirmation** : Vous recevrez un email de confirmation\n\n"
        
        response += "**Informations importantes :**\n"
        response += f"• **Délai de traitement** : {eligibility_result.get('timeline', '5-7 jours ouvrés')}\n"
        response += "• **Mode de remboursement** : Même moyen de paiement\n"
        response += "• **Suivi** : Numéro de référence fourni\n\n"
        
        response += "**Prochaines étapes :**\n"
        response += "• Votre demande est en cours de traitement\n"
        response += "• Vous recevrez une confirmation par email\n"
        response += "• Le remboursement apparaîtra sur votre relevé\n\n"
        
        response += "Avez-vous des questions sur le processus de remboursement ?"
        
        return response
    
    def _format_ineligible_refund_response(self, eligibility_result: Dict[str, Any]) -> str:
        """
        Format response for ineligible refunds.
        
        Args:
            eligibility_result: Eligibility result
            
        Returns:
            Formatted response
        """
        response = "Je comprends votre demande de remboursement.\n\n"
        
        response += "**Statut de votre demande :**\n"
        response += "Malheureusement, votre demande ne peut pas être traitée automatiquement.\n\n"
        
        if eligibility_result.get('reasons'):
            response += "**Raisons :**\n"
            for reason in eligibility_result['reasons']:
                response += f"• {reason}\n"
            response += "\n"
        
        response += "**Solutions possibles :**\n"
        response += "• **Échange** : Produit défectueux → Échange gratuit\n"
        response += "• **Crédit** : Crédit boutique pour futurs achats\n"
        response += "• **Exception** : Cas particuliers étudiés individuellement\n\n"
        
        response += "**Notre politique de retour :**\n"
        response += "• Retour possible dans les 30 jours\n"
        response += "• Produit en état original\n"
        response += "• Emballage d'origine conservé\n\n"
        
        response += "Je vais transférer votre demande à notre équipe qui pourra étudier votre cas spécifiquement."
        
        return response
    
    def _format_escalation_response(self) -> str:
        """
        Format escalation response.
        
        Returns:
            Formatted response
        """
        return """**Votre demande nécessite une attention particulière.**

Je vais transférer votre demande à notre équipe spécialisée qui pourra :
• Étudier votre cas spécifiquement
• Proposer des solutions alternatives
• Trouver un arrangement satisfaisant

Vous devriez recevoir une réponse dans les plus brefs délais."""
    
    def _format_error_response(self) -> str:
        """
        Format error response.
        
        Returns:
            Formatted response
        """
        return """Je rencontre une difficulté technique pour traiter votre demande de remboursement.

Votre demande a été enregistrée et sera traitée par notre équipe.

Si votre demande est urgente, n'hésitez pas à nous contacter directement."""
    
    def _should_escalate(self, ticket: Ticket, intent_result: Dict[str, Any], refund_analysis: Dict[str, Any]) -> bool:
        """
        Check if ticket should be escalated.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            refund_analysis: Refund analysis results
            
        Returns:
            True if escalation is required
        """
        # Check for high-value refunds
        if refund_analysis.get('order_numbers'):
            # This would check order value in real implementation
            pass
        
        # Check urgency
        if refund_analysis.get('urgency') == 'high':
            return True
        
        # Check sentiment
        if intent_result.get('sentiment') == 'negative' and intent_result.get('emotion_level', 0) > 3:
            return True
        
        # Check for special circumstances
        special_reasons = ['defective', 'wrong_item', 'not_as_described']
        if refund_analysis.get('reason') in special_reasons:
            return True
        
        return False
    
    def _should_escalate_ineligible(self, eligibility_result: Dict[str, Any]) -> bool:
        """
        Check if ineligible refund should be escalated.
        
        Args:
            eligibility_result: Eligibility result
            
        Returns:
            True if escalation is required
        """
        # Always escalate ineligible refunds for human review
        return True
    
    def _get_escalation_triggers(self, ticket: Ticket, intent_result: Dict[str, Any], refund_analysis: Dict[str, Any]) -> List[str]:
        """
        Get list of escalation triggers.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            refund_analysis: Refund analysis results
            
        Returns:
            List of escalation triggers
        """
        triggers = []
        
        if refund_analysis.get('urgency') == 'high':
            triggers.append('high_urgency')
        
        if intent_result.get('sentiment') == 'negative':
            triggers.append('negative_sentiment')
        
        if refund_analysis.get('reason') in ['defective', 'wrong_item']:
            triggers.append('product_issue')
        
        if not refund_analysis.get('order_numbers'):
            triggers.append('missing_order_info')
        
        return triggers
