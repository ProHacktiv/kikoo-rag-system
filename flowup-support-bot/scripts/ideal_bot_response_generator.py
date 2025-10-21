#!/usr/bin/env python3
"""
Générateur de réponses bot idéales avec format professionnel et détaillé
Basé sur la structure de réponse idéale fournie
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class IdealBotResponseGenerator:
    """Générateur de réponses bot idéales avec format professionnel"""
    
    def __init__(self):
        self.escalation_threshold = 12  # Jours légaux
        
    def calculate_days_since_order(self, create_date: str) -> int:
        """Calcule le nombre de jours depuis la commande"""
        try:
            if not create_date:
                return 0
            
            if isinstance(create_date, str):
                if 'T' in create_date:
                    ticket_date = datetime.fromisoformat(create_date.replace('Z', '+00:00'))
                else:
                    ticket_date = datetime.strptime(create_date.split(' ')[0], '%Y-%m-%d')
            else:
                ticket_date = create_date
            
            today = datetime.now()
            delta = today - ticket_date
            return delta.days
            
        except Exception as e:
            print(f"❌ Erreur calcul délai: {e}")
            return 0
    
    def determine_order_status(self, days_since_order: int, ticket_data: Dict) -> Dict:
        """Détermine le statut de la commande basé sur les délais"""
        
        if days_since_order > self.escalation_threshold:
            return {
                'status': 'RETARD_CRITIQUE',
                'status_text': 'RETARD CRITIQUE - Escalade immédiate',
                'description': 'Délai légal dépassé',
                'escalation_needed': True,
                'urgency': 'CRITICAL'
            }
        elif days_since_order > 8:
            return {
                'status': 'RETARD_IMPORTANT',
                'status_text': 'RETARD IMPORTANT',
                'description': 'Retard significatif détecté',
                'escalation_needed': True,
                'urgency': 'HIGH'
            }
        elif days_since_order > 5:
            return {
                'status': 'EN_COURS_RETARD',
                'status_text': 'EN COURS - Retard mineur',
                'description': 'Production en cours avec léger retard',
                'escalation_needed': False,
                'urgency': 'MEDIUM'
            }
        else:
            return {
                'status': 'EN_COURS_NORMAL',
                'status_text': 'EN COURS - Production',
                'description': 'Production en cours normalement',
                'escalation_needed': False,
                'urgency': 'NORMAL'
            }
    
    def generate_ideal_response(self, ticket: Dict) -> str:
        """Génère une réponse idéale avec format professionnel"""
        
        try:
            # Calculs de base
            create_date = ticket.get('create_date', '')
            days_since_order = self.calculate_days_since_order(create_date)
            
            # Données client
            customer_name = ticket.get('partner_name', 'Client')
            first_name = customer_name.split()[0] if customer_name and customer_name != 'N/A' else 'Client'
            order_ref = ticket.get('order_ref', '')
            
            # Déterminer le statut
            order_status = self.determine_order_status(days_since_order, ticket)
            
            # Format de la date
            if create_date:
                try:
                    if isinstance(create_date, str):
                        if 'T' in create_date:
                            order_date = datetime.fromisoformat(create_date.replace('Z', '+00:00'))
                        else:
                            order_date = datetime.strptime(create_date.split(' ')[0], '%Y-%m-%d')
                    else:
                        order_date = create_date
                    
                    formatted_date = order_date.strftime('%d/%m')
                except:
                    formatted_date = create_date.split(' ')[0] if create_date else 'N/A'
            else:
                formatted_date = 'N/A'
            
            # Générer la réponse selon le statut
            if order_status['status'] == 'RETARD_CRITIQUE':
                return self._generate_critical_delay_response(first_name, formatted_date, days_since_order, order_ref, order_status)
            elif order_status['status'] == 'RETARD_IMPORTANT':
                return self._generate_important_delay_response(first_name, formatted_date, days_since_order, order_ref, order_status)
            elif order_status['status'] == 'EN_COURS_RETARD':
                return self._generate_minor_delay_response(first_name, formatted_date, days_since_order, order_ref, order_status)
            else:
                return self._generate_normal_response(first_name, formatted_date, days_since_order, order_ref, order_status)
                
        except Exception as e:
            print(f"❌ Erreur génération réponse idéale pour ticket {ticket.get('ticket_id')}: {e}")
            return self._generate_fallback_response(first_name)
    
    def _generate_critical_delay_response(self, first_name: str, order_date: str, days_since_order: int, order_ref: str, order_status: Dict) -> str:
        """Génère une réponse pour retard critique"""
        return f"""Bonjour {first_name}, je suis l'assistant automatique FlowUp.

