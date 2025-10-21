"""
Database connection and operations for the flowup-support-bot.
"""

import asyncio
import asyncpg
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..utils.logger import get_logger


class DatabaseConnection:
    """
    Database connection and operations handler.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database connection.
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.pool = None
        
    async def connect(self) -> None:
        """
        Establish database connection pool.
        """
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['name'],
                user=self.config['user'],
                password=self.config['password'],
                ssl=self.config.get('ssl_mode', 'prefer'),
                min_size=1,
                max_size=10
            )
            self.logger.info("Database connection pool created successfully")
        except Exception as e:
            self.logger.error(f"Error creating database connection pool: {str(e)}")
            raise
    
    async def close(self) -> None:
        """
        Close database connection pool.
        """
        if self.pool:
            await self.pool.close()
            self.logger.info("Database connection pool closed")
    
    async def save_ticket(self, ticket) -> bool:
        """
        Save a ticket to the database.
        
        Args:
            ticket: Ticket object to save
            
        Returns:
            True if successful
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO tickets (
                        id, customer_id, message, intent, confidence, sentiment,
                        urgency, response, status, created_at, processed_at,
                        escalation_required, escalation_reason, escalated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (id) DO UPDATE SET
                        intent = EXCLUDED.intent,
                        confidence = EXCLUDED.confidence,
                        sentiment = EXCLUDED.sentiment,
                        urgency = EXCLUDED.urgency,
                        response = EXCLUDED.response,
                        status = EXCLUDED.status,
                        processed_at = EXCLUDED.processed_at,
                        escalation_required = EXCLUDED.escalation_required,
                        escalation_reason = EXCLUDED.escalation_reason,
                        escalated_at = EXCLUDED.escalated_at
                """, 
                ticket.id, ticket.customer_id, ticket.message, ticket.intent,
                ticket.confidence, ticket.sentiment, ticket.urgency, ticket.response,
                ticket.status, ticket.created_at, ticket.processed_at,
                ticket.escalation_required, ticket.escalation_reason, ticket.escalated_at
                )
            
            self.logger.info(f"Saved ticket {ticket.id} to database")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving ticket {ticket.id}: {str(e)}")
            return False
    
    async def get_ticket(self, ticket_id: str):
        """
        Get a ticket by ID.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket object or None if not found
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM tickets WHERE id = $1
                """, ticket_id)
                
                if row:
                    from ..models.ticket import Ticket
                    return Ticket.from_dict(dict(row))
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting ticket {ticket_id}: {str(e)}")
            return None
    
    async def update_ticket(self, ticket) -> bool:
        """
        Update a ticket in the database.
        
        Args:
            ticket: Ticket object to update
            
        Returns:
            True if successful
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE tickets SET
                        intent = $2, confidence = $3, sentiment = $4, urgency = $5,
                        response = $6, status = $7, processed_at = $8,
                        escalation_required = $9, escalation_reason = $10, escalated_at = $11
                    WHERE id = $1
                """, 
                ticket.id, ticket.intent, ticket.confidence, ticket.sentiment,
                ticket.urgency, ticket.response, ticket.status, ticket.processed_at,
                ticket.escalation_required, ticket.escalation_reason, ticket.escalated_at
                )
            
            self.logger.info(f"Updated ticket {ticket.id} in database")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating ticket {ticket.id}: {str(e)}")
            return False
    
    async def get_customer_tickets(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get tickets for a specific customer.
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of tickets to return
            
        Returns:
            List of ticket dictionaries
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM tickets 
                    WHERE customer_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2
                """, customer_id, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting tickets for customer {customer_id}: {str(e)}")
            return []
    
    async def get_tickets_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get tickets by status.
        
        Args:
            status: Ticket status
            limit: Maximum number of tickets to return
            
        Returns:
            List of ticket dictionaries
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM tickets 
                    WHERE status = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2
                """, status, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting tickets with status {status}: {str(e)}")
            return []
    
    async def get_escalated_tickets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get escalated tickets.
        
        Args:
            limit: Maximum number of tickets to return
            
        Returns:
            List of escalated ticket dictionaries
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM tickets 
                    WHERE escalation_required = true 
                    ORDER BY escalated_at DESC 
                    LIMIT $1
                """, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting escalated tickets: {str(e)}")
            return []
    
    async def save_customer(self, customer) -> bool:
        """
        Save a customer to the database.
        
        Args:
            customer: Customer object to save
            
        Returns:
            True if successful
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO customers (
                        id, name, email, phone, company, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone,
                        company = EXCLUDED.company,
                        updated_at = EXCLUDED.updated_at
                """, 
                customer.id, customer.name, customer.email, customer.phone,
                customer.company, customer.created_at, customer.updated_at
                )
            
            self.logger.info(f"Saved customer {customer.id} to database")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving customer {customer.id}: {str(e)}")
            return False
    
    async def get_customer(self, customer_id: str):
        """
        Get a customer by ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer object or None if not found
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM customers WHERE id = $1
                """, customer_id)
                
                if row:
                    from ..models.customer import Customer
                    return Customer.from_dict(dict(row))
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting customer {customer_id}: {str(e)}")
            return None
    
    async def save_order(self, order) -> bool:
        """
        Save an order to the database.
        
        Args:
            order: Order object to save
            
        Returns:
            True if successful
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO orders (
                        id, customer_id, order_number, status, amount, 
                        created_at, updated_at, order_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        amount = EXCLUDED.amount,
                        updated_at = EXCLUDED.updated_at,
                        order_data = EXCLUDED.order_data
                """, 
                order.id, order.customer_id, order.order_number, order.status,
                order.amount, order.created_at, order.updated_at, json.dumps(order.order_data)
                )
            
            self.logger.info(f"Saved order {order.id} to database")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving order {order.id}: {str(e)}")
            return False
    
    async def get_order(self, order_id: str):
        """
        Get an order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None if not found
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM orders WHERE id = $1
                """, order_id)
                
                if row:
                    from ..models.order import Order
                    order_dict = dict(row)
                    if order_dict.get('order_data'):
                        order_dict['order_data'] = json.loads(order_dict['order_data'])
                    return Order.from_dict(order_dict)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting order {order_id}: {str(e)}")
            return None
    
    async def get_orders_by_customer(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get orders for a specific customer.
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of orders to return
            
        Returns:
            List of order dictionaries
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM orders 
                    WHERE customer_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2
                """, customer_id, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting orders for customer {customer_id}: {str(e)}")
            return []
    
    async def create_tables(self) -> None:
        """
        Create database tables if they don't exist.
        """
        try:
            async with self.pool.acquire() as conn:
                # Create customers table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS customers (
                        id VARCHAR PRIMARY KEY,
                        name VARCHAR NOT NULL,
                        email VARCHAR,
                        phone VARCHAR,
                        company VARCHAR,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Create orders table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id VARCHAR PRIMARY KEY,
                        customer_id VARCHAR REFERENCES customers(id),
                        order_number VARCHAR UNIQUE,
                        status VARCHAR,
                        amount DECIMAL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        order_data JSONB
                    )
                """)
                
                # Create tickets table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS tickets (
                        id VARCHAR PRIMARY KEY,
                        customer_id VARCHAR REFERENCES customers(id),
                        message TEXT NOT NULL,
                        intent VARCHAR,
                        confidence DECIMAL,
                        sentiment VARCHAR,
                        urgency VARCHAR,
                        response TEXT,
                        status VARCHAR DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT NOW(),
                        processed_at TIMESTAMP,
                        escalation_required BOOLEAN DEFAULT FALSE,
                        escalation_reason TEXT,
                        escalated_at TIMESTAMP
                    )
                """)
                
                # Create indexes
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_customer_id ON tickets(customer_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_intent ON tickets(intent)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)")
                
                self.logger.info("Database tables created successfully")
                
        except Exception as e:
            self.logger.error(f"Error creating database tables: {str(e)}")
            raise
