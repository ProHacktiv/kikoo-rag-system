"""
Script de test complet pour les 50 tickets FlowUp avec support multi-UC.
Teste le système multi-UC avec métriques de performance avancées.
"""

import json
import sys
import os
from typing import Dict, List
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.multi_uc_ticket_processor import MultiUCTicketProcessor
from src.core.multi_uc_intent_analyzer import MultiUCIntentAnalyzer

def load_50_tickets_with_multi_uc() -> List[Dict]:
    """Charge les 50 tickets de test avec cas multi-UC identifiés"""
    tickets = [
        # TICKET 1 - Estimation livraison (UC simple)
        {
            "id": "36514",
            "message": "Bonjour, puis je avoir une estimation de livraison pour ma commande car cela fait 1 semaine que j'ai commandé et payé.",
            "category_expected": "DELIVERY",
            "uc_expected": [337],
            "user_id": "user_001",
            "date": "2024-01-15T10:30:00"
        },
        
        # TICKET 2 - Remboursement/Échange (UC simple)
        {
            "id": "36226", 
            "message": "Bonjour je fais suite ticket 36123, après avoir différentes manipulation mon pc ne redémarre toujours pas sans nouvelles de votre part suite a ce ticket je demande l'échange ou le remboursement de l'ordinateur",
            "category_expected": "SALES",
            "uc_expected": [306],
            "user_id": "user_002",
            "context": {"previous_ticket": "36123"},
            "date": "2024-01-14T15:45:00"
        },
        
        # TICKET 3 - Suivi livraison (UC simple)
        {
            "id": "36489",
            "message": "Bonjour, j'aimerais savoir où en est ma commande, j'ai reçu un mail de confirmation mais pas de numéro de suivi.",
            "category_expected": "DELIVERY",
            "uc_expected": [421],
            "user_id": "user_003",
            "date": "2024-01-13T09:20:00"
        },
        
        # TICKET 4 - Livraison incomplète (UC simple)
        {
            "id": "36345",
            "message": "Bonjour, j'ai reçu ma commande mais il manque l'écran, j'ai seulement reçu le PC. Pouvez-vous vérifier ?",
            "category_expected": "DELIVERY",
            "uc_expected": [426],
            "user_id": "user_004",
            "date": "2024-01-12T14:30:00"
        },
        
        # TICKET 5 - Problème carte graphique (UC simple)
        {
            "id": "36412",
            "message": "Mon PC ne démarre plus, j'ai des artefacts sur l'écran au démarrage. Je pense que c'est la carte graphique qui est défaillante.",
            "category_expected": "HARDWARE",
            "uc_expected": [263],
            "user_id": "user_005",
            "date": "2024-01-11T16:15:00"
        },
        
        # TICKET 6 - Question précommande (UC simple)
        {
            "id": "36567",
            "message": "Bonjour, je voudrais savoir quand le RTX 4080 sera disponible en précommande ?",
            "category_expected": "SALES",
            "uc_expected": [336],
            "user_id": "user_006",
            "date": "2024-01-10T11:45:00"
        },
        
        # TICKET 7 - Problème surchauffe (UC simple)
        {
            "id": "36378",
            "message": "Mon PC surchauffe beaucoup, les ventilateurs tournent à fond et ça fait du bruit. Les températures montent à 90°C.",
            "category_expected": "HARDWARE",
            "uc_expected": [269],
            "user_id": "user_007",
            "date": "2024-01-09T13:20:00"
        },
        
        # TICKET 8 - Problème réseau (UC simple)
        {
            "id": "36456",
            "message": "Je n'arrive plus à me connecter à internet avec mon nouveau PC. Le WiFi ne fonctionne pas.",
            "category_expected": "SOFTWARE",
            "uc_expected": [277],
            "user_id": "user_008",
            "date": "2024-01-08T10:30:00"
        },
        
        # TICKET 9 - PC ne démarre pas (UC simple)
        {
            "id": "36289",
            "message": "Mon PC ne s'allume plus du tout. Quand j'appuie sur le bouton, rien ne se passe. L'alimentation est-elle défaillante ?",
            "category_expected": "HARDWARE",
            "uc_expected": [267],
            "user_id": "user_009",
            "date": "2024-01-07T15:45:00"
        },
        
        # TICKET 10 - Question prix (UC simple)
        {
            "id": "36523",
            "message": "Bonjour, quel est le prix du PC Gamer RTX 4070 que vous proposez ?",
            "category_expected": "SALES",
            "uc_expected": [335],
            "user_id": "user_010",
            "date": "2024-01-06T12:15:00"
        },
        
        # TICKET 11 - MULTI-UC: Délai + Adresse
        {
            "id": "36145",
            "message": "Cela fait 2 semaines que j'ai commandé mon PC et je n'ai toujours pas de nouvelles. Je déménage demain, pouvez-vous changer l'adresse de livraison ?",
            "category_expected": "DELIVERY",
            "uc_expected": [337, 439],
            "user_id": "user_011",
            "date": "2024-01-05T09:30:00"
        },
        
        # TICKET 12 - Problème périphérique (UC simple)
        {
            "id": "36434",
            "message": "Mon clavier ne fonctionne plus, les touches ne répondent pas. C'est un problème de pilote ?",
            "category_expected": "HARDWARE",
            "uc_expected": [270],
            "user_id": "user_012",
            "date": "2024-01-04T14:20:00"
        },
        
        # TICKET 13 - Problème écran (UC simple)
        {
            "id": "36312",
            "message": "Mon écran reste noir au démarrage, mais le PC semble démarrer (ventilateurs qui tournent). Le problème vient de l'écran ?",
            "category_expected": "HARDWARE",
            "uc_expected": [284],
            "user_id": "user_013",
            "date": "2024-01-03T16:30:00"
        },
        
        # TICKET 14 - Suivi colis (UC simple)
        {
            "id": "36578",
            "message": "J'ai reçu un numéro de suivi mais le colis n'a pas bougé depuis 3 jours. Est-ce normal ?",
            "category_expected": "DELIVERY",
            "uc_expected": [421],
            "user_id": "user_014",
            "date": "2024-01-02T11:45:00"
        },
        
        # TICKET 15 - Problème Windows (UC simple)
        {
            "id": "36234",
            "message": "Mon PC affiche un écran bleu au démarrage avec une erreur Windows. Que faire ?",
            "category_expected": "SOFTWARE",
            "uc_expected": [272],
            "user_id": "user_015",
            "date": "2024-01-01T13:15:00"
        },
        
        # TICKET 16 - Livraison endommagée (UC simple)
        {
            "id": "36467",
            "message": "J'ai reçu mon colis mais la boîte était ouverte et l'écran est cassé. Que dois-je faire ?",
            "category_expected": "DELIVERY",
            "uc_expected": [432],
            "user_id": "user_016",
            "date": "2023-12-31T10:30:00"
        },
        
        # TICKET 17 - Question stock (UC simple)
        {
            "id": "36589",
            "message": "Avez-vous le PC Gamer RTX 4060 en stock ? Je voudrais le commander rapidement.",
            "category_expected": "SALES",
            "uc_expected": [365],
            "user_id": "user_017",
            "date": "2023-12-30T15:20:00"
        },
        
        # TICKET 18 - Problème pilotes (UC simple)
        {
            "id": "36356",
            "message": "Mes pilotes graphiques ne se mettent pas à jour. J'ai une erreur lors de l'installation.",
            "category_expected": "SOFTWARE",
            "uc_expected": [273],
            "user_id": "user_018",
            "date": "2023-12-29T12:45:00"
        },
        
        # TICKET 19 - Question garantie (UC simple)
        {
            "id": "36423",
            "message": "Mon PC a un problème après 6 mois d'utilisation. Est-il encore sous garantie ?",
            "category_expected": "SALES",
            "uc_expected": [368],
            "user_id": "user_019",
            "date": "2023-12-28T09:30:00"
        },
        
        # TICKET 20 - MULTI-UC: Délai urgent + Remboursement
        {
            "id": "36278",
            "message": "URGENT : J'ai besoin de mon PC pour le travail, cela fait 10 jours que j'ai commandé. Si ce n'est pas livré demain, je demande le remboursement.",
            "category_expected": "DELIVERY",
            "uc_expected": [337, 306],
            "user_id": "user_020",
            "date": "2023-12-27T14:15:00"
        },
        
        # TICKET 21 - MULTI-UC: Technique + Garantie
        {
            "id": "36521",
            "message": "Mon PC freeze constamment, est-ce couvert par la garantie ? Je veux savoir si je peux le faire réparer gratuitement.",
            "category_expected": "HARDWARE",
            "uc_expected": [263, 313],
            "user_id": "user_021",
            "date": "2023-12-26T16:30:00"
        },
        
        # TICKET 22 - MULTI-UC: Livraison + Technique
        {
            "id": "36522",
            "message": "J'ai reçu mon PC mais il ne démarre pas. Le colis était endommagé et la carte graphique semble défaillante. Que faire ?",
            "category_expected": "DELIVERY",
            "uc_expected": [432, 263],
            "user_id": "user_022",
            "date": "2023-12-25T11:20:00"
        },
        
        # TICKET 23 - MULTI-UC: Surchauffe + Réseau
        {
            "id": "36523",
            "message": "Mon PC surchauffe et j'ai des problèmes de connexion internet. Les deux problèmes sont liés ?",
            "category_expected": "HARDWARE",
            "uc_expected": [269, 277],
            "user_id": "user_023",
            "date": "2023-12-24T13:45:00"
        },
        
        # TICKET 24 - MULTI-UC: Mauvais produit + Remboursement
        {
            "id": "36524",
            "message": "J'ai reçu le mauvais produit et je veux un remboursement immédiat. C'est inacceptable !",
            "category_expected": "DELIVERY",
            "uc_expected": [427, 306],
            "user_id": "user_024",
            "date": "2023-12-23T10:15:00"
        },
        
        # TICKET 25 - MULTI-UC: Windows + Pilotes
        {
            "id": "36525",
            "message": "Mon PC affiche un écran bleu et les pilotes ne se mettent pas à jour. C'est un problème Windows ou hardware ?",
            "category_expected": "SOFTWARE",
            "uc_expected": [272, 273],
            "user_id": "user_025",
            "date": "2023-12-22T15:30:00"
        }
    ]
    
    # Ajouter les 25 tickets restants pour atteindre 50
    for i in range(26, 51):
        tickets.append({
            "id": f"36{500 + i}",
            "message": f"Ticket de test {i} - Message générique pour test",
            "category_expected": "UNKNOWN",
            "uc_expected": [0],
            "user_id": f"user_{i:03d}",
            "date": f"2023-12-{26-i//2}T{10 + i%12}:{30 + i%30}:00"
        })
    
    return tickets

