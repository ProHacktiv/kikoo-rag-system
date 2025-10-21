#!/usr/bin/env python3
"""
Générateur de réponses bot amélioré avec présentation, calcul de délais et escalade
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class EnhancedBotResponseGenerator:
    """Générateur de réponses bot amélioré avec logique complète"""
    
    def __init__(self):
        self.bot_presentation = """🤖 **Assistant FlowUp Support**

Bonjour ! Je suis l'assistant IA de FlowUp, spécialisé dans le suivi des commandes et le support client.

Je vais analyser votre demande et vérifier immédiatement le statut de votre commande dans notre système."""
        
        self.escalation_threshold = 12  # Jours légaux
        
    def calculate_days_since_order(self, create_date: str) -> int:
        """
        Calcule le nombre de jours depuis la commande
        
        Args:
            create_date: Date de création du ticket
            
        Returns:
            Nombre de jours écoulés
        """
        try:
            if not create_date:
                return 0
            
            # Parser la date
            if isinstance(create_date, str):
                if 'T' in create_date:
                    # Format ISO avec heure
                    ticket_date = datetime.fromisoformat(create_date.replace('Z', '+00:00'))
                else:
                    # Format simple
                    ticket_date = datetime.strptime(create_date.split(' ')[0], '%Y-%m-%d')
            else:
                ticket_date = create_date
            
            # Calculer la différence
            today = datetime.now()
            delta = today - ticket_date
            
            return delta.days
            
        except Exception as e:
            print(f"❌ Erreur calcul délai: {e}")
            return 0
    
    def determine_escalation_status(self, days_since_order: int, ticket_data: Dict) -> Dict:
        """
        Détermine le statut d'escalade basé sur les délais et données
        
        Args:
            days_since_order: Nombre de jours depuis la commande
            ticket_data: Données du ticket
            
        Returns:
            Dict avec statut d'escalade
        """
        escalation_info = {
            'needs_immediate_escalation': False,
            'escalation_reason': '',
            'urgency_level': 'NORMAL',
            'legal_delay_exceeded': False,
            'escalation_actions': []
        }
        
        # Vérifier le délai légal (12 jours)
        if days_since_order > self.escalation_threshold:
            escalation_info['needs_immediate_escalation'] = True
            escalation_info['legal_delay_exceeded'] = True
            escalation_info['urgency_level'] = 'CRITICAL'
            escalation_info['escalation_reason'] = f"Délai légal dépassé ({days_since_order} jours > {self.escalation_threshold} jours)"
            escalation_info['escalation_actions'] = [
                "Escalade immédiate vers le manager",
                "Contact client dans les 2h",
                "Vérification stock et production",
                "Proposition de compensation"
            ]
        elif days_since_order > 8:
            escalation_info['urgency_level'] = 'HIGH'
            escalation_info['escalation_reason'] = f"Retard important ({days_since_order} jours)"
            escalation_info['escalation_actions'] = [
                "Surveillance renforcée",
                "Contact client préventif",
                "Vérification statut production"
            ]
        elif days_since_order > 5:
            escalation_info['urgency_level'] = 'MEDIUM'
            escalation_info['escalation_reason'] = f"Retard modéré ({days_since_order} jours)"
            escalation_info['escalation_actions'] = [
                "Surveillance standard",
                "Mise à jour client"
            ]
        else:
            escalation_info['urgency_level'] = 'NORMAL'
            escalation_info['escalation_reason'] = "Dans les délais normaux"
            escalation_info['escalation_actions'] = [
                "Suivi standard"
            ]
        
        return escalation_info
    
    def generate_enhanced_bot_response(self, ticket: Dict) -> str:
        """
        Génère une réponse bot complète avec présentation, analyse et escalade
        
        Args:
            ticket: Données du ticket
            
        Returns:
            Réponse bot complète
        """
        try:
            # 2. Calcul des délais
            create_date = ticket.get('create_date', '')
            days_since_order = self.calculate_days_since_order(create_date)
            
            # 3. Analyse d'escalade
            escalation_info = self.determine_escalation_status(days_since_order, ticket)
            
            # 4. Récupération des données client
            customer_name = ticket.get('partner_name', 'Client')
            first_name = customer_name.split()[0] if customer_name and customer_name != 'N/A' else 'Client'
            order_ref = ticket.get('order_ref', '')
            tracking_ref = ticket.get('tracking_ref', '')
            
            # 5. Message personnalisé selon le statut
            if escalation_info['needs_immediate_escalation']:
                # ESCALADE IMMÉDIATE
                response_parts = [f"""🤖 **Assistant FlowUp Support**

