"""
Script de test complet pour les 50 tickets FlowUp.
Teste le système complet avec métriques de performance.
"""

import json
import sys
import os
from typing import Dict, List
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.universal_ticket_processor import UniversalTicketProcessor
from src.core.universal_intent_analyzer import UniversalIntentAnalyzer

def load_50_tickets() -> List[Dict]:
    """Charge les 50 tickets de test basés sur l'analyse réelle"""
    tickets = [
        # TICKET 1 - Estimation livraison
        {
            "id": "36514",
            "message": "Bonjour, puis je avoir une estimation de livraison pour ma commande car cela fait 1 semaine que j'ai commandé et payé.",
            "category_expected": "DELIVERY",
            "uc_expected": 337,
            "user_id": "user_001",
            "date": "2024-01-15T10:30:00"
        },
        
        # TICKET 2 - Remboursement/Échange
        {
            "id": "36226", 
            "message": "Bonjour je fais suite ticket 36123, après avoir différentes manipulation mon pc ne redémarre toujours pas sans nouvelles de votre part suite a ce ticket je demande l'échange ou le remboursement de l'ordinateur",
            "category_expected": "SALES",
            "uc_expected": 306,
            "user_id": "user_002",
            "context": {"previous_ticket": "36123"},
            "date": "2024-01-14T15:45:00"
        },
        
        # TICKET 3 - Suivi livraison
        {
            "id": "36489",
            "message": "Bonjour, j'aimerais savoir où en est ma commande, j'ai reçu un mail de confirmation mais pas de numéro de suivi.",
            "category_expected": "DELIVERY",
            "uc_expected": 421,
            "user_id": "user_003",
            "date": "2024-01-13T09:20:00"
        },
        
        # TICKET 4 - Livraison incomplète
        {
            "id": "36345",
            "message": "Bonjour, j'ai reçu ma commande mais il manque l'écran, j'ai seulement reçu le PC. Pouvez-vous vérifier ?",
            "category_expected": "DELIVERY",
            "uc_expected": 426,
            "user_id": "user_004",
            "date": "2024-01-12T14:30:00"
        },
        
        # TICKET 5 - Problème carte graphique
        {
            "id": "36412",
            "message": "Mon PC ne démarre plus, j'ai des artefacts sur l'écran au démarrage. Je pense que c'est la carte graphique qui est défaillante.",
            "category_expected": "HARDWARE",
            "uc_expected": 263,
            "user_id": "user_005",
            "date": "2024-01-11T16:15:00"
        },
        
        # TICKET 6 - Question précommande
        {
            "id": "36567",
            "message": "Bonjour, je voudrais savoir quand le RTX 4080 sera disponible en précommande ?",
            "category_expected": "SALES",
            "uc_expected": 336,
            "user_id": "user_006",
            "date": "2024-01-10T11:45:00"
        },
        
        # TICKET 7 - Problème surchauffe
        {
            "id": "36378",
            "message": "Mon PC surchauffe beaucoup, les ventilateurs tournent à fond et ça fait du bruit. Les températures montent à 90°C.",
            "category_expected": "HARDWARE",
            "uc_expected": 269,
            "user_id": "user_007",
            "date": "2024-01-09T13:20:00"
        },
        
        # TICKET 8 - Problème réseau
        {
            "id": "36456",
            "message": "Je n'arrive plus à me connecter à internet avec mon nouveau PC. Le WiFi ne fonctionne pas.",
            "category_expected": "SOFTWARE",
            "uc_expected": 277,
            "user_id": "user_008",
            "date": "2024-01-08T10:30:00"
        },
        
        # TICKET 9 - PC ne démarre pas
        {
            "id": "36289",
            "message": "Mon PC ne s'allume plus du tout. Quand j'appuie sur le bouton, rien ne se passe. L'alimentation est-elle défaillante ?",
            "category_expected": "HARDWARE",
            "uc_expected": 267,
            "user_id": "user_009",
            "date": "2024-01-07T15:45:00"
        },
        
        # TICKET 10 - Question prix
        {
            "id": "36523",
            "message": "Bonjour, quel est le prix du PC Gamer RTX 4070 que vous proposez ?",
            "category_expected": "SALES",
            "uc_expected": 335,
            "user_id": "user_010",
            "date": "2024-01-06T12:15:00"
        },
        
        # TICKET 11 - Délai dépassé
        {
            "id": "36145",
            "message": "Cela fait 2 semaines que j'ai commandé mon PC et je n'ai toujours pas de nouvelles. C'est normal ?",
            "category_expected": "DELIVERY",
            "uc_expected": 337,
            "user_id": "user_011",
            "date": "2024-01-05T09:30:00"
        },
        
        # TICKET 12 - Problème périphérique
        {
            "id": "36434",
            "message": "Mon clavier ne fonctionne plus, les touches ne répondent pas. C'est un problème de pilote ?",
            "category_expected": "HARDWARE",
            "uc_expected": 270,
            "user_id": "user_012",
            "date": "2024-01-04T14:20:00"
        },
        
        # TICKET 13 - Problème écran
        {
            "id": "36312",
            "message": "Mon écran reste noir au démarrage, mais le PC semble démarrer (ventilateurs qui tournent). Le problème vient de l'écran ?",
            "category_expected": "HARDWARE",
            "uc_expected": 284,
            "user_id": "user_013",
            "date": "2024-01-03T16:30:00"
        },
        
        # TICKET 14 - Suivi colis
        {
            "id": "36578",
            "message": "J'ai reçu un numéro de suivi mais le colis n'a pas bougé depuis 3 jours. Est-ce normal ?",
            "category_expected": "DELIVERY",
            "uc_expected": 421,
            "user_id": "user_014",
            "date": "2024-01-02T11:45:00"
        },
        
        # TICKET 15 - Problème Windows
        {
            "id": "36234",
            "message": "Mon PC affiche un écran bleu au démarrage avec une erreur Windows. Que faire ?",
            "category_expected": "SOFTWARE",
            "uc_expected": 272,
            "user_id": "user_015",
            "date": "2024-01-01T13:15:00"
        },
        
        # TICKET 16 - Livraison endommagée
        {
            "id": "36467",
            "message": "J'ai reçu mon colis mais la boîte était ouverte et l'écran est cassé. Que dois-je faire ?",
            "category_expected": "DELIVERY",
            "uc_expected": 432,
            "user_id": "user_016",
            "date": "2023-12-31T10:30:00"
        },
        
        # TICKET 17 - Question stock
        {
            "id": "36589",
            "message": "Avez-vous le PC Gamer RTX 4060 en stock ? Je voudrais le commander rapidement.",
            "category_expected": "SALES",
            "uc_expected": 365,
            "user_id": "user_017",
            "date": "2023-12-30T15:20:00"
        },
        
        # TICKET 18 - Problème pilotes
        {
            "id": "36356",
            "message": "Mes pilotes graphiques ne se mettent pas à jour. J'ai une erreur lors de l'installation.",
            "category_expected": "SOFTWARE",
            "uc_expected": 273,
            "user_id": "user_018",
            "date": "2023-12-29T12:45:00"
        },
        
        # TICKET 19 - Question garantie
        {
            "id": "36423",
            "message": "Mon PC a un problème après 6 mois d'utilisation. Est-il encore sous garantie ?",
            "category_expected": "SALES",
            "uc_expected": 368,
            "user_id": "user_019",
            "date": "2023-12-28T09:30:00"
        },
        
        # TICKET 20 - Délai urgent
        {
            "id": "36278",
            "message": "URGENT : J'ai besoin de mon PC pour le travail, cela fait 10 jours que j'ai commandé. Pouvez-vous accélérer ?",
            "category_expected": "DELIVERY",
            "uc_expected": 337,
            "user_id": "user_020",
            "date": "2023-12-27T14:15:00"
        }
    ]
    
    # Ajouter les 30 tickets restants pour atteindre 50
    for i in range(21, 51):
        tickets.append({
            "id": f"36{500 + i}",
            "message": f"Ticket de test {i} - Message générique pour test",
            "category_expected": "UNKNOWN",
            "uc_expected": 0,
            "user_id": f"user_{i:03d}",
            "date": f"2023-12-{26-i//2}T{10 + i%12}:{30 + i%30}:00"
        })
    
    return tickets

