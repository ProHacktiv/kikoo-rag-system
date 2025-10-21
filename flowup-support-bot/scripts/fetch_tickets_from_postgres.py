#!/usr/bin/env python3
"""
Script pour récupérer 10 tickets UC 336 depuis PostgreSQL
Plus direct et fiable que l'API Odoo
"""

import sys
import os
import json
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class PostgreSQLTicketFetcher:
    """Récupérateur de tickets depuis PostgreSQL"""
    
    def __init__(self, db_config: Dict = None):
        self.db_config = db_config or self._get_default_config()
        self.connection = None
        
    def _get_default_config(self) -> Dict:
        """Configuration PostgreSQL FlowUp RAG"""
        return {
            "host": "localhost",
            "port": 5432,
            "database": "flowup_rag",
            "user": "flowup",
            "password": "dev123_change_in_prod"
        }
    
    def connect(self) -> bool:
        """Connexion à PostgreSQL"""
        try:
            print(f"🔗 Connexion à PostgreSQL...")
            print(f"📊 Host: {self.db_config['host']}:{self.db_config['port']}")
            print(f"🗄️ Database: {self.db_config['database']}")
            print(f"👤 User: {self.db_config['user']}")
            
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            
            print("✅ Connexion PostgreSQL réussie!")
            return True
            
        except Exception as e:
            print(f"❌ Erreur connexion PostgreSQL: {e}")
            return False
    
    def fetch_uc336_tickets(self, limit: int = 10) -> List[Dict]:
        """
        Récupère les tickets UC 336 depuis PostgreSQL
        
        Args:
            limit: Nombre de tickets à récupérer
            
        Returns:
            Liste des tickets UC 336
        """
        try:
            if not self.connection:
                print("❌ Pas de connexion à la base")
                return []
            
            print(f"📥 Récupération de {limit} tickets UC 336...")
            
            # Requête SQL pour récupérer les tickets UC 336
            query = """
            SELECT 
                ticket_id,
                odoo_id,
                name,
                description,
                create_date,
                close_date,
                write_date,
                category_l1_id,
                category_l1,
                category_l2_id,
                category_l2,
                category_l3_id,
                category_l3,
                priority,
                stage,
                team,
                assigned_to,
                partner_name,
                partner_email,
                order_ref,
                tracking_ref,
                ai_problem_resume,
                ai_solution_apporte,
                ai_emotions_detectees,
                ai_urgency_indicators,
                ai_impact,
                ai_real_priority,
                ai_categorie,
                ai_order_number,
                data,
                imported_at,
                updated_at
            FROM tickets 
            WHERE category_l3_id = 336
            AND create_date >= '2024-01-01'
            AND create_date <= '2025-09-30'
            ORDER BY create_date DESC
            LIMIT %s
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (limit,))
            
            # Récupérer les résultats
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            tickets = []
            for row in rows:
                ticket = dict(zip(columns, row))
                tickets.append(ticket)
            
            cursor.close()
            
            print(f"✅ {len(tickets)} tickets UC 336 récupérés")
            return tickets
            
        except Exception as e:
            print(f"❌ Erreur récupération tickets: {e}")
            return []
    
    def get_ticket_messages(self, ticket_id: int) -> List[Dict]:
        """
        Récupère les messages d'un ticket depuis PostgreSQL
        Note: Les messages sont stockés dans la colonne 'data' (JSONB)
        
        Args:
            ticket_id: ID du ticket
            
        Returns:
            Liste des messages du ticket
        """
        try:
            # Récupérer les données JSON du ticket
            query = """
            SELECT data
            FROM tickets 
            WHERE ticket_id = %s
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (ticket_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                data = result[0]
                # Extraire les messages du JSON
                messages = data.get('messages', [])
                cursor.close()
                return messages
            else:
                cursor.close()
                return []
            
        except Exception as e:
            print(f"❌ Erreur récupération messages ticket {ticket_id}: {e}")
            return []
    
    def get_first_customer_message(self, ticket_id: int) -> Optional[str]:
        """
        Récupère le premier message du client
        Utilise la colonne 'description' qui contient le message original
        
        Args:
            ticket_id: ID du ticket
            
        Returns:
            Premier message du client ou None
        """
        try:
            # Récupérer le message original du ticket
            query = """
            SELECT description
            FROM tickets 
            WHERE ticket_id = %s
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (ticket_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                description = result[0]
                if description and len(description.strip()) > 10:
                    # Nettoyer le HTML basique
                    clean_description = description.replace('<p>', '').replace('</p>', '').replace('<br>', '\n').strip()
                    if clean_description and not clean_description.startswith('<!--'):
                        return clean_description
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération premier message ticket {ticket_id}: {e}")
            return None
    
    def validate_tickets(self, tickets: List[Dict]) -> List[Dict]:
        """
        Valide que les tickets sont bien UC 336 et dans la période
        
        Args:
            tickets: Liste des tickets
            
        Returns:
            Tickets validés
        """
        validated_tickets = []
        
        for ticket in tickets:
            # Vérifier UC 336
            category_l3_id = ticket.get('category_l3_id')
            if category_l3_id != 336:
                print(f"⚠️ Ticket {ticket.get('ticket_id')} n'est pas UC 336: {category_l3_id}")
                continue
            
            # Vérifier la date
            create_date = ticket.get('create_date', '')
            if create_date:
                try:
                    if isinstance(create_date, str):
                        ticket_date = datetime.strptime(create_date.split(' ')[0], '%Y-%m-%d')
                    else:
                        ticket_date = create_date
                    
                    if ticket_date < datetime(2024, 1, 1) or ticket_date > datetime(2025, 9, 30):
                        print(f"⚠️ Ticket {ticket.get('ticket_id')} hors période: {create_date}")
                        continue
                except:
                    print(f"⚠️ Date invalide pour ticket {ticket.get('ticket_id')}: {create_date}")
                    continue
            
            validated_tickets.append(ticket)
        
        print(f"✅ {len(validated_tickets)}/{len(tickets)} tickets validés")
        return validated_tickets
    
    def close(self):
        """Ferme la connexion"""
        if self.connection:
            self.connection.close()
            print("🔌 Connexion PostgreSQL fermée")

def main():
    """Fonction principale"""
    print("🎫 RÉCUPÉRATION TICKETS UC 336 DEPUIS POSTGRESQL")
    print("=" * 60)
    
    # Configuration PostgreSQL FlowUp RAG
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "flowup_rag",
        "user": "flowup",
        "password": "dev123_change_in_prod"
    }
    
    # Initialiser le récupérateur
    fetcher = PostgreSQLTicketFetcher(db_config)
    
    # Connexion
    print("🔐 Connexion à PostgreSQL...")
    if not fetcher.connect():
        print("❌ Échec connexion")
        print("💡 Vérifiez les paramètres de connexion dans le script")
        return
    
    try:
        # Récupérer les tickets
        print("📥 Récupération des tickets UC 336...")
        tickets = fetcher.fetch_uc336_tickets(limit=10)
        
        if not tickets:
            print("❌ Aucun ticket UC 336 trouvé")
            return
        
        # Valider les tickets
        print("✅ Validation des tickets...")
        validated_tickets = fetcher.validate_tickets(tickets)
        
        if not validated_tickets:
            print("❌ Aucun ticket valide trouvé")
            return
        
        # Récupérer le premier message pour chaque ticket
        print("💬 Récupération des premiers messages...")
        tickets_with_messages = []
        
        for i, ticket in enumerate(validated_tickets[:10], 1):
            print(f"  {i}/10 - Ticket {ticket.get('ticket_id')}")
            
            first_message = fetcher.get_first_customer_message(ticket.get('ticket_id'))
            
            ticket_data = {
                'ticket_id': ticket.get('ticket_id'),
                'odoo_id': ticket.get('odoo_id'),
                'ticket_name': ticket.get('name'),
                'description': ticket.get('description'),
                'create_date': str(ticket.get('create_date')),
                'close_date': str(ticket.get('close_date')) if ticket.get('close_date') else None,
                'partner_name': ticket.get('partner_name'),
                'partner_email': ticket.get('partner_email'),
                'priority': ticket.get('priority'),
                'stage': ticket.get('stage'),
                'team': ticket.get('team'),
                'assigned_to': ticket.get('assigned_to'),
                'order_ref': ticket.get('order_ref'),
                'tracking_ref': ticket.get('tracking_ref'),
                'category_l1': ticket.get('category_l1'),
                'category_l2': ticket.get('category_l2'),
                'category_l3': ticket.get('category_l3'),
                'category_l3_id': ticket.get('category_l3_id'),
                'ai_problem_resume': ticket.get('ai_problem_resume'),
                'ai_solution_apporte': ticket.get('ai_solution_apporte'),
                'ai_emotions_detectees': ticket.get('ai_emotions_detectees'),
                'ai_urgency_indicators': ticket.get('ai_urgency_indicators'),
                'ai_impact': ticket.get('ai_impact'),
                'ai_real_priority': ticket.get('ai_real_priority'),
                'ai_categorie': ticket.get('ai_categorie'),
                'ai_order_number': ticket.get('ai_order_number'),
                'first_customer_message': first_message
            }
            
            tickets_with_messages.append(ticket_data)
        
        # Sauvegarder les résultats
        output_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_postgres_tickets.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tickets_with_messages, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tickets sauvegardés: {output_file}")
        
        # Résumé
        print(f"\n📊 RÉSUMÉ")
        print("=" * 30)
        print(f"✅ Tickets récupérés: {len(tickets_with_messages)}")
        print(f"📅 Période: Janvier 2024 - Septembre 2025")
        print(f"🏷️ UC: 336 (Statut précommande)")
        print(f"💾 Fichier: {output_file}")
        
        # Afficher les détails
        for i, ticket in enumerate(tickets_with_messages, 1):
            print(f"\n{i}. Ticket {ticket['ticket_id']}")
            print(f"   Nom: {ticket.get('ticket_name', 'N/A')}")
            print(f"   Date: {ticket['create_date']}")
            print(f"   Client: {ticket.get('partner_name', 'N/A')}")
            print(f"   Message: {ticket['first_customer_message'][:100]}..." if ticket['first_customer_message'] else "   Message: Aucun")
    
    finally:
        # Fermer la connexion
        fetcher.close()

if __name__ == "__main__":
    main()