Je vérifie immédiatement votre commande du {order_date}.

[Check Odoo automatique]

🚨 **ALERTE CRITIQUE DÉTECTÉE**

Votre commande dépasse le délai légal de {self.escalation_threshold} jours :

📊 **État actuel de votre commande :**
- Date de commande : {order_date}
- Jours écoulés : {days_since_order} jours
- Statut : {order_status['status_text']}
- Délai légal : {self.escalation_threshold} jours (dépassé de {days_since_order - self.escalation_threshold} jours)

🚨 **Actions immédiates en cours :**
- Escalade vers l'équipe
- Vérification urgente de la production
- Un membre de l'équipe vous contactera dans les 24h
- Proposition de compensation

⏱️ **Prochaines étapes :**
- Un membre de l'équipe vous contactera dans les 24h
- Vérification statut production
- Proposition de solution
- Suivi renforcé

Cette situation est inacceptable et nécessite une intervention immédiate.

Puis-je vous aider pour autre chose ?"""
    
    def _generate_important_delay_response(self, first_name: str, order_date: str, days_since_order: int, order_ref: str, order_status: Dict) -> str:
        """Génère une réponse pour retard important"""
        return f"""Bonjour {first_name}, je suis l'assistant automatique FlowUp.

Je vérifie immédiatement votre commande du {order_date}.

[Check Odoo automatique]

⚠️ **RETARD IMPORTANT DÉTECTÉ**

Votre commande présente un retard significatif :

📊 **État actuel de votre commande :**
- Date de commande : {order_date}
- Jours écoulés : {days_since_order} jours
- Statut : {order_status['status_text']}
- Délai légal : {self.escalation_threshold} jours (reste {self.escalation_threshold - days_since_order} jours)

🔧 **Que signifie ce retard ?**
Votre commande est en cours de production mais avec un délai plus long que prévu :
- Vérification des composants
- Tests de qualité renforcés
- Contrôles supplémentaires

⏱️ **Actions en cours :**
- Surveillance renforcée
- Contact avec la production
- Mise à jour dans les 24h

Je vous tiens informé de l'avancement.

Puis-je vous aider pour autre chose ?"""
    
    def _generate_minor_delay_response(self, first_name: str, order_date: str, days_since_order: int, order_ref: str, order_status: Dict) -> str:
        """Génère une réponse pour retard mineur"""
        return f"""Bonjour {first_name}, je suis l'assistant automatique FlowUp.

Je vérifie immédiatement votre commande du {order_date}.

[Check Odoo automatique]

📋 **SUIVI RENFORCÉ**

Votre commande est en cours avec un léger retard :

📊 **État actuel de votre commande :**
- Date de commande : {order_date}
- Jours écoulés : {days_since_order} jours
- Statut : {order_status['status_text']}
- Délai légal : {self.escalation_threshold} jours (reste {self.escalation_threshold - days_since_order} jours)

🔧 **Que signifie "EN COURS" ?**
Votre PC est actuellement en phase de production dans nos ateliers :
- Assemblage des composants
- Câblage et configuration
- Tests initiaux

⏱️ **Prochaines étapes :**
- Test qualité (24-48h)
- Préparation expédition
- Livraison estimée : dans les 3-5 jours

Le statut sera mis à jour automatiquement à chaque étape.

Puis-je vous aider pour autre chose ?"""
    
    def _generate_normal_response(self, first_name: str, order_date: str, days_since_order: int, order_ref: str, order_status: Dict) -> str:
        """Génère une réponse normale"""
        return f"""Bonjour {first_name}, je suis l'assistant automatique FlowUp.

Je vérifie immédiatement votre commande du {order_date}.