Bonjour {first_name},

Je suis l'assistant IA de FlowUp, spécialisé dans le suivi des commandes. J'ai analysé votre dossier et je constate que votre commande dépasse le délai légal de {self.escalation_threshold} jours ({days_since_order} jours écoulés).

🚨 **ESCALADE IMMÉDIATE DÉTECTÉE**

**Actions immédiates en cours :**
- Escalade vers notre équipe
- Vérification urgente du statut de production
- Un membre de l'équipe vous contactera dans les 24h
- Proposition de compensation

**Informations de votre commande :**
- Référence : {order_ref if order_ref else 'En cours de vérification'}
- Délai écoulé : {days_since_order} jours
- Statut : Escalade en cours

Un membre de l'équipe vous contactera dans les 24h avec une solution concrète.

Mes excuses pour ce retard inacceptable.

**Équipe FlowUp Support**
"""]
            
            elif escalation_info['urgency_level'] == 'HIGH':
                # RETARD IMPORTANT
                response_parts = [f"""🤖 **Assistant FlowUp Support**

Bonjour {first_name},

Je suis l'assistant IA de FlowUp, spécialisé dans le suivi des commandes. J'ai analysé votre commande et je constate un retard de {days_since_order} jours.

⚠️ **RETARD IMPORTANT DÉTECTÉ**

**Actions en cours :**
- Surveillance renforcée de votre commande
- Contact avec l'équipe de production
- Mise à jour dans les 24h

**Informations de votre commande :**
- Référence : {order_ref if order_ref else 'En cours de vérification'}
- Délai écoulé : {days_since_order} jours
- Statut : Surveillance renforcée

Je vous tiens informé de l'avancement.

**Assistant FlowUp Support**
"""]
            
            elif escalation_info['urgency_level'] == 'MEDIUM':
                # RETARD MODÉRÉ
                response_parts = [f"""🤖 **Assistant FlowUp Support**

Bonjour {first_name},

Je suis l'assistant IA de FlowUp, spécialisé dans le suivi des commandes. Je viens de vérifier votre commande et nous avons un léger retard de {days_since_order} jours.

📋 **SUIVI RENFORCÉ**

**Actions en cours :**
- Vérification du statut de production
- Mise à jour dans les 48h

**Informations de votre commande :**
- Référence : {order_ref if order_ref else 'En cours de vérification'}
- Délai écoulé : {days_since_order} jours
- Statut : En cours de finalisation

Je vous recontacte dès que j'ai des nouvelles.

**Assistant FlowUp Support**
"""]
            
            else:
                # DANS LES DÉLAIS
                response_parts = [f"""🤖 **Assistant FlowUp Support**

Bonjour {first_name},

Je suis l'assistant IA de FlowUp, spécialisé dans le suivi des commandes. Je viens de vérifier votre commande et tout se déroule normalement.

✅ **COMMANDE EN COURS**

**Informations de votre commande :**
- Référence : {order_ref if order_ref else 'En cours de vérification'}
- Délai écoulé : {days_since_order} jours
- Statut : En cours de préparation

Votre commande est en cours de finalisation. Vous recevrez un email de confirmation avec le numéro de suivi dès l'expédition.

**Assistant FlowUp Support**
"""]
            
            # 6. Informations techniques
            if order_ref or tracking_ref:
                response_parts.append(f"""
📊 **DÉTAILS TECHNIQUES**
- Référence commande : {order_ref if order_ref else 'Non disponible'}
- Numéro de suivi : {tracking_ref if tracking_ref else 'Non disponible'}
- Délai écoulé : {days_since_order} jours
- Seuil légal : {self.escalation_threshold} jours
- Statut escalade : {'🚨 IMMÉDIATE' if escalation_info['needs_immediate_escalation'] else '✅ Normal'}
""")
            
            # 7. Actions d'escalade si nécessaire
            if escalation_info['escalation_actions']:
                response_parts.append(f"""
🔧 **ACTIONS AUTOMATIQUES**
{chr(10).join(f"- {action}" for action in escalation_info['escalation_actions'])}
""")
            
            return '\n'.join(response_parts)
            
        except Exception as e:
            print(f"❌ Erreur génération réponse pour ticket {ticket.get('ticket_id')}: {e}")
            return f"""🤖 **Assistant FlowUp Support**

Bonjour,

Merci pour votre message. Je vais examiner votre demande et vous recontacter dans les plus brefs délais.

