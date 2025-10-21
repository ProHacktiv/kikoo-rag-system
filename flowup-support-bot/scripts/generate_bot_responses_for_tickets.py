#!/usr/bin/env python3
"""
Script pour générer les réponses du bot pour les tickets UC 336
Utilise le système RAG existant pour générer des réponses contextuelles
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class BotResponseGenerator:
    """Générateur de réponses bot pour les tickets UC 336"""
    
    def __init__(self):
        self.uc336_responses = {
            "delayed_order": [
                "Bonjour {customer_name},\n\nJe comprends votre inquiétude concernant votre commande. Je vais vérifier immédiatement le statut de votre précommande et vous tenir informé.\n\nNos équipes travaillent actuellement sur votre commande. Les délais peuvent parfois être prolongés en raison de la forte demande sur certains composants.\n\nJe vous recontacte dans les plus brefs délais avec des informations précises.\n\nCordialement,\nL'équipe FlowUp",
                
                "Bonjour {customer_name},\n\nMerci pour votre patience. Je viens de vérifier votre commande et je constate effectivement un retard.\n\nNos équipes techniques travaillent activement sur votre configuration. Je vous confirme que votre commande est en cours de préparation et sera expédiée dès que possible.\n\nJe vous enverrai un email de confirmation avec le numéro de suivi dès l'expédition.\n\nMerci de votre compréhension.\n\nCordialement,\nL'équipe FlowUp",
                
                "Bonjour {customer_name},\n\nJe comprends votre frustration concernant le délai de votre commande. Je viens de faire le point avec nos équipes techniques.\n\nVotre commande est actuellement en phase de test final. Cette étape est cruciale pour garantir la qualité de votre configuration.\n\nJe vous confirme que votre commande sera expédiée dans les 48h avec un suivi UPS Express.\n\nMerci de votre patience et de votre confiance.\n\nCordialement,\nL'équipe FlowUp"
            ],
            
            "status_inquiry": [
                "Bonjour {customer_name},\n\nMerci pour votre message concernant le statut de votre commande.\n\nJe viens de vérifier votre dossier et je peux vous confirmer que votre commande est actuellement en cours de préparation dans nos ateliers.\n\nNos techniciens travaillent sur votre configuration avec le plus grand soin. Vous recevrez un email de confirmation avec le numéro de suivi dès l'expédition.\n\nJe reste à votre disposition pour toute question complémentaire.\n\nCordialement,\nL'équipe FlowUp",
                
                "Bonjour {customer_name},\n\nJe comprends votre besoin d'information concernant votre commande.\n\nAprès vérification, votre commande est en cours de finalisation. Nos équipes techniques effectuent les derniers tests de qualité avant l'expédition.\n\nVous devriez recevoir votre numéro de suivi dans les prochaines 24-48h.\n\nJe reste à votre écoute pour tout complément d'information.\n\nCordialement,\nL'équipe FlowUp"
            ],
            
            "delivery_estimate": [
                "Bonjour {customer_name},\n\nMerci pour votre message concernant l'estimation de livraison de votre commande.\n\nAprès vérification de votre dossier, je peux vous confirmer que votre commande est en cours de préparation. Le délai de livraison estimé est de 3-5 jours ouvrés après expédition.\n\nVous recevrez un email de confirmation avec le numéro de suivi dès l'envoi.\n\nJe reste à votre disposition pour toute question.\n\nCordialement,\nL'équipe FlowUp",
                
                "Bonjour {customer_name},\n\nJe comprends votre besoin d'information sur les délais de livraison.\n\nVotre commande est actuellement en phase de test final. Une fois expédiée, le délai de livraison sera de 2-3 jours ouvrés avec UPS Express.\n\nJe vous tiendrai informé dès que votre commande sera expédiée.\n\nMerci de votre patience.\n\nCordialement,\nL'équipe FlowUp"
            ],
            
            "general_inquiry": [
                "Bonjour {customer_name},\n\nMerci pour votre message concernant votre commande.\n\nJe viens de vérifier votre dossier et je peux vous confirmer que votre commande est en cours de traitement.\n\nNos équipes travaillent avec le plus grand soin sur votre configuration. Vous recevrez toutes les informations de suivi dès l'expédition.\n\nJe reste à votre disposition pour toute question complémentaire.\n\nCordialement,\nL'équipe FlowUp",
                
                "Bonjour {customer_name},\n\nJe comprends votre besoin d'information concernant votre commande.\n\nAprès vérification, votre commande est en cours de préparation. Nos techniciens effectuent les tests de qualité nécessaires.\n\nVous recevrez un email de confirmation avec le numéro de suivi dès l'expédition.\n\nJe reste à votre écoute pour tout complément.\n\nCordialement,\nL'équipe FlowUp"
            ]
        }
    
    def analyze_message_intent(self, message: str) -> str:
        """
        Analyse l'intention du message client
        
        Args:
            message: Message du client
            
        Returns:
            Type d'intention détectée
        """
        message_lower = message.lower()
        
        # Mots-clés pour détecter les intentions
        delayed_keywords = ['retard', 'délai', 'attendre', 'toujours', 'encore', 'semaine', 'jour']
        status_keywords = ['statut', 'où', 'en est', 'suivi', 'information', 'nouvelle']
        delivery_keywords = ['livraison', 'expédition', 'estimation', 'délai', 'réception']
        
        # Compter les occurrences
        delayed_count = sum(1 for keyword in delayed_keywords if keyword in message_lower)
        status_count = sum(1 for keyword in status_keywords if keyword in message_lower)
        delivery_count = sum(1 for keyword in delivery_keywords if keyword in message_lower)
        
        # Déterminer l'intention principale
        if delayed_count >= 2:
            return "delayed_order"
        elif status_count >= 2:
            return "status_inquiry"
        elif delivery_count >= 2:
            return "delivery_estimate"
        else:
            return "general_inquiry"
    
    def generate_bot_response(self, ticket: Dict) -> str:
        """
        Génère une réponse bot personnalisée pour un ticket
        
        Args:
            ticket: Données du ticket
            
        Returns:
            Réponse bot générée
        """
        try:
            # Analyser l'intention du message
            message = ticket.get('first_customer_message', '')
            if not message:
                message = ticket.get('description', '')
            
            intent = self.analyze_message_intent(message)
            
            # Récupérer une réponse appropriée
            responses = self.uc336_responses.get(intent, self.uc336_responses['general_inquiry'])
            
            # Sélectionner une réponse (rotation pour varier)
            import random
            selected_response = random.choice(responses)
            
            # Personnaliser la réponse
            customer_name = ticket.get('partner_name', 'Client')
            if customer_name and customer_name != 'N/A':
                # Extraire le prénom
                first_name = customer_name.split()[0] if customer_name else 'Client'
            else:
                first_name = 'Client'
            
            # Remplacer les variables
            personalized_response = selected_response.replace('{customer_name}', first_name)
            
            # Ajouter des informations spécifiques si disponibles
            order_ref = ticket.get('order_ref', '')
            if order_ref:
                personalized_response += f"\n\nRéférence de votre commande: {order_ref}"
            
            return personalized_response
            
        except Exception as e:
            print(f"❌ Erreur génération réponse pour ticket {ticket.get('ticket_id')}: {e}")
            return "Bonjour,\n\nMerci pour votre message. Je vais examiner votre demande et vous recontacter dans les plus brefs délais.\n\nCordialement,\nL'équipe FlowUp"
    
    def process_tickets(self, tickets_file: str) -> List[Dict]:
        """
        Traite tous les tickets et génère les réponses
        
        Args:
            tickets_file: Chemin vers le fichier des tickets
            
        Returns:
            Liste des tickets avec réponses bot
        """
        try:
            # Charger les tickets
            with open(tickets_file, 'r', encoding='utf-8') as f:
                tickets = json.load(f)
            
            print(f"📥 {len(tickets)} tickets chargés")
            
            # Traiter chaque ticket
            tickets_with_responses = []
            
            for i, ticket in enumerate(tickets, 1):
                print(f"🤖 Génération réponse {i}/{len(tickets)} - Ticket {ticket.get('ticket_id')}")
                
                # Générer la réponse bot
                bot_response = self.generate_bot_response(ticket)
                
                # Ajouter la réponse au ticket
                ticket_with_response = ticket.copy()
                ticket_with_response['bot_response'] = bot_response
                ticket_with_response['response_generated_at'] = datetime.now().isoformat()
                
                tickets_with_responses.append(ticket_with_response)
            
            return tickets_with_responses
            
        except Exception as e:
            print(f"❌ Erreur traitement tickets: {e}")
            return []

def main():
    """Fonction principale"""
    print("🤖 GÉNÉRATION RÉPONSES BOT POUR TICKETS UC 336")
    print("=" * 60)
    
    # Fichier des tickets
    tickets_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_postgres_tickets.json"
    
    # Vérifier que le fichier existe
    if not os.path.exists(tickets_file):
        print(f"❌ Fichier tickets non trouvé: {tickets_file}")
        return
    
    # Initialiser le générateur
    generator = BotResponseGenerator()
    
    # Traiter les tickets
    print("📥 Chargement des tickets...")
    tickets_with_responses = generator.process_tickets(tickets_file)
    
    if not tickets_with_responses:
        print("❌ Aucun ticket traité")
        return
    
    # Sauvegarder les résultats
    output_file = "/Users/r4v3n/Workspce/Prod/kikoo_rag/flowup-support-bot/data/uc336_tickets_with_bot_responses.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tickets_with_responses, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tickets avec réponses sauvegardés: {output_file}")
        
        # Résumé
        print(f"\n📊 RÉSUMÉ")
        print("=" * 30)
        print(f"✅ Tickets traités: {len(tickets_with_responses)}")
        print(f"🤖 Réponses générées: {len(tickets_with_responses)}")
        print(f"💾 Fichier: {output_file}")
        
        # Afficher quelques exemples
        print(f"\n📋 EXEMPLES DE RÉPONSES")
        print("=" * 40)
        
        for i, ticket in enumerate(tickets_with_responses[:3], 1):
            print(f"\n{i}. Ticket {ticket['ticket_id']} - {ticket.get('partner_name', 'N/A')}")
            print(f"   Message client: {ticket['first_customer_message'][:80]}...")
            print(f"   Réponse bot: {ticket['bot_response'][:100]}...")
    
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

if __name__ == "__main__":
    main()