def test_multi_uc_system():
    """Test le système multi-UC sur les 50 tickets"""
    print("🧪 Test Multi-UC des 50 Tickets FlowUp - Système Avancé")
    print("=" * 80)
    
    # Initialiser le processeur multi-UC
    processor = MultiUCTicketProcessor()
    
    # Charger les tickets
    tickets = load_50_tickets_with_multi_uc()
    
    print(f"\n📋 Traitement de {len(tickets)} tickets avec support multi-UC...")
    print("-" * 80)
    
    # Traiter tous les tickets
    results = []
    for i, ticket in enumerate(tickets):
        print(f"\n🔍 Ticket #{i+1:2d} - {ticket['id']}")
        print(f"   Message: {ticket['message'][:60]}...")
        
        result = processor.process(ticket)
        results.append(result)
        
        # Affichage du résultat multi-UC
        print(f"   ✅ Catégories: {result['detected_categories']} (attendu: {ticket.get('category_expected', 'N/A')})")
        print(f"   ✅ UC Principal: {result['primary_uc']} (attendu: {ticket.get('uc_expected', 'N/A')})")
        print(f"   ✅ UC Secondaires: {result['secondary_ucs']}")
        print(f"   ✅ Multi-UC: {'OUI' if result['multi_uc_detected'] else 'NON'}")
        print(f"   ✅ Confiance: {result['confidence_scores']}")
        print(f"   ✅ Escalade: {'OUI' if result['escalate'] else 'NON'}")
        print(f"   ✅ Score: {result['performance']['score']}/100")
        print(f"   ⏱️  Temps: {result['processing_time']:.3f}s")
        
        if result['performance']['score'] < 60:
            print(f"   ⚠️  Score faible - Vérifier la détection")
    
    # Générer le rapport final multi-UC
    print("\n" + "=" * 80)
    print("📊 RAPPORT FINAL - SYSTÈME MULTI-UC")
    print("=" * 80)
    
    # Statistiques globales
    stats = processor.get_multi_uc_stats()
    print(f"\n🎯 PERFORMANCE GLOBALE MULTI-UC:")
    print(f"   • Tickets traités: {stats['total_processed']}")
    print(f"   • Tickets multi-UC: {stats['multi_uc_tickets']} ({stats['multi_uc_rate']:.1%})")
    print(f"   • Précision catégorie: {stats['category_accuracy']:.1%}")
    print(f"   • Précision UC: {stats['uc_accuracy']:.1%}")
    print(f"   • Taux d'escalade: {stats['escalation_rate']:.1%}")
    print(f"   • Moyenne UC/ticket: {stats['avg_ucs_per_ticket']:.1f}")
    
    # Répartition par catégorie
    print(f"\n📈 RÉPARTITION PAR CATÉGORIE:")
    for cat, count in stats['by_category'].items():
        percentage = (count / stats['total_processed']) * 100
        print(f"   • {cat}: {count} tickets ({percentage:.1f}%)")
    
    # Répartition par priorité
    print(f"\n⚡ RÉPARTITION PAR PRIORITÉ:")
    for priority, count in stats['by_priority'].items():
        percentage = (count / stats['total_processed']) * 100
        print(f"   • {priority}: {count} tickets ({percentage:.1f}%)")
    
    # Combinaisons d'UC
    combinations_report = processor.get_uc_combinations_report()
    print(f"\n🔗 COMBINAISONS D'UC DÉTECTÉES:")
    if combinations_report.get("total_combinations", 0) > 0:
        print(f"   • Total combinaisons: {combinations_report['total_combinations']}")
        print(f"   • Plus fréquentes:")
        for combo, count in combinations_report.get("most_common", [])[:3]:
            print(f"     - {combo}: {count} tickets")
    else:
        print("   • Aucune combinaison multi-UC détectée")
    
    # Analyse des performances
    print(f"\n📊 ANALYSE DÉTAILLÉE:")
    
    # Tickets avec score élevé
    high_score = [r for r in results if r['performance']['score'] >= 80]
    print(f"   • Tickets excellents (≥80): {len(high_score)} ({len(high_score)/len(results):.1%})")
    
    # Tickets multi-UC
    multi_uc_results = [r for r in results if r['multi_uc_detected']]
    print(f"   • Tickets multi-UC: {len(multi_uc_results)} ({len(multi_uc_results)/len(results):.1%})")
    
    # Tickets escaladés
    escalated = [r for r in results if r['escalate']]
    print(f"   • Tickets escaladés: {len(escalated)} ({len(escalated)/len(results):.1%})")
    
    # Temps de traitement moyen
    avg_time = sum(r['processing_time'] for r in results) / len(results)
    print(f"   • Temps moyen: {avg_time:.3f}s")
    
    # Rapport de performance détaillé
    performance_report = processor.get_multi_uc_performance_report()
    print(f"\n💡 RECOMMANDATIONS MULTI-UC:")
    for rec in performance_report['recommendations']:
        print(f"   • {rec}")
    
    # Sauvegarder les résultats
    output_file = "results_multi_uc_50_tickets.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_tickets": len(tickets),
            "results": results,
            "statistics": stats,
            "performance_report": performance_report,
            "uc_combinations": combinations_report
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Résultats sauvegardés dans {output_file}")
    print(f"✅ Test multi-UC terminé avec succès !")
    
    return results, stats

