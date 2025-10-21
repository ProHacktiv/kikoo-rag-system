#!/usr/bin/env python3
"""
Script to import tickets from Odoo into the knowledge base.
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.integrations.odoo_client import OdooClient
from src.rag.knowledge_base import KnowledgeBase
from src.utils.logger import get_logger


async def main():
    """Main function to import tickets."""
    parser = argparse.ArgumentParser(description='Import tickets from Odoo')
    parser.add_argument('--config', default='config/settings.yaml', help='Configuration file path')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of tickets to import')
    parser.add_argument('--status', default='done', help='Ticket status to import')
    parser.add_argument('--category', help='Ticket category to filter by')
    parser.add_argument('--date-from', help='Start date for ticket filtering (YYYY-MM-DD)')
    parser.add_argument('--date-to', help='End date for ticket filtering (YYYY-MM-DD)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger(__name__)
    if args.verbose:
        logger.info("Starting ticket import process")
    
    try:
        # Load configuration
        import yaml
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Initialize Odoo client
        odoo_client = OdooClient(config['odoo'])
        
        # Initialize knowledge base
        kb = KnowledgeBase(config)
        
        # Search for tickets in Odoo
        logger.info(f"Searching for tickets with status: {args.status}")
        
        # Build search criteria
        search_criteria = [('stage_id.name', '=', args.status)]
        
        if args.category:
            search_criteria.append(('tag_ids.name', '=', args.category))
        
        if args.date_from:
            search_criteria.append(('create_date', '>=', args.date_from))
        
        if args.date_to:
            search_criteria.append(('create_date', '<=', args.date_to))
        
        # Get ticket IDs
        ticket_ids = odoo_client.models.execute_kw(
            odoo_client.database, odoo_client.uid, odoo_client.password,
            'helpdesk.ticket', 'search',
            [search_criteria],
            {'limit': args.limit, 'order': 'create_date desc'}
        )
        
        logger.info(f"Found {len(ticket_ids)} tickets to import")
        
        if not ticket_ids:
            logger.info("No tickets found matching criteria")
            return
        
        # Get ticket details
        tickets = odoo_client.models.execute_kw(
            odoo_client.database, odoo_client.uid, odoo_client.password,
            'helpdesk.ticket', 'read',
            ticket_ids,
            {'fields': [
                'name', 'description', 'partner_id', 'priority', 'stage_id',
                'create_date', 'write_date', 'tag_ids', 'user_id', 'team_id'
            ]}
        )
        
        # Process tickets
        imported_count = 0
        failed_count = 0
        
        for ticket in tickets:
            try:
                # Extract ticket information
                ticket_data = {
                    'id': ticket['name'],
                    'subject': ticket['name'],
                    'description': ticket.get('description', ''),
                    'customer_id': ticket.get('partner_id', [None, None])[0] if ticket.get('partner_id') else None,
                    'customer_name': ticket.get('partner_id', [None, None])[1] if ticket.get('partner_id') else None,
                    'priority': ticket.get('priority', '1'),
                    'status': ticket.get('stage_id', [None, None])[1] if ticket.get('stage_id') else None,
                    'created_at': ticket.get('create_date', ''),
                    'resolved_at': ticket.get('write_date', ''),
                    'tags': [tag[1] for tag in ticket.get('tag_ids', [])],
                    'assigned_user': ticket.get('user_id', [None, None])[1] if ticket.get('user_id') else None,
                    'team': ticket.get('team_id', [None, None])[1] if ticket.get('team_id') else None
                }
                
                # Determine category from tags or content
                category = 'general'
                if ticket_data['tags']:
                    category = ticket_data['tags'][0].lower()
                elif 'livraison' in ticket_data['description'].lower() or 'commande' in ticket_data['description'].lower():
                    category = 'delivery'
                elif 'erreur' in ticket_data['description'].lower() or 'problème' in ticket_data['description'].lower():
                    category = 'technical'
                elif 'prix' in ticket_data['description'].lower() or 'devis' in ticket_data['description'].lower():
                    category = 'sales'
                elif 'remboursement' in ticket_data['description'].lower() or 'annuler' in ticket_data['description'].lower():
                    category = 'refund'
                
                ticket_data['category'] = category
                
                # Create solution text (for now, use description as solution)
                solution = ticket_data['description']
                if not solution:
                    solution = f"Ticket résolu: {ticket_data['subject']}"
                
                ticket_data['solution'] = solution
                
                # Add to knowledge base
                success = await kb.add_resolved_ticket(ticket_data)
                
                if success:
                    imported_count += 1
                    if args.verbose:
                        logger.info(f"Imported ticket: {ticket_data['id']}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to import ticket: {ticket_data['id']}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing ticket {ticket.get('name', 'unknown')}: {str(e)}")
        
        logger.info(f"Import completed: {imported_count} imported, {failed_count} failed")
        
        # Get updated statistics
        stats = kb.get_knowledge_base_stats()
        logger.info(f"Updated knowledge base statistics: {stats}")
        
    except Exception as e:
        logger.error(f"Error importing tickets: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