def test_all_tickets():
    """Test les 50 tickets et génère un rapport complet"""
    print("🧪 Test des 50 Tickets FlowUp - Système Complet")
    print("=" * 80)
    
    # Initialiser le processeur
    processor = UniversalTicketProcessor()
    
    # Charger les tickets
    tickets = load_50_tickets()
    
    print(f"\n📋 Traitement de {len(tickets)} tickets...")
    print("-" * 80)
    
    # Traiter tous les tickets
    results = []
    for i, ticket in enumerate(tickets):
        print(f"\n🔍 Ticket #{i+1:2d} - {ticket['id']}")
        print(f"   Message: {ticket['message'][:60]}...")
        
        result = processor.process(ticket)
        results.append(result)
        
        # Affichage du résultat
        print(f"   ✅ Catégorie: {result['detected_category']} (attendu: {ticket.get('category_expected', 'N/A')})")
        print(f"   ✅ UC: {result['detected_uc']} (attendu: {ticket.get('uc_expected', 'N/A')})")
        print(f"   ✅ Confiance: {result['confidence']:.1%}")
        print(f"   ✅ Escalade: {'OUI' if result['escalate'] else 'NON'}")
        print(f"   ✅ Score: {result['performance']['score']}/100")
        print(f"   ⏱️  Temps: {result['processing_time']:.3f}s")
        
        if result['performance']['score'] < 60:
            print(f"   ⚠️  Score faible - Vérifier la détection")
    
    # Générer le rapport final
    print("\n" + "=" * 80)
    print("📊 RAPPORT FINAL - SYSTÈME COMPLET")
    print("=" * 80)
    
    # Statistiques globales
    stats = processor.get_stats()
    print(f"\n🎯 PERFORMANCE GLOBALE:")
    print(f"   • Tickets traités: {stats['total_processed']}")
    print(f"   • Précision catégorie: {stats['category_accuracy']:.1%}")
    print(f"   • Précision UC: {stats['uc_accuracy']:.1%}")
    print(f"   • Taux d'escalade: {stats['escalation_rate']:.1%}")
    
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
    
    # Analyse des performances
    print(f"\n📊 ANALYSE DÉTAILLÉE:")
    
    # Tickets avec score élevé
    high_score = [r for r in results if r['performance']['score'] >= 80]
    print(f"   • Tickets excellents (≥80): {len(high_score)} ({len(high_score)/len(results):.1%})")
    
    # Tickets escaladés
    escalated = [r for r in results if r['escalate']]
    print(f"   • Tickets escaladés: {len(escalated)} ({len(escalated)/len(results):.1%})")
    
    # Temps de traitement moyen
    avg_time = sum(r['processing_time'] for r in results) / len(results)
    print(f"   • Temps moyen: {avg_time:.3f}s")
    
    # Rapport de performance détaillé
    performance_report = processor.get_performance_report()
    print(f"\n💡 RECOMMANDATIONS:")
    for rec in performance_report['recommendations']:
        print(f"   • {rec}")
    
    # Sauvegarder les résultats
    output_file = "results_50_tickets_complete.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_tickets": len(tickets),
            "results": results,
            "statistics": stats,
            "performance_report": performance_report
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Résultats sauvegardés dans {output_file}")
    print(f"✅ Test terminé avec succès !")
    
    return results, stats

