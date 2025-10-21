#!/usr/bin/env python3
"""
Script pour récupérer 10 tickets UC 336 réels depuis Odoo
Utilise les credentials du fichier odoo_config.json
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class RealOdooTicketFetcher:
    """Récupérateur de tickets Odoo réel avec authentification"""
    
    def __init__(self, config_path: str = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.session_id = None
        self.uid = None
        
    def _load_config(self) -> Dict:
        """Charge la configuration Odoo"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
            return {}
    
    def authenticate(self) -> bool:
        """Authentification Odoo avec session"""
        try:
            print(f"🔐 Connexion à {self.config['url']}")
            print(f"📊 Base: {self.config['db']}")
            print(f"👤 Utilisateur: {self.config['username']}")
            
            # URL d'authentification
            auth_url = f"{self.config['url']}/web/session/authenticate"
            
            auth_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.config['db'],
                    "login": self.config['username'],
                    "password": self.config['password']
                },
                "id": 1
            }
            
            # Headers pour l'authentification
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.post(
                auth_url,
                json=auth_data,
                headers=headers,
                timeout=15
            )
            
            print(f"📡 Statut: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📊 Réponse: {result}")
                
                if 'result' in result and result['result']:
                    self.uid = result['result'].get('uid')
                    self.session_id = result['result'].get('session_id')
                    print(f"✅ Authentification réussie!")
                    print(f"🆔 UID: {self.uid}")
                    print(f"🔑 Session: {self.session_id[:20]}...")
                    return True
                else:
                    print(f"❌ Authentification échouée: {result}")
                    return False
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                print(f"📄 Réponse: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Erreur authentification: {e}")
            return False
    
    def fetch_uc336_tickets(self, limit: int = 10) -> List[Dict]:
        """
        Récupère les tickets UC 336 réels
        
        Args:
            limit: Nombre de tickets à récupérer
            
        Returns:
            Liste des tickets UC 336
        """
        try:
            if not self.session_id or not self.uid:
                print("❌ Pas de session active")
                return []
            
            print(f"📥 Récupération de {limit} tickets UC 336...")
            
            # URL pour l'API Odoo
            api_url = f"{self.config['url']}/web/dataset/call_kw"
            
            # Filtres pour UC 336 et période
            domain = [
                ['x_uc_number', '=', 'UC_336'],  # UC 336
                ['create_date', '>=', '2024-01-01'],  # Depuis janvier 2024
                ['create_date', '<=', '2025-09-30']   # Jusqu'à septembre 2025
            ]
            
            # Champs à récupérer
            fields = [
                'id', 'name', 'subject', 'description', 'create_date',
                'partner_id', 'user_id', 'team_id', 'priority', 'stage_id',
                'x_uc_number', 'x_first_message', 'x_customer_message',
                'partner_name', 'partner_email'
            ]
            
            data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": "helpdesk.ticket",
                    "method": "search_read",
                    "args": [domain],
                    "kwargs": {
                        "fields": fields,
                        "limit": limit,
                        "order": "create_date desc"  # Plus récents en premier
                    }
                },
                "id": 1
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'session_id={self.session_id}',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.post(api_url, json=data, headers=headers, timeout=20)
            
            print(f"📡 Statut API: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📊 Résultat: {result}")
                
                if 'result' in result:
                    tickets = result['result']
                    print(f"✅ {len(tickets)} tickets UC 336 récupérés")
                    return tickets
                else:
                    print(f"❌ Erreur dans la réponse: {result}")
                    return []
            else:
                print(f"❌ Erreur API: {response.status_code}")
                print(f"📄 Réponse: {response.text[:300]}...")
                return []
                
        except Exception as e:
            print(f"❌ Erreur récupération tickets: {e}")
            return []
    
    def get_ticket_messages(self, ticket_id: int) -> List[Dict]:
        """
        Récupère les messages d'un ticket
        
        Args:
            ticket_id: ID du ticket
            
        Returns:
            Liste des messages du ticket
        """
        try:
            api_url = f"{self.config['url']}/web/dataset/call_kw"
            
            # Récupérer les messages du ticket
            domain = [['res_id', '=', ticket_id], ['model', '=', 'helpdesk.ticket']]
            
            data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": "mail.message",
                    "method": "search_read",
                    "args": [domain],
                    "kwargs": {
                        "fields": ['id', 'body', 'author_id', 'date', 'message_type', 'subtype_id'],
                        "order": "date asc"  # Chronologique
                    }
                },
                "id": 1
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'session_id={self.session_id}',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.post(api_url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                else:
                    return []
            else:
                return []
                
        except Exception as e:
            print(f"❌ Erreur récupération messages ticket {ticket_id}: {e}")
            return []
    
    def get_first_customer_message(self, ticket_id: int) -> Optional[str]:
        """
        Récupère le premier message du client
        
        Args:
            ticket_id: ID du ticket
            
        Returns:
            Premier message du client ou None
        """
        try:
            messages = self.get_ticket_messages(ticket_id)
            
            # Chercher le premier message du client (pas du système)
            for message in messages:
                if message.get('message_type') == 'comment':
                    body = message.get('body', '')
                    if body and len(body.strip()) > 10:
                        # Nettoyer le HTML basique
                        clean_body = body.replace('<p>', '').replace('</p>', '').replace('<br>', '\n').strip()
                        if clean_body and not clean_body.startswith('<!--'):
                            return clean_body
            
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
            uc_number = ticket.get('x_uc_number', '')
            if uc_number != 'UC_336':
                print(f"⚠️ Ticket {ticket.get('id')} n'est pas UC 336: {uc_number}")
                continue
            
            # Vérifier la date
            create_date = ticket.get('create_date', '')
            if create_date:
                try:
                    ticket_date = datetime.strptime(create_date.split(' ')[0], '%Y-%m-%d')
                    if ticket_date < datetime(2024, 1, 1) or ticket_date > datetime(2025, 9, 30):
                        print(f"⚠️ Ticket {ticket.get('id')} hors période: {create_date}")
                        continue
                except:
                    print(f"⚠️ Date invalide pour ticket {ticket.get('id')}: {create_date}")
                    continue
            
            validated_tickets.append(ticket)
        
        print(f"✅ {len(validated_tickets)}/{len(tickets)} tickets validés")
        return validated_tickets

def main():
    """Fonction principale"""
    print("🎫 RÉCUPÉRATION TICKETS UC 336 RÉELS")
    print("=" * 50)
    
    # Initialiser le récupérateur
    fetcher = RealOdooTicketFetcher()
    
    # Authentification
    print("🔐 Authentification Odoo...")
    if not fetcher.authenticate():
        print("❌ Échec authentification")
        return
    
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
        print(f"  {i}/10 - Ticket {ticket.get('id')}")
        
        first_message = fetcher.get_first_customer_message(ticket.get('id'))
        
        ticket_data = {
            'ticket_id': ticket.get('id'),
            'ticket_name': ticket.get('name'),
            'subject': ticket.get('subject'),
            'description': ticket.get('description'),
            'create_date': ticket.get('create_date'),
            'partner_id': ticket.get('partner_id'),
            'partner_name': ticket.get('partner_name'),
            'partner_email': ticket.get('partner_email'),
            'priority': ticket.get('priority'),
            'uc_number': ticket.get('x_uc_number'),
            'first_customer_message': first_message
        }
        
        tickets_with_messages.append(ticket_data)
    
    # Sauvegarder les résultats
    output_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_real_tickets.json"
    
    try:
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
            print(f"   Sujet: {ticket['subject']}")
            print(f"   Date: {ticket['create_date']}")
            print(f"   Client: {ticket.get('partner_name', 'N/A')}")
            print(f"   Message: {ticket['first_customer_message'][:100]}..." if ticket['first_customer_message'] else "   Message: Aucun")
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

if __name__ == "__main__":
    main()
