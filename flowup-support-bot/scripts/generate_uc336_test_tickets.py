#!/usr/bin/env python3
"""
Génération de tickets UC 336 de test avec réponses bot
Simule 10 tickets UC 336 créés entre janvier 2024 et septembre 2025
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict
import random

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class UC336TicketGenerator:
    """Générateur de tickets UC 336 de test"""
    
    def __init__(self):
        self.uc336_messages = [
            "Bonjour, j'ai passé une commande il y a 2 semaines et je n'ai toujours pas de nouvelles. Pouvez-vous me dire où en est ma précommande ?",
            "Salut, j'ai commandé une RTX 4090 en précommande il y a un mois. Avez-vous des informations sur la disponibilité ?",
            "Bonjour, je voudrais savoir le statut de ma précommande pour la RTX 4080. Quand sera-t-elle disponible ?",
            "Hello, j'ai réservé une carte graphique en précommande mais je n'ai aucune nouvelle depuis 3 semaines. Pouvez-vous m'aider ?",
            "Bonjour, j'aimerais connaître l'avancement de ma précommande pour la RTX 4070. Y a-t-il des retards prévus ?",
            "Salut, j'ai commandé un GPU en précommande il y a longtemps et je n'ai pas de suivi. Pouvez-vous me renseigner ?",
            "Bonjour, je voudrais savoir où en est ma précommande pour la RTX 4060. Quand sera-t-elle prête ?",
            "Hello, j'ai réservé une carte graphique mais je n'ai aucune information sur la livraison. Pouvez-vous m'aider ?",
            "Bonjour, j'aimerais connaître le statut de ma précommande. Y a-t-il des nouvelles sur la disponibilité ?",
            "Salut, j'ai commandé en précommande il y a un moment et je n'ai pas de nouvelles. Pouvez-vous me dire où ça en est ?"
        ]
        
        self.customer_names = [
            "Jean Dupont", "Marie Martin", "Pierre Durand", "Sophie Bernard", "Lucas Moreau",
            "Emma Petit", "Thomas Roux", "Léa Simon", "Antoine Laurent", "Camille Garcia"
        ]
        
        self.ticket_subjects = [
            "Statut précommande RTX 4090",
            "Suivi commande RTX 4080", 
            "Information précommande RTX 4070",
            "Statut livraison RTX 4060",
            "Suivi précommande GPU",
            "Information commande carte graphique",
            "Statut précommande RTX 4090",
            "Suivi livraison RTX 4080",
            "Information précommande RTX 4070",
            "Statut commande RTX 4060"
        ]
    
    def generate_tickets(self, count: int = 10) -> List[Dict]:
        """
        Génère des tickets UC 336 de test
        
        Args:
            count: Nombre de tickets à générer
            
        Returns:
            Liste des tickets générés
        """
        tickets = []
        
        for i in range(count):
            # Générer une date aléatoire entre janvier 2024 et septembre 2025
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2025, 9, 30)
            random_days = random.randint(0, (end_date - start_date).days)
            ticket_date = start_date + timedelta(days=random_days)
            
            # Générer les données du ticket
            ticket = {
                'ticket_id': 1000 + i,
                'ticket_name': f'TICKET-UC336-{1000 + i}',
                'subject': self.ticket_subjects[i % len(self.ticket_subjects)],
                'description': f'Demande de suivi pour précommande - {self.customer_names[i % len(self.customer_names)]}',
                'create_date': ticket_date.strftime('%Y-%m-%d %H:%M:%S'),
                'partner_id': [i + 1, self.customer_names[i % len(self.customer_names)]],
                'priority': random.choice(['0', '1', '2']),  # 0=Normal, 1=Important, 2=Urgent
                'uc_number': 'UC_336',
                'first_customer_message': self.uc336_messages[i % len(self.uc336_messages)],
                'customer_name': self.customer_names[i % len(self.customer_names)],
                'customer_email': f'client{i+1}@example.com'
            }
            
            tickets.append(ticket)
        
        return tickets
    
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
            if ticket.get('uc_number') != 'UC_336':
                print(f"⚠️ Ticket {ticket.get('ticket_id')} n'est pas UC 336")
                continue
            
            # Vérifier la date
            create_date = ticket.get('create_date', '')
            if create_date:
                try:
                    ticket_date = datetime.strptime(create_date.split(' ')[0], '%Y-%m-%d')
                    if ticket_date < datetime(2024, 1, 1) or ticket_date > datetime(2025, 9, 30):
                        print(f"⚠️ Ticket {ticket.get('ticket_id')} hors période: {create_date}")
                        continue
                except:
                    print(f"⚠️ Date invalide pour ticket {ticket.get('ticket_id')}: {create_date}")
                    continue
            
            validated_tickets.append(ticket)
        
        print(f"✅ {len(validated_tickets)}/{len(tickets)} tickets validés")
        return validated_tickets

def main():
    """Fonction principale"""
    print("🎫 GÉNÉRATION TICKETS UC 336 DE TEST")
    print("=" * 50)
    
    # Initialiser le générateur
    generator = UC336TicketGenerator()
    
    # Générer les tickets
    print("📝 Génération de 10 tickets UC 336...")
    tickets = generator.generate_tickets(10)
    
    # Valider les tickets
    print("✅ Validation des tickets...")
    validated_tickets = generator.validate_tickets(tickets)
    
    if not validated_tickets:
        print("❌ Aucun ticket valide généré")
        return
    
    # Sauvegarder les résultats
    output_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_tickets_generated.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(validated_tickets, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tickets sauvegardés: {output_file}")
        
        # Résumé
        print(f"\n📊 RÉSUMÉ")
        print("=" * 30)
        print(f"✅ Tickets générés: {len(validated_tickets)}")
        print(f"📅 Période: Janvier 2024 - Septembre 2025")
        print(f"🏷️ UC: 336 (Statut précommande)")
        print(f"💾 Fichier: {output_file}")
        
        # Afficher les détails
        for i, ticket in enumerate(validated_tickets, 1):
            print(f"\n{i}. Ticket {ticket['ticket_id']}")
            print(f"   Sujet: {ticket['subject']}")
            print(f"   Date: {ticket['create_date']}")
            print(f"   Client: {ticket['customer_name']}")
            print(f"   Message: {ticket['first_customer_message'][:100]}...")
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

if __name__ == "__main__":
    main()
