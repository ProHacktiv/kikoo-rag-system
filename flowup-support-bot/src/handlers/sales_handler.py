"""
Sales handler for the flowup-support-bot.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models.ticket import Ticket
from ..integrations.odoo_client import OdooClient
from ..rag.retriever import ContextRetriever
from ..utils.logger import get_logger


class SalesHandler:
    """
    Handler for sales-related support requests.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the sales handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.odoo_client = OdooClient(config['odoo'])
        self.context_retriever = ContextRetriever(config)
    
    async def generate_response(self, ticket: Ticket, intent_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response for sales-related tickets.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            context: Context information
            
        Returns:
            Generated response
        """
        try:
            # Analyze the sales request
            request_analysis = await self._analyze_sales_request(ticket.message, context)
            
            # Generate appropriate response based on request type
            if request_analysis['request_type'] == 'product_info':
                response = await self._handle_product_info_request(request_analysis)
            elif request_analysis['request_type'] == 'pricing':
                response = await self._handle_pricing_request(request_analysis)
            elif request_analysis['request_type'] == 'quote':
                response = await self._handle_quote_request(request_analysis)
            elif request_analysis['request_type'] == 'comparison':
                response = await self._handle_comparison_request(request_analysis)
            else:
                response = await self._handle_general_sales_request(request_analysis)
            
            # Check for escalation triggers
            escalation_required = self._should_escalate(ticket, intent_result, request_analysis)
            if escalation_required:
                response += "\n\n" + self._format_escalation_response()
            
            return {
                'content': response,
                'escalation_required': escalation_required,
                'metadata': {
                    'handler': 'sales',
                    'request_type': request_analysis['request_type'],
                    'products_mentioned': request_analysis.get('products', []),
                    'escalation_triggers': self._get_escalation_triggers(ticket, intent_result, request_analysis)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating sales response: {str(e)}")
            return {
                'content': self._format_error_response(),
                'escalation_required': True,
                'metadata': {'error': str(e)}
            }
    
    async def _analyze_sales_request(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the sales request.
        
        Args:
            message: Customer message
            context: Context information
            
        Returns:
            Request analysis
        """
        message_lower = message.lower()
        
        # Detect request type
        request_type = 'general'
        if any(keyword in message_lower for keyword in ['prix', 'price', 'coût', 'cost', 'combien', 'how much']):
            request_type = 'pricing'
        elif any(keyword in message_lower for keyword in ['devis', 'quote', 'estimation', 'budget']):
            request_type = 'quote'
        elif any(keyword in message_lower for keyword in ['comparer', 'compare', 'différence', 'difference']):
            request_type = 'comparison'
        elif any(keyword in message_lower for keyword in ['produit', 'product', 'fonctionnalité', 'feature']):
            request_type = 'product_info'
        
        # Extract mentioned products
        products = self._extract_mentioned_products(message)
        
        # Detect urgency
        urgency = 'normal'
        if any(keyword in message_lower for keyword in ['urgent', 'urgent', 'asap', 'rapidement']):
            urgency = 'high'
        elif any(keyword in message_lower for keyword in ['quand', 'when', 'délai', 'timeline']):
            urgency = 'medium'
        
        # Detect budget range
        budget_range = self._extract_budget_range(message)
        
        return {
            'request_type': request_type,
            'products': products,
            'urgency': urgency,
            'budget_range': budget_range,
            'message': message
        }
    
    def _extract_mentioned_products(self, message: str) -> List[str]:
        """
        Extract mentioned products from the message.
        
        Args:
            message: Customer message
            
        Returns:
            List of mentioned products
        """
        # This would implement product extraction logic
        # For now, return empty list
        return []
    
    def _extract_budget_range(self, message: str) -> Optional[str]:
        """
        Extract budget range from the message.
        
        Args:
            message: Customer message
            
        Returns:
            Budget range or None
        """
        import re
        
        # Look for budget patterns
        budget_patterns = [
            r'budget[:\s]+([0-9,]+)',
            r'budget[:\s]+([0-9,]+)\s*€',
            r'jusqu\'à\s+([0-9,]+)',
            r'up to\s+([0-9,]+)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _handle_product_info_request(self, request_analysis: Dict[str, Any]) -> str:
        """
        Handle product information requests.
        
        Args:
            request_analysis: Request analysis results
            
        Returns:
            Formatted response
        """
        response = "Je serais ravi de vous renseigner sur nos produits Flowup !\n\n"
        
        if request_analysis.get('products'):
            response += f"Vous mentionnez : {', '.join(request_analysis['products'])}\n\n"
        
        response += "**Nos principales solutions :**\n\n"
        response += "• **Flowup Core** - Solution de base pour PME\n"
        response += "• **Flowup Pro** - Version avancée avec fonctionnalités étendues\n"
        response += "• **Flowup Enterprise** - Solution complète pour grandes entreprises\n\n"
        
        response += "**Fonctionnalités principales :**\n"
        response += "• Gestion des commandes et stocks\n"
        response += "• Suivi des livraisons\n"
        response += "• Interface utilisateur intuitive\n"
        response += "• Intégrations tierces\n\n"
        
        response += "Souhaitez-vous des informations spécifiques sur une solution ou avez-vous des questions particulières ?"
        
        return response
    
    async def _handle_pricing_request(self, request_analysis: Dict[str, Any]) -> str:
        """
        Handle pricing requests.
        
        Args:
            request_analysis: Request analysis results
            
        Returns:
            Formatted response
        """
        response = "Voici nos tarifs Flowup :\n\n"
        
        response += "**Tarifs mensuels :**\n"
        response += "• **Flowup Core** : 29€/mois\n"
        response += "• **Flowup Pro** : 59€/mois\n"
        response += "• **Flowup Enterprise** : Sur devis\n\n"
        
        response += "**Options disponibles :**\n"
        response += "• Support technique inclus\n"
        response += "• Formation utilisateur\n"
        response += "• Intégrations personnalisées\n"
        response += "• Hébergement sécurisé\n\n"
        
        if request_analysis.get('budget_range'):
            response += f"Je vois que votre budget est autour de {request_analysis['budget_range']}€. "
            response += "Cela correspond parfaitement à nos solutions Flowup Core ou Pro.\n\n"
        
        response += "**Avantages :**\n"
        response += "• Essai gratuit 30 jours\n"
        response += "• Pas d'engagement\n"
        response += "• Support dédié\n"
        response += "• Mises à jour incluses\n\n"
        
        response += "Souhaitez-vous un devis personnalisé ou avez-vous des questions sur nos tarifs ?"
        
        return response
    
    async def _handle_quote_request(self, request_analysis: Dict[str, Any]) -> str:
        """
        Handle quote requests.
        
        Args:
            request_analysis: Request analysis results
            
        Returns:
            Formatted response
        """
        response = "Je vais préparer un devis personnalisé pour vous !\n\n"
        
        response += "**Pour créer votre devis, j'ai besoin de :**\n"
        response += "• Nombre d'utilisateurs\n"
        response += "• Fonctionnalités souhaitées\n"
        response += "• Intégrations nécessaires\n"
        response += "• Durée du contrat\n\n"
        
        response += "**Processus de devis :**\n"
        response += "1. Analyse de vos besoins\n"
        response += "2. Proposition personnalisée\n"
        response += "3. Démonstration si souhaitée\n"
        response += "4. Devis détaillé sous 24h\n\n"
        
        response += "**Avantages de notre approche :**\n"
        response += "• Solution sur mesure\n"
        response += "• Accompagnement personnalisé\n"
        response += "• Formation incluse\n"
        response += "• Support dédié\n\n"
        
        response += "Pouvez-vous me donner plus de détails sur vos besoins spécifiques ?"
        
        return response
    
    async def _handle_comparison_request(self, request_analysis: Dict[str, Any]) -> str:
        """
        Handle product comparison requests.
        
        Args:
            request_analysis: Request analysis results
            
        Returns:
            Formatted response
        """
        response = "Voici une comparaison de nos solutions Flowup :\n\n"
        
        response += "**Flowup Core vs Pro :**\n\n"
        response += "| Fonctionnalité | Core | Pro |\n"
        response += "|----------------|------|-----|\n"
        response += "| Gestion commandes | ✅ | ✅ |\n"
        response += "| Suivi livraisons | ✅ | ✅ |\n"
        response += "| Rapports avancés | ❌ | ✅ |\n"
        response += "| Intégrations | Basiques | Avancées |\n"
        response += "| Support | Standard | Prioritaire |\n\n"
        
        response += "**Flowup Pro vs Enterprise :**\n\n"
        response += "| Fonctionnalité | Pro | Enterprise |\n"
        response += "|----------------|-----|------------|\n"
        response += "| Utilisateurs | Jusqu'à 50 | Illimité |\n"
        response += "| Stockage | 100GB | Illimité |\n"
        response += "| API | Standard | Complète |\n"
        response += "| Support | Prioritaire | Dédié |\n\n"
        
        response += "**Recommandation :**\n"
        response += "• **Flowup Core** : Parfait pour débuter\n"
        response += "• **Flowup Pro** : Idéal pour la croissance\n"
        response += "• **Flowup Enterprise** : Solution complète\n\n"
        
        response += "Quelle solution correspond le mieux à vos besoins actuels ?"
        
        return response
    
    async def _handle_general_sales_request(self, request_analysis: Dict[str, Any]) -> str:
        """
        Handle general sales requests.
        
        Args:
            request_analysis: Request analysis results
            
        Returns:
            Formatted response
        """
        response = "Je suis là pour vous aider avec toutes vos questions commerciales !\n\n"
        
        response += "**Je peux vous aider avec :**\n"
        response += "• Informations sur nos produits\n"
        response += "• Tarifs et devis\n"
        response += "• Comparaisons de solutions\n"
        response += "• Démonstrations\n"
        response += "• Intégrations\n\n"
        
        response += "**Nos solutions Flowup :**\n"
        response += "• Gestion complète des commandes\n"
        response += "• Suivi des livraisons en temps réel\n"
        response += "• Interface intuitive et moderne\n"
        response += "• Support technique dédié\n\n"
        
        response += "**Prochaines étapes :**\n"
        response += "1. Définir vos besoins\n"
        response += "2. Choisir la solution adaptée\n"
        response += "3. Essai gratuit 30 jours\n"
        response += "4. Accompagnement personnalisé\n\n"
        
        response += "Quelle est votre question ou votre besoin spécifique ?"
        
        return response
    
    def _format_escalation_response(self) -> str:
        """
        Format escalation response.
        
        Returns:
            Formatted response
        """
        return """**Votre demande nécessite une attention commerciale spécialisée.**

Je vais transférer votre demande à notre équipe commerciale qui pourra :
• Vous proposer une solution personnalisée
• Organiser une démonstration
• Préparer un devis détaillé
• Vous accompagner dans votre choix

Vous devriez recevoir une réponse dans les plus brefs délais."""
    
    def _format_error_response(self) -> str:
        """
        Format error response.
        
        Returns:
            Formatted response
        """
        return """Je rencontre une difficulté technique pour traiter votre demande commerciale.

Votre demande a été enregistrée et sera traitée par notre équipe commerciale.

Si votre demande est urgente, n'hésitez pas à nous contacter directement."""
    
    def _should_escalate(self, ticket: Ticket, intent_result: Dict[str, Any], request_analysis: Dict[str, Any]) -> bool:
        """
        Check if ticket should be escalated.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            request_analysis: Request analysis results
            
        Returns:
            True if escalation is required
        """
        # Check for high-value opportunities
        if request_analysis.get('budget_range'):
            try:
                budget = int(request_analysis['budget_range'].replace(',', ''))
                if budget > 1000:  # High-value opportunity
                    return True
            except ValueError:
                pass
        
        # Check for enterprise requests
        if request_analysis['request_type'] == 'quote' and request_analysis.get('urgency') == 'high':
            return True
        
        # Check for complex requirements
        if len(request_analysis.get('products', [])) > 2:
            return True
        
        # Check confidence
        if intent_result.get('confidence', 0) < 0.7:
            return True
        
        return False
    
    def _get_escalation_triggers(self, ticket: Ticket, intent_result: Dict[str, Any], request_analysis: Dict[str, Any]) -> List[str]:
        """
        Get list of escalation triggers.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            request_analysis: Request analysis results
            
        Returns:
            List of escalation triggers
        """
        triggers = []
        
        if request_analysis.get('budget_range'):
            try:
                budget = int(request_analysis['budget_range'].replace(',', ''))
                if budget > 1000:
                    triggers.append('high_value_opportunity')
            except ValueError:
                pass
        
        if request_analysis['request_type'] == 'quote':
            triggers.append('quote_request')
        
        if request_analysis.get('urgency') == 'high':
            triggers.append('high_urgency')
        
        if intent_result.get('confidence', 0) < 0.7:
            triggers.append('low_confidence')
        
        return triggers