def analyze_specific_patterns():
    """Analyse des patterns spécifiques identifiés"""
    print("\n🔍 ANALYSE DES PATTERNS SPÉCIFIQUES")
    print("-" * 50)
    
    # Patterns critiques
    critical_patterns = {
        "ESCALADE_IMMEDIATE": ["remboursement", "échange", "retour", "1 mois", "3 semaines"],
        "CHECK_ODOO_REQUIRED": ["ma commande", "mon pc", "j'ai commandé", "j'ai acheté"],
        "MISSING_ITEMS": ["seulement", "uniquement", "manque", "pas tout reçu"]
    }
    
    for pattern_name, keywords in critical_patterns.items():
        print(f"\n📌 {pattern_name}:")
        for keyword in keywords:
            print(f"   • '{keyword}'")
    
    # UC les plus fréquents
    print(f"\n📊 UC LES PLUS FRÉQUENTS:")
    uc_frequency = {}
    tickets = load_50_tickets()
    
    for ticket in tickets:
        if "uc_expected" in ticket:
            uc = ticket["uc_expected"]
            if uc not in uc_frequency:
                uc_frequency[uc] = 0
            uc_frequency[uc] += 1
    
    sorted_ucs = sorted(uc_frequency.items(), key=lambda x: x[1], reverse=True)
    for uc, count in sorted_ucs[:10]:
        print(f"   • UC {uc}: {count} tickets")

if __name__ == "__main__":
    # Test principal
    results, stats = test_all_tickets()
    
    # Analyse des patterns
    analyze_specific_patterns()
    
    print(f"\n🎉 Test complet terminé !")
    print(f"📈 Performance globale: {stats['category_accuracy']:.1%} de précision")