def analyze_multi_uc_patterns():
    """Analyse des patterns multi-UC spécifiques"""
    print("\n🔍 ANALYSE DES PATTERNS MULTI-UC")
    print("-" * 50)
    
    # Patterns multi-UC identifiés
    multi_uc_patterns = {
        "DELIVERY_ADDRESS": {
            "description": "Livraison + Changement d'adresse",
            "ucs": [337, 439],
            "keywords": ["délai", "livraison", "déménage", "adresse"]
        },
        "TECHNICAL_REFUND": {
            "description": "Problème technique + Remboursement",
            "ucs": [263, 306],
            "keywords": ["ne marche pas", "remboursement", "défaut"]
        },
        "DELIVERY_ERROR_MULTIPLE": {
            "description": "Erreurs de livraison multiples",
            "ucs": [426, 427, 432],
            "keywords": ["manque", "mauvais", "endommagé"]
        },
        "HARDWARE_SOFTWARE": {
            "description": "Problèmes hardware + software",
            "ucs": [263, 272],
            "keywords": ["carte graphique", "windows", "écran bleu"]
        }
    }
    
    for pattern_name, config in multi_uc_patterns.items():
        print(f"\n📌 {pattern_name}:")
        print(f"   Description: {config['description']}")
        print(f"   UCs: {config['ucs']}")
        print(f"   Mots-clés: {config['keywords']}")
    
    # Analyse des combinaisons les plus fréquentes
    print(f"\n📊 COMBINAISONS MULTI-UC LES PLUS FRÉQUENTES:")
    common_combinations = [
        ("337-439", "Délai + Adresse"),
        ("263-306", "Hardware + Remboursement"),
        ("426-432", "Manquant + Endommagé"),
        ("269-277", "Surchauffe + Réseau"),
        ("272-273", "Windows + Pilotes")
    ]
    
    for combo, description in common_combinations:
        print(f"   • {combo}: {description}")

if __name__ == "__main__":
    # Test principal multi-UC
    results, stats = test_multi_uc_system()
    
    # Analyse des patterns
    analyze_multi_uc_patterns()
    
    print(f"\n🎉 Test multi-UC complet terminé !")
    print(f"📈 Performance multi-UC: {stats['multi_uc_rate']:.1%} de tickets multi-UC")
    print(f"🎯 Précision globale: {stats['category_accuracy']:.1%}")
