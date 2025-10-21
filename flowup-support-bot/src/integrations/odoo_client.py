"""
Odoo API client for the flowup-support-bot.
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import xmlrpc.client

from ..utils.logger import get_logger


class OdooClient:
    """
    Client for interacting with Odoo API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Odoo client.
        
        Args:
            config: Odoo configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        self.url = config['url']
        self.database = config['database']
        self.username = config['username']
        self.password = config['password']
        self.api_key = config.get('api_key')
        
        # Initialize XML-RPC clients
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        
        # Authenticate
        self.uid = self._authenticate()
    
    def _authenticate(self) -> int:
        """
        Authenticate with Odoo.
        
        Returns:
            User ID
        """
        try:
            uid = self.common.authenticate(
                self.database, 
                self.username, 
                self.password, 
                {}
            )
            if uid:
                self.logger.info(f"Successfully authenticated with Odoo as {self.username}")
                return uid
            else:
                raise Exception("Authentication failed")
        except Exception as e:
            self.logger.error(f"Odoo authentication error: {str(e)}")
            raise
    
    async def get_order(self, order_number: str) -> Optional[Dict[str, Any]]:
        """
        Get order information by order number.
        
        Args:
            order_number: Order number to search for
            
        Returns:
            Order information or None if not found
        """
        try:
            # Search for sale order
            order_ids = self.models.execute_kw(
                self.database, self.uid, self.password,
                'sale.order', 'search',
                [[('name', '=', order_number)]],
                {'limit': 1}
            )
            
            if not order_ids:
                return None
            
            # Get order details
            orders = self.models.execute_kw(
                self.database, self.uid, self.password,
                'sale.order', 'read',
                [order_ids[0]],
                {'fields': [
                    'name', 'partner_id', 'state', 'date_order', 'amount_total',
                    'delivery_address', 'invoice_address', 'order_line'
                ]}
            )
            
            if orders:
                order = orders[0]
                return {
                    'id': order['id'],
                    'name': order['name'],
                    'partner_id': order['partner_id'][0] if order['partner_id'] else None,
                    'partner_name': order['partner_id'][1] if order['partner_id'] else None,
                    'state': order['state'],
                    'date_order': order['date_order'],
                    'amount_total': order['amount_total'],
                    'delivery_address': order.get('delivery_address'),
                    'invoice_address': order.get('invoice_address'),
                    'order_lines': order.get('order_line', [])
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting order {order_number}: {str(e)}")
            return None
    
    async def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get customer information by ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer information or None if not found
        """
        try:
            customers = self.models.execute_kw(
                self.database, self.uid, self.password,
                'res.partner', 'read',
                [customer_id],
                {'fields': [
                    'name', 'email', 'phone', 'mobile', 'street', 'city',
                    'zip', 'country_id', 'state_id', 'is_company', 'customer_rank'
                ]}
            )
            
            if customers:
                customer = customers[0]
                return {
                    'id': customer['id'],
                    'name': customer['name'],
                    'email': customer.get('email'),
                    'phone': customer.get('phone'),
                    'mobile': customer.get('mobile'),
                    'street': customer.get('street'),
                    'city': customer.get('city'),
                    'zip': customer.get('zip'),
                    'country': customer.get('country_id')[1] if customer.get('country_id') else None,
                    'state': customer.get('state_id')[1] if customer.get('state_id') else None,
                    'is_company': customer.get('is_company', False),
                    'customer_rank': customer.get('customer_rank', 0)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting customer {customer_id}: {str(e)}")
            return None
    
    async def get_delivery_status(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Get delivery status for an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Delivery status information
        """
        try:
            # Get delivery orders (stock.picking)
            delivery_ids = self.models.execute_kw(
                self.database, self.uid, self.password,
                'stock.picking', 'search',
                [[('origin', '=', order_id)]],
                {'limit': 10}
            )
            
            if not delivery_ids:
                return None
            
            # Get delivery details
            deliveries = self.models.execute_kw(
                self.database, self.uid, self.password,
                'stock.picking', 'read',
                delivery_ids,
                {'fields': [
                    'name', 'state', 'scheduled_date', 'date_done',
                    'carrier_id', 'tracking_number', 'note'
                ]}
            )
            
            return {
                'deliveries': deliveries,
                'total_deliveries': len(deliveries),
                'last_delivery': deliveries[-1] if deliveries else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting delivery status for order {order_id}: {str(e)}")
            return None
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a support ticket in Odoo.
        
        Args:
            ticket_data: Ticket data
            
        Returns:
            Created ticket ID or None if failed
        """
        try:
            ticket_id = self.models.execute_kw(
                self.database, self.uid, self.password,
                'helpdesk.ticket', 'create',
                [{
                    'name': ticket_data.get('subject', 'Support Request'),
                    'description': ticket_data.get('description', ''),
                    'partner_id': ticket_data.get('customer_id'),
                    'priority': ticket_data.get('priority', '1'),
                    'tag_ids': ticket_data.get('tags', []),
                    'user_id': ticket_data.get('assigned_user_id'),
                    'team_id': ticket_data.get('team_id')
                }]
            )
            
            self.logger.info(f"Created ticket {ticket_id} in Odoo")
            return ticket_id
            
        except Exception as e:
            self.logger.error(f"Error creating ticket in Odoo: {str(e)}")
            return None
    
    async def update_ticket(self, ticket_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update a support ticket in Odoo.
        
        Args:
            ticket_id: Ticket ID
            update_data: Data to update
            
        Returns:
            True if successful
        """
        try:
            self.models.execute_kw(
                self.database, self.uid, self.password,
                'helpdesk.ticket', 'write',
                [[ticket_id], update_data]
            )
            
            self.logger.info(f"Updated ticket {ticket_id} in Odoo")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating ticket {ticket_id} in Odoo: {str(e)}")
            return False
    
    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Get ticket information from Odoo.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket information or None if not found
        """
        try:
            tickets = self.models.execute_kw(
                self.database, self.uid, self.password,
                'helpdesk.ticket', 'read',
                [ticket_id],
                {'fields': [
                    'name', 'description', 'partner_id', 'priority', 'state',
                    'user_id', 'team_id', 'create_date', 'write_date',
                    'tag_ids', 'message_ids'
                ]}
            )
            
            if tickets:
                return tickets[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting ticket {ticket_id} from Odoo: {str(e)}")
            return None
    
    async def search_orders_by_customer(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search orders by customer ID.
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of orders to return
            
        Returns:
            List of orders
        """
        try:
            order_ids = self.models.execute_kw(
                self.database, self.uid, self.password,
                'sale.order', 'search',
                [[('partner_id', '=', customer_id)]],
                {'limit': limit, 'order': 'date_order desc'}
            )
            
            if not order_ids:
                return []
            
            orders = self.models.execute_kw(
                self.database, self.uid, self.password,
                'sale.order', 'read',
                order_ids,
                {'fields': [
                    'name', 'state', 'date_order', 'amount_total', 'partner_id'
                ]}
            )
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Error searching orders for customer {customer_id}: {str(e)}")
            return []
    
    async def get_product_info(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get product information.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product information or None if not found
        """
        try:
            products = self.models.execute_kw(
                self.database, self.uid, self.password,
                'product.product', 'read',
                [product_id],
                {'fields': [
                    'name', 'description', 'list_price', 'standard_price',
                    'categ_id', 'type', 'sale_ok', 'purchase_ok'
                ]}
            )
            
            if products:
                return products[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting product {product_id}: {str(e)}")
            return None
