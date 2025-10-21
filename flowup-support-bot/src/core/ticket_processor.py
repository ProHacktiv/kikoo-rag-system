"""
Main ticket processor for the flowup-support-bot.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models.ticket import Ticket
from ..models.customer import Customer
from .intent_analyzer import IntentAnalyzer
from .response_generator import ResponseGenerator
from ..integrations.database import DatabaseConnection
from ..utils.logger import get_logger


class TicketProcessor:
    """
    Main processor for handling support tickets.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ticket processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.intent_analyzer = IntentAnalyzer(config)
        self.response_generator = ResponseGenerator(config)
        self.db = DatabaseConnection(config['database'])
        
    async def process_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a support ticket through the complete workflow.
        
        Args:
            ticket_data: Raw ticket data from the source system
            
        Returns:
            Processed ticket with response and metadata
        """
        try:
            # Create ticket object
            ticket = Ticket.from_dict(ticket_data)
            
            # Analyze intent
            intent_result = await self.intent_analyzer.analyze_intent(
                ticket.message,
                ticket.customer_id
            )
            
            # Update ticket with intent analysis
            ticket.intent = intent_result['intent']
            ticket.confidence = intent_result['confidence']
            ticket.sentiment = intent_result['sentiment']
            ticket.urgency = intent_result['urgency']
            
            # Generate response based on intent
            response = await self.response_generator.generate_response(
                ticket,
                intent_result
            )
            
            # Update ticket with response
            ticket.response = response['content']
            ticket.response_metadata = response['metadata']
            ticket.status = 'processed'
            ticket.processed_at = datetime.utcnow()
            
            # Save to database
            await self.db.save_ticket(ticket)
            
            # Log processing
            self.logger.info(
                f"Ticket {ticket.id} processed successfully",
                extra={
                    'ticket_id': ticket.id,
                    'intent': ticket.intent,
                    'confidence': ticket.confidence,
                    'processing_time': (ticket.processed_at - ticket.created_at).total_seconds()
                }
            )
            
            return {
                'ticket_id': ticket.id,
                'intent': ticket.intent,
                'confidence': ticket.confidence,
                'response': ticket.response,
                'escalation_required': response.get('escalation_required', False),
                'processing_time': (ticket.processed_at - ticket.created_at).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(
                f"Error processing ticket {ticket_data.get('id', 'unknown')}: {str(e)}",
                extra={'ticket_data': ticket_data, 'error': str(e)}
            )
            raise
    
    async def batch_process_tickets(self, tickets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple tickets in batch.
        
        Args:
            tickets_data: List of raw ticket data
            
        Returns:
            List of processed ticket results
        """
        results = []
        
        # Process tickets concurrently (with limit)
        semaphore = asyncio.Semaphore(self.config.get('max_concurrent_tickets', 10))
        
        async def process_single_ticket(ticket_data):
            async with semaphore:
                return await self.process_ticket(ticket_data)
        
        tasks = [process_single_ticket(ticket_data) for ticket_data in tickets_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to process ticket {i}: {str(result)}")
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_ticket_status(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific ticket.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            Ticket status information or None if not found
        """
        try:
            ticket = await self.db.get_ticket(ticket_id)
            if not ticket:
                return None
                
            return {
                'id': ticket.id,
                'status': ticket.status,
                'intent': ticket.intent,
                'confidence': ticket.confidence,
                'created_at': ticket.created_at,
                'processed_at': ticket.processed_at,
                'escalation_required': ticket.escalation_required
            }
        except Exception as e:
            self.logger.error(f"Error getting ticket status {ticket_id}: {str(e)}")
            return None
    
    async def escalate_ticket(self, ticket_id: str, reason: str) -> bool:
        """
        Escalate a ticket to human support.
        
        Args:
            ticket_id: ID of the ticket to escalate
            reason: Reason for escalation
            
        Returns:
            True if escalation was successful
        """
        try:
            ticket = await self.db.get_ticket(ticket_id)
            if not ticket:
                return False
            
            ticket.escalation_required = True
            ticket.escalation_reason = reason
            ticket.escalated_at = datetime.utcnow()
            
            await self.db.update_ticket(ticket)
            
            # Send notification to support team
            await self._notify_escalation(ticket)
            
            self.logger.info(f"Ticket {ticket_id} escalated: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error escalating ticket {ticket_id}: {str(e)}")
            return False
    
    async def _notify_escalation(self, ticket: Ticket) -> None:
        """
        Send notification about ticket escalation.
        
        Args:
            ticket: The escalated ticket
        """
        # Implementation would depend on notification system
        # (email, Slack, etc.)
        pass
