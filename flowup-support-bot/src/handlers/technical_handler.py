"""
Technical support handler for the flowup-support-bot.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models.ticket import Ticket
from ..rag.retriever import ContextRetriever
from ..utils.logger import get_logger


class TechnicalHandler:
    """
    Handler for technical support requests.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the technical handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.context_retriever = ContextRetriever(config)
    
    async def generate_response(self, ticket: Ticket, intent_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response for technical support tickets.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            context: Context information
            
        Returns:
            Generated response
        """
        try:
            # Analyze the technical issue
            issue_analysis = await self._analyze_technical_issue(ticket.message, context)
            
            # Search for solutions in knowledge base
            solutions = await self._search_solutions(issue_analysis, context)
            
            # Generate response based on solutions found
            if solutions:
                response = self._format_solution_response(issue_analysis, solutions)
                escalation_required = False
            else:
                response = self._format_no_solution_response(issue_analysis)
                escalation_required = True
            
            # Check for escalation triggers
            if self._should_escalate(ticket, intent_result, issue_analysis):
                escalation_required = True
                response += "\n\n" + self._format_escalation_response()
            
            return {
                'content': response,
                'escalation_required': escalation_required,
                'metadata': {
                    'handler': 'technical',
                    'issue_type': issue_analysis.get('issue_type'),
                    'complexity': issue_analysis.get('complexity'),
                    'solutions_found': len(solutions) if solutions else 0,
                    'escalation_triggers': self._get_escalation_triggers(ticket, intent_result, issue_analysis)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating technical response: {str(e)}")
            return {
                'content': self._format_error_response(),
                'escalation_required': True,
                'metadata': {'error': str(e)}
            }
    
    async def _analyze_technical_issue(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the technical issue described in the message.
        
        Args:
            message: Customer message
            context: Context information
            
        Returns:
            Issue analysis
        """
        # Extract technical keywords
        technical_keywords = {
            'bug': ['bug', 'erreur', 'error', 'dysfonctionnement', 'malfunction'],
            'performance': ['lent', 'slow', 'performance', 'ralentit', 'lag'],
            'installation': ['install', 'installation', 'setup', 'configuration'],
            'compatibility': ['compatible', 'compatibility', 'version', 'update'],
            'data': ['données', 'data', 'perte', 'loss', 'corruption'],
            'security': ['sécurité', 'security', 'accès', 'access', 'permission']
        }
        
        message_lower = message.lower()
        detected_issues = []
        
        for issue_type, keywords in technical_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_issues.append(issue_type)
        
        # Determine complexity
        complexity = self._assess_complexity(message, detected_issues)
        
        # Extract error messages or specific details
        error_details = self._extract_error_details(message)
        
        return {
            'issue_type': detected_issues[0] if detected_issues else 'general',
            'all_issues': detected_issues,
            'complexity': complexity,
            'error_details': error_details,
            'message': message
        }
    
    def _assess_complexity(self, message: str, detected_issues: List[str]) -> str:
        """
        Assess the complexity of the technical issue.
        
        Args:
            message: Customer message
            detected_issues: List of detected issue types
            
        Returns:
            Complexity level (low, medium, high)
        """
        complexity_indicators = {
            'high': [
                'données perdues', 'data loss', 'corruption', 'sécurité compromise',
                'security breach', 'système planté', 'system crash', 'critique'
            ],
            'medium': [
                'configuration', 'setup', 'installation', 'compatibility',
                'performance', 'lent', 'slow', 'problème récurrent'
            ]
        }
        
        message_lower = message.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                return level
        
        # Check for multiple issues
        if len(detected_issues) > 2:
            return 'high'
        elif len(detected_issues) > 1:
            return 'medium'
        else:
            return 'low'
    
    def _extract_error_details(self, message: str) -> List[str]:
        """
        Extract error details from the message.
        
        Args:
            message: Customer message
            
        Returns:
            List of error details
        """
        import re
        
        # Look for error patterns
        error_patterns = [
            r'erreur[:\s]+([^.!?]+)',
            r'error[:\s]+([^.!?]+)',
            r'exception[:\s]+([^.!?]+)',
            r'fatal[:\s]+([^.!?]+)'
        ]
        
        error_details = []
        for pattern in error_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            error_details.extend(matches)
        
        return error_details
    
    async def _search_solutions(self, issue_analysis: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for solutions in the knowledge base.
        
        Args:
            issue_analysis: Issue analysis results
            context: Context information
            
        Returns:
            List of solutions
        """
        try:
            # Use RAG system to find relevant solutions
            search_query = f"{issue_analysis['issue_type']} {issue_analysis['message']}"
            solutions = await self.context_retriever.retrieve_context(search_query)
            
            # Filter and rank solutions
            filtered_solutions = self._filter_solutions(solutions, issue_analysis)
            
            return filtered_solutions[:3]  # Return top 3 solutions
            
        except Exception as e:
            self.logger.error(f"Error searching solutions: {str(e)}")
            return []
    
    def _filter_solutions(self, solutions: Dict[str, Any], issue_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter and rank solutions based on relevance.
        
        Args:
            solutions: Raw solutions from knowledge base
            context: Context information
            
        Returns:
            Filtered and ranked solutions
        """
        # This would implement solution filtering logic
        # For now, return empty list
        return []
    
    def _format_solution_response(self, issue_analysis: Dict[str, Any], solutions: List[Dict[str, Any]]) -> str:
        """
        Format response with solutions.
        
        Args:
            issue_analysis: Issue analysis results
            solutions: List of solutions
            
        Returns:
            Formatted response
        """
        response = f"Je comprends que vous rencontrez un problème de type **{issue_analysis['issue_type']}**.\n\n"
        
        response += "**Voici les solutions que je recommande :**\n\n"
        
        for i, solution in enumerate(solutions, 1):
            response += f"**Solution {i} :**\n"
            response += f"{solution.get('content', 'Solution non disponible')}\n\n"
        
        response += "**Étapes de résolution :**\n"
        response += "1. Essayez les solutions dans l'ordre proposé\n"
        response += "2. Testez après chaque étape\n"
        response += "3. Si le problème persiste, contactez-nous avec les détails\n\n"
        
        response += "**Informations utiles :**\n"
        response += "• Version de votre système\n"
        response += "• Messages d'erreur exacts\n"
        response += "• Étapes qui ont mené au problème\n\n"
        
        response += "Ces informations m'aideront à vous fournir une assistance plus précise."
        
        return response
    
    def _format_no_solution_response(self, issue_analysis: Dict[str, Any]) -> str:
        """
        Format response when no solutions are found.
        
        Args:
            issue_analysis: Issue analysis results
            
        Returns:
            Formatted response
        """
        response = f"Je comprends que vous rencontrez un problème de type **{issue_analysis['issue_type']}**.\n\n"
        
        response += "Malheureusement, je n'ai pas trouvé de solution spécifique dans notre base de connaissances pour ce type de problème.\n\n"
        
        response += "**Pour vous aider efficacement, j'ai besoin de :**\n"
        response += "• Une description détaillée du problème\n"
        response += "• Les messages d'erreur exacts\n"
        response += "• Les étapes qui ont mené au problème\n"
        response += "• Votre version de système\n\n"
        
        response += "**En attendant, vous pouvez essayer :**\n"
        response += "• Redémarrer l'application\n"
        response += "• Vérifier votre connexion internet\n"
        response += "• Mettre à jour vers la dernière version\n\n"
        
        response += "Je vais transférer votre demande à notre équipe technique qui pourra vous aider plus spécifiquement."
        
        return response
    
    def _format_escalation_response(self) -> str:
        """
        Format escalation response.
        
        Returns:
            Formatted response
        """
        return """**Votre demande nécessite une expertise technique avancée.**

Je vais transférer votre demande à notre équipe de développeurs qui pourra :
• Analyser le problème en détail
• Fournir une solution personnalisée
• Vous accompagner dans la résolution

Vous devriez recevoir une réponse dans les plus brefs délais."""
    
    def _format_error_response(self) -> str:
        """
        Format error response.
        
        Returns:
            Formatted response
        """
        return """Je rencontre une difficulté technique pour analyser votre problème.

Votre demande a été enregistrée et sera traitée par notre équipe technique.

Si votre problème est urgent, n'hésitez pas à nous contacter directement."""
    
    def _should_escalate(self, ticket: Ticket, intent_result: Dict[str, Any], issue_analysis: Dict[str, Any]) -> bool:
        """
        Check if ticket should be escalated.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            issue_analysis: Issue analysis results
            
        Returns:
            True if escalation is required
        """
        # Check complexity
        if issue_analysis.get('complexity') == 'high':
            return True
        
        # Check for critical issues
        critical_issues = ['data', 'security', 'system_crash']
        if any(issue in issue_analysis.get('all_issues', []) for issue in critical_issues):
            return True
        
        # Check confidence
        if intent_result.get('confidence', 0) < 0.8:
            return True
        
        # Check sentiment
        if intent_result.get('sentiment') == 'negative' and intent_result.get('emotion_level', 0) > 3:
            return True
        
        return False
    
    def _get_escalation_triggers(self, ticket: Ticket, intent_result: Dict[str, Any], issue_analysis: Dict[str, Any]) -> List[str]:
        """
        Get list of escalation triggers.
        
        Args:
            ticket: The ticket object
            intent_result: Intent analysis results
            issue_analysis: Issue analysis results
            
        Returns:
            List of escalation triggers
        """
        triggers = []
        
        if issue_analysis.get('complexity') == 'high':
            triggers.append('high_complexity')
        
        if any(issue in issue_analysis.get('all_issues', []) for issue in ['data', 'security']):
            triggers.append('critical_issue')
        
        if intent_result.get('confidence', 0) < 0.8:
            triggers.append('low_confidence')
        
        if intent_result.get('sentiment') == 'negative':
            triggers.append('negative_sentiment')
        
        return triggers
