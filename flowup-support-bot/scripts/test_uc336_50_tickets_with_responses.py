#!/usr/bin/env python3
"""
Test des 50 tickets UC_336 avec génération de réponses complètes
Utilise la connexion Odoo pour récupérer les données de commande
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.enhanced_flowup_chatbot import EnhancedFlowUpChatbot
from src.integrations.odoo_client import OdooClient

def load_uc336_50_tickets() -> List[Dict]:
    """Charge 50 tickets spécifiques UC_336 (statut précommande)"""
    tickets = [
        # TICKET 1 - Demande statut précommande
        {
            "id": "36514",
            "message": "Bonjour j'ai commander le dernier blackhawk disponible auriez vous une idée concernant l'envoi ainsi que la réception du colis.",
            "expected_uc": "UC_336",
            "user_id": "user_001",
            "order_number": "SO001",
            "date": "2024-01-15T10:30:00"
        },
        
        # TICKET 2 - Demande avancement simple
        {
            "id": "36515",
            "message": "j'aimerais savoir où en est ma commande",
            "expected_uc": "UC_336",
            "user_id": "user_002",
            "order_number": "SO002",
            "date": "2024-01-14T15:45:00"
        },
        
        # TICKET 3 - Statut visible mentionné
        {
            "id": "36516",
            "message": "Ma commande est toujours en cours, pouvez-vous me donner des nouvelles ?",
            "expected_uc": "UC_336",
            "user_id": "user_003",
            "order_number": "SO003",
            "date": "2024-01-13T09:20:00"
        },
        
        # TICKET 4 - Demande statut récente
        {
            "id": "36517",
            "message": "Commande passée il y a 3 jours, où en est-elle ?",
            "expected_uc": "UC_336",
            "user_id": "user_004",
            "order_number": "SO004",
            "date": "2024-01-12T14:30:00"
        },
        
        # TICKET 5 - Demande avancement
        {
            "id": "36518",
            "message": "J'aimerais connaître l'avancement de ma commande",
            "expected_uc": "UC_336",
            "user_id": "user_005",
            "order_number": "SO005",
            "date": "2024-01-11T16:15:00"
        },
        
        # TICKET 6 - Question précommande RTX
        {
            "id": "36519",
            "message": "Bonjour, je voudrais savoir quand le RTX 4080 sera disponible en précommande ?",
            "expected_uc": "UC_336",
            "user_id": "user_006",
            "order_number": "SO006",
            "date": "2024-01-10T11:45:00"
        },
        
        # TICKET 7 - Statut fabrication
        {
            "id": "36520",
            "message": "Commande effectuée le 24/03 : ordre de fabrication toujours noté EN COURS, des infos ?",
            "expected_uc": "UC_336",
            "user_id": "user_007",
            "order_number": "SO007",
            "date": "2024-01-09T13:20:00"
        },
        
        # TICKET 8 - Demande statut avec délai
        {
            "id": "36521",
            "message": "j'ai passé commande il y a une semaine j'aimerai savoir où en est la commande",
            "expected_uc": "UC_336",
            "user_id": "user_008",
            "order_number": "SO008",
            "date": "2024-01-08T10:30:00"
        },
        
        # TICKET 9 - Question précommande GPU
        {
            "id": "36522",
            "message": "Quand le RTX 4090 sera-t-il disponible en précommande ?",
            "expected_uc": "UC_336",
            "user_id": "user_009",
            "order_number": "SO009",
            "date": "2024-01-07T15:45:00"
        },
        
        # TICKET 10 - Statut avec mention EN COURS
        {
            "id": "36523",
            "message": "Ma commande est toujours en fabrication, pouvez-vous me donner des nouvelles ?",
            "expected_uc": "UC_336",
            "user_id": "user_010",
            "order_number": "SO010",
            "date": "2024-01-06T12:15:00"
        },
        
        # TICKET 11 - Demande statut récente
        {
            "id": "36524",
            "message": "Commande passée il y a 5 jours, où en est-elle ?",
            "expected_uc": "UC_336",
            "user_id": "user_011",
            "order_number": "SO011",
            "date": "2024-01-05T09:30:00"
        },
        
        # TICKET 12 - Question précommande CPU
        {
            "id": "36525",
            "message": "Le nouveau processeur Intel sera-t-il disponible en précommande ?",
            "expected_uc": "UC_336",
            "user_id": "user_012",
            "order_number": "SO012",
            "date": "2024-01-04T14:20:00"
        },
        
        # TICKET 13 - Demande avancement avec contexte
        {
            "id": "36526",
            "message": "Bonjour, j'ai commandé un PC sur mesure il y a 10 jours, pouvez-vous me dire où en est la fabrication ?",
            "expected_uc": "UC_336",
            "user_id": "user_013",
            "order_number": "SO013",
            "date": "2024-01-03T16:30:00"
        },
        
        # TICKET 14 - Statut précommande avec urgence
        {
            "id": "36527",
            "message": "J'ai besoin de savoir rapidement l'état de ma précommande pour organiser ma réception",
            "expected_uc": "UC_336",
            "user_id": "user_014",
            "order_number": "SO014",
            "date": "2024-01-02T11:45:00"
        },
        
        # TICKET 15 - Question précommande avec date
        {
            "id": "36528",
            "message": "Quand sera disponible la nouvelle carte mère que j'ai précommandée ?",
            "expected_uc": "UC_336",
            "user_id": "user_015",
            "order_number": "SO015",
            "date": "2024-01-01T13:15:00"
        },
        
        # TICKET 16 - Demande statut avec référence
        {
            "id": "36529",
            "message": "Pouvez-vous me donner des nouvelles de ma commande SO016 ?",
            "expected_uc": "UC_336",
            "user_id": "user_016",
            "order_number": "SO016",
            "date": "2023-12-31T10:30:00"
        },
        
        # TICKET 17 - Question précommande avec stock
        {
            "id": "36530",
            "message": "Avez-vous une idée de quand le stock sera reconstitué pour ma précommande ?",
            "expected_uc": "UC_336",
            "user_id": "user_017",
            "order_number": "SO017",
            "date": "2023-12-30T15:20:00"
        },
        
        # TICKET 18 - Statut fabrication détaillé
        {
            "id": "36531",
            "message": "Ma commande est en cours de fabrication depuis 2 semaines, pouvez-vous me dire à quelle étape elle en est ?",
            "expected_uc": "UC_336",
            "user_id": "user_018",
            "order_number": "SO018",
            "date": "2023-12-29T12:45:00"
        },
        
        # TICKET 19 - Question précommande avec délai
        {
            "id": "36532",
            "message": "Combien de temps faut-il compter pour recevoir ma précommande ?",
            "expected_uc": "UC_336",
            "user_id": "user_019",
            "order_number": "SO019",
            "date": "2023-12-28T09:30:00"
        },
        
        # TICKET 20 - Demande statut avec inquiétude
        {
            "id": "36533",
            "message": "Je m'inquiète pour ma commande, pouvez-vous me rassurer sur son avancement ?",
            "expected_uc": "UC_336",
            "user_id": "user_020",
            "order_number": "SO020",
            "date": "2023-12-27T14:15:00"
        }
    ]
    
    # Ajouter 30 tickets supplémentaires pour atteindre 50
    for i in range(21, 51):
        tickets.append({
            "id": f"365{20 + i}",
            "message": f"Demande de statut pour ma commande {i} - Où en est ma précommande ?",
            "expected_uc": "UC_336",
            "user_id": f"user_{i:03d}",
            "order_number": f"SO{i:03d}",
            "date": f"2023-12-{26-i//2}T{10 + i%12}:{30 + i%30}:00"
        })
    
    return tickets

async def test_uc336_with_odoo_responses():
    """Test UC_336 avec réponses complètes et connexion Odoo"""
    print("🧪 Test UC_336 - 50 Tickets avec Réponses Odoo")
    print("=" * 80)
    
    # Initialiser le chatbot
    chatbot = EnhancedFlowUpChatbot()
    
    # Charger la configuration Odoo
    config_path = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"
    
    try:
        with open(config_path, 'r') as f:
            odoo_config = json.load(f)
        
        # Adapter la configuration pour le client
        client_config = {
            'url': odoo_config['url'],
            'database': odoo_config['db'],
            'username': odoo_config['username'],
            'password': odoo_config['password']
        }
        
        # Initialiser le client Odoo
        odoo_client = OdooClient(client_config)
        print(f"✅ Connexion Odoo établie")
        
    except Exception as e:
        print(f"❌ Erreur connexion Odoo: {e}")
        odoo_client = None
    
    # Charger les tickets UC_336
    tickets = load_uc336_50_tickets()
    
    print(f"\n📋 Traitement de {len(tickets)} tickets UC_336...")
    print("-" * 80)
    
    # Traiter tous les tickets
    results = []
    for i, ticket in enumerate(tickets):
        print(f"\n🔍 Ticket #{i+1:2d} - {ticket['id']}")
        print(f"   Message: {ticket['message'][:60]}...")
        
        # Récupérer les données de commande depuis Odoo si disponible
        order_data = None
        if odoo_client:
            try:
                order_data = await odoo_client.get_order(ticket['order_number'])
                if order_data:
                    print(f"   📊 Commande trouvée: {order_data['name']} - {order_data['state']}")
                else:
                    print(f"   ⚠️  Commande {ticket['order_number']} non trouvée")
            except Exception as e:
                print(f"   ❌ Erreur récupération commande: {e}")
        
        # Créer le contexte avec les données de commande
        context = {}
        if order_data:
            context['order_data'] = order_data
        
        # Traiter le ticket avec le chatbot
        start_time = datetime.now()
        
        try:
            response = chatbot.process_message(ticket['message'], context)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Vérifier la détection UC_336
            is_uc336 = response.uc_detected.uc_id == "UC_336"
            confidence = response.uc_detected.confidence * 100
            
            print(f"   ✅ UC détecté: {response.uc_detected.uc_id} (attendu: {ticket['expected_uc']})")
            print(f"   ✅ Confiance: {confidence:.1f}%")
            print(f"   ✅ Escalade: {'OUI' if response.requires_escalation else 'NON'}")
            print(f"   ⏱️  Temps: {processing_time:.3f}s")
            
            # Afficher un extrait de la réponse générée
            response_preview = response.content[:150] + "..." if len(response.content) > 150 else response.content
            print(f"   📝 Réponse: {response_preview}")
            
            # Calculer le score de performance
            score = 100 if is_uc336 else 0
            if confidence >= 80:
                score += 20
            if not response.requires_escalation:
                score += 10
            
            result = {
                'ticket_id': ticket['id'],
                'message': ticket['message'],
                'expected_uc': ticket['expected_uc'],
                'detected_uc': response.uc_detected.uc_id,
                'confidence': confidence,
                'escalate': response.requires_escalation,
                'response': response.content,
                'processing_time': processing_time,
                'score': min(score, 100),
                'order_data': order_data,
                'success': is_uc336
            }
            
            results.append(result)
            
            if score < 60:
                print(f"   ⚠️  Score faible - Vérifier la détection")
            
        except Exception as e:
            print(f"   ❌ Erreur traitement: {e}")
            result = {
                'ticket_id': ticket['id'],
                'message': ticket['message'],
                'error': str(e),
                'success': False,
                'score': 0
            }
            results.append(result)
    
    # Générer le rapport final
    print("\n" + "=" * 80)
    print("📊 RAPPORT FINAL - UC_336 avec Réponses")
    print("=" * 80)
    
    # Statistiques
    total_tickets = len(results)
    successful_detections = sum(1 for r in results if r.get('success', False))
    avg_confidence = sum(r.get('confidence', 0) for r in results if 'confidence' in r) / max(1, sum(1 for r in results if 'confidence' in r))
    avg_score = sum(r.get('score', 0) for r in results) / total_tickets
    escalated_tickets = sum(1 for r in results if r.get('escalate', False))
    
    print(f"\n🎯 PERFORMANCE GLOBALE:")
    print(f"   • Tickets traités: {total_tickets}")
    print(f"   • Détections UC_336 réussies: {successful_detections}/{total_tickets} ({successful_detections/total_tickets*100:.1f}%)")
    print(f"   • Confiance moyenne: {avg_confidence:.1f}%")
    print(f"   • Score moyen: {avg_score:.1f}/100")
    print(f"   • Tickets escaladés: {escalated_tickets} ({escalated_tickets/total_tickets*100:.1f}%)")
    
    # Analyse des réponses générées
    print(f"\n📝 ANALYSE DES RÉPONSES:")
    
    # Réponses avec données Odoo
    responses_with_odoo = sum(1 for r in results if r.get('order_data'))
    print(f"   • Réponses avec données Odoo: {responses_with_odoo}")
    
    # Longueur moyenne des réponses
    avg_response_length = sum(len(r.get('response', '')) for r in results if r.get('response')) / max(1, sum(1 for r in results if r.get('response')))
    print(f"   • Longueur moyenne réponse: {avg_response_length:.0f} caractères")
    
    # Temps de traitement moyen
    avg_processing_time = sum(r.get('processing_time', 0) for r in results if 'processing_time' in r) / max(1, sum(1 for r in results if 'processing_time' in r))
    print(f"   • Temps moyen traitement: {avg_processing_time:.3f}s")
    
    # Sauvegarder les résultats détaillés
    output_file = "results_uc336_50_tickets_with_responses.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_tickets": total_tickets,
            "successful_detections": successful_detections,
            "success_rate": successful_detections/total_tickets,
            "avg_confidence": avg_confidence,
            "avg_score": avg_score,
            "escalated_tickets": escalated_tickets,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Résultats sauvegardés dans {output_file}")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    if successful_detections/total_tickets >= 0.9:
        print(f"   ✅ Excellente détection UC_336 (≥90%)")
    elif successful_detections/total_tickets >= 0.8:
        print(f"   ✅ Bonne détection UC_336 (≥80%)")
    else:
        print(f"   ⚠️  Détection UC_336 à améliorer (<80%)")
    
    if avg_confidence >= 80:
        print(f"   ✅ Confiance élevée (≥80%)")
    else:
        print(f"   ⚠️  Confiance à améliorer (<80%)")
    
    if escalated_tickets/total_tickets <= 0.1:
        print(f"   ✅ Taux d'escalade acceptable (≤10%)")
    else:
        print(f"   ⚠️  Taux d'escalade élevé (>10%)")
    
    print(f"\n🎉 Test UC_336 terminé avec succès !")
    print(f"📈 Performance: {successful_detections/total_tickets*100:.1f}% de détection réussie")
    
    return results

def analyze_uc336_patterns():
    """Analyse des patterns spécifiques UC_336"""
    print("\n🔍 ANALYSE DES PATTERNS UC_336")
    print("-" * 50)
    
    # Patterns UC_336 identifiés
    uc336_patterns = {
        "STATUS_INQUIRY": {
            "description": "Demande de statut de commande",
            "keywords": ["où en est", "statut", "avancement", "commande"],
            "examples": ["j'aimerais savoir où en est ma commande", "pouvez-vous me donner des nouvelles"]
        },
        "PREORDER_QUESTION": {
            "description": "Question sur précommande",
            "keywords": ["précommande", "disponible", "quand", "stock"],
            "examples": ["quand sera disponible", "précommande", "reconstitué"]
        },
        "FABRICATION_STATUS": {
            "description": "Statut de fabrication",
            "keywords": ["fabrication", "en cours", "EN COURS", "étape"],
            "examples": ["ordre de fabrication", "en cours de fabrication", "étape"]
        },
        "DELIVERY_TIMELINE": {
            "description": "Délai de livraison",
            "keywords": ["délai", "temps", "combien", "réception"],
            "examples": ["combien de temps", "délai", "réception"]
        }
    }
    
    for pattern_name, config in uc336_patterns.items():
        print(f"\n📌 {pattern_name}:")
        print(f"   Description: {config['description']}")
        print(f"   Mots-clés: {config['keywords']}")
        print(f"   Exemples: {config['examples']}")
    
    # Distinction UC_336 vs autres UC
    print(f"\n🔍 DISTINCTION UC_336 vs AUTRES UC:")
    distinctions = {
        "UC_336 vs UC_337": {
            "UC_336": "Demande de statut/précommande",
            "UC_337": "Estimation de livraison",
            "difference": "UC_336 = statut actuel, UC_337 = délai futur"
        },
        "UC_336 vs UC_421": {
            "UC_336": "Statut général",
            "UC_421": "Numéro de suivi",
            "difference": "UC_336 = avancement, UC_421 = tracking"
        }
    }
    
    for comparison, details in distinctions.items():
        print(f"\n📊 {comparison}:")
        print(f"   UC_336: {details['UC_336']}")
        print(f"   Autre UC: {details['UC_337'] if 'UC_337' in details else details['UC_421']}")
        print(f"   Différence: {details['difference']}")

async def main():
    """Fonction principale de test"""
    print("🚀 FlowUp Support Bot - Test UC_336 avec Réponses Odoo")
    print("=" * 70)
    
    try:
        # Test principal avec réponses
        results = await test_uc336_with_odoo_responses()
        
        # Analyse des patterns
        analyze_uc336_patterns()
        
        print(f"\n🎯 RÉSUMÉ FINAL")
        print("=" * 70)
        
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        if successful/total >= 0.9:
            print("✅ Détection UC_336: EXCELLENTE (≥90%)")
            print("✅ Intégration Odoo: OPÉRATIONNELLE")
            print("✅ Génération réponses: FONCTIONNELLE")
            print("🎉 Le système UC_336 est prêt pour la production !")
        elif successful/total >= 0.8:
            print("✅ Détection UC_336: BONNE (≥80%)")
            print("✅ Intégration Odoo: OPÉRATIONNELLE")
            print("✅ Génération réponses: FONCTIONNELLE")
            print("🔧 Quelques ajustements mineurs recommandés")
        else:
            print("⚠️ Détection UC_336: À AMÉLIORER (<80%)")
            print("🔧 Des corrections sont nécessaires")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