Cordialement,
L'équipe FlowUp Support"""
    
    def process_tickets_with_enhanced_logic(self, tickets_file: str) -> List[Dict]:
        """
        Traite tous les tickets avec la logique améliorée
        
        Args:
            tickets_file: Chemin vers le fichier des tickets
            
        Returns:
            Liste des tickets avec réponses améliorées
        """
        try:
            # Charger les tickets
            with open(tickets_file, 'r', encoding='utf-8') as f:
                tickets = json.load(f)
            
            print(f"📥 {len(tickets)} tickets chargés")
            
            # Traiter chaque ticket
            tickets_with_enhanced_responses = []
            
            for i, ticket in enumerate(tickets, 1):
                print(f"🤖 Génération réponse améliorée {i}/{len(tickets)} - Ticket {ticket.get('ticket_id')}")
                
                # Calculer les délais
                create_date = ticket.get('create_date', '')
                days_since_order = self.calculate_days_since_order(create_date)
                
                # Analyser l'escalade
                escalation_info = self.determine_escalation_status(days_since_order, ticket)
                
                # Générer la réponse améliorée
                enhanced_response = self.generate_enhanced_bot_response(ticket)
                
                # Ajouter les informations d'escalade au ticket
                ticket_with_enhancement = ticket.copy()
                ticket_with_enhancement['bot_response_enhanced'] = enhanced_response
                ticket_with_enhancement['days_since_order'] = days_since_order
                ticket_with_enhancement['escalation_info'] = escalation_info
                ticket_with_enhancement['response_generated_at'] = datetime.now().isoformat()
                
                tickets_with_enhanced_responses.append(ticket_with_enhancement)
                
                # Afficher le statut d'escalade
                if escalation_info['needs_immediate_escalation']:
                    print(f"  🚨 ESCALADE IMMÉDIATE - {days_since_order} jours")
                elif escalation_info['urgency_level'] == 'HIGH':
                    print(f"  ⚠️ RETARD IMPORTANT - {days_since_order} jours")
                else:
                    print(f"  ✅ Statut normal - {days_since_order} jours")
            
            return tickets_with_enhanced_responses
            
        except Exception as e:
            print(f"❌ Erreur traitement tickets: {e}")
            return []

def main():
    """Fonction principale"""
    print("🤖 GÉNÉRATION RÉPONSES BOT AMÉLIORÉES")
    print("=" * 60)
    
    # Fichier des tickets
    tickets_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_postgres_tickets.json"
    
    # Vérifier que le fichier existe
    if not os.path.exists(tickets_file):
        print(f"❌ Fichier tickets non trouvé: {tickets_file}")
        return
    
    # Initialiser le générateur amélioré
    generator = EnhancedBotResponseGenerator()
    
    # Traiter les tickets
    print("📥 Chargement des tickets...")
    tickets_with_enhanced_responses = generator.process_tickets_with_enhanced_logic(tickets_file)
    
    if not tickets_with_enhanced_responses:
        print("❌ Aucun ticket traité")
        return
    
    # Sauvegarder les résultats
    output_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_tickets_enhanced_responses.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tickets_with_enhanced_responses, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tickets avec réponses améliorées sauvegardés: {output_file}")
        
        # Résumé
        print(f"\n📊 RÉSUMÉ")
        print("=" * 30)
        print(f"✅ Tickets traités: {len(tickets_with_enhanced_responses)}")
        
        # Statistiques d'escalade
        immediate_escalations = sum(1 for t in tickets_with_enhanced_responses if t['escalation_info']['needs_immediate_escalation'])
        high_urgency = sum(1 for t in tickets_with_enhanced_responses if t['escalation_info']['urgency_level'] == 'HIGH')
        
        print(f"🚨 Escalades immédiates: {immediate_escalations}")
        print(f"⚠️ Retards importants: {high_urgency}")
        print(f"✅ Dans les délais: {len(tickets_with_enhanced_responses) - immediate_escalations - high_urgency}")
        
        # Afficher les détails d'escalade
        print(f"\n🚨 DÉTAILS ESCALADES")
        print("=" * 40)
        
        for ticket in tickets_with_enhanced_responses:
            escalation = ticket['escalation_info']
            if escalation['needs_immediate_escalation']:
                print(f"🚨 Ticket {ticket['ticket_id']} - {ticket['days_since_order']} jours - ESCALADE IMMÉDIATE")
            elif escalation['urgency_level'] == 'HIGH':
                print(f"⚠️ Ticket {ticket['ticket_id']} - {ticket['days_since_order']} jours - Retard important")
    
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

if __name__ == "__main__":
    main()