[Check Odoo automatique]

✅ **COMMANDE EN COURS**

Votre commande se déroule normalement :

📊 **État actuel de votre commande :**
- Date de commande : {order_date}
- Jours écoulés : {days_since_order} jours
- Statut : {order_status['status_text']}
- Délai légal : {self.escalation_threshold} jours (reste {self.escalation_threshold - days_since_order} jours)

🔧 **Que signifie "EN COURS" ?**
Votre PC est actuellement en phase de production dans nos ateliers. Cette étape comprend :
- Assemblage des composants
- Câblage et configuration
- Tests initiaux

⏱️ **Prochaines étapes :**
- Test qualité (24-48h)
- Préparation expédition
- Livraison estimée : dans les 3-5 jours

Tout se déroule normalement. Le statut sera mis à jour automatiquement à chaque étape.

Puis-je vous aider pour autre chose ?"""
    
    def _generate_fallback_response(self, first_name: str) -> str:
        """Génère une réponse de fallback"""
        return f"""Bonjour {first_name}, je suis l'assistant automatique FlowUp.

Je vais examiner votre demande et vous recontacter dans les plus brefs délais.

Cordialement,
L'équipe FlowUp Support"""
    
    def process_tickets_with_ideal_responses(self, tickets_file: str) -> List[Dict]:
        """Traite tous les tickets avec des réponses idéales"""
        try:
            with open(tickets_file, 'r', encoding='utf-8') as f:
                tickets = json.load(f)
            
            print(f"📥 {len(tickets)} tickets chargés")
            
            tickets_with_ideal_responses = []
            
            for i, ticket in enumerate(tickets, 1):
                print(f"🤖 Génération réponse idéale {i}/{len(tickets)} - Ticket {ticket.get('ticket_id')}")
                
                # Générer la réponse idéale
                ideal_response = self.generate_ideal_response(ticket)
                
                # Ajouter la réponse au ticket
                ticket_with_ideal = ticket.copy()
                ticket_with_ideal['bot_response_ideal'] = ideal_response
                ticket_with_ideal['response_generated_at'] = datetime.now().isoformat()
                
                tickets_with_ideal_responses.append(ticket_with_ideal)
            
            return tickets_with_ideal_responses
            
        except Exception as e:
            print(f"❌ Erreur traitement tickets: {e}")
            return []

def main():
    """Fonction principale"""
    print("🤖 GÉNÉRATION RÉPONSES BOT IDÉALES")
    print("=" * 60)
    
    # Fichier des tickets
    tickets_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_postgres_tickets.json"
    
    if not os.path.exists(tickets_file):
        print(f"❌ Fichier tickets non trouvé: {tickets_file}")
        return
    
    # Initialiser le générateur
    generator = IdealBotResponseGenerator()
    
    # Traiter les tickets
    print("📥 Chargement des tickets...")
    tickets_with_ideal_responses = generator.process_tickets_with_ideal_responses(tickets_file)
    
    if not tickets_with_ideal_responses:
        print("❌ Aucun ticket traité")
        return
    
    # Sauvegarder les résultats
    output_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_tickets_ideal_responses.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tickets_with_ideal_responses, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tickets avec réponses idéales sauvegardés: {output_file}")
        
        # Résumé
        print(f"\n📊 RÉSUMÉ")
        print("=" * 30)
        print(f"✅ Tickets traités: {len(tickets_with_ideal_responses)}")
        print(f"🤖 Réponses idéales générées: {len(tickets_with_ideal_responses)}")
        print(f"💾 Fichier: {output_file}")
        
        # Afficher quelques exemples
        print(f"\n📋 EXEMPLES DE RÉPONSES IDÉALES")
        print("=" * 50)
        
        for i, ticket in enumerate(tickets_with_ideal_responses[:2], 1):
            print(f"\n{i}. Ticket {ticket['ticket_id']} - {ticket.get('partner_name', 'N/A')}")
            print(f"   Message client: {ticket['first_customer_message'][:60]}...")
            print(f"   Réponse idéale: {ticket['bot_response_ideal'][:100]}...")
    
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

if __name__ == "__main__":
    main()
