#!/usr/bin/env python3
"""
Test du système final simplifié
Test rapide et efficace du chatbot FlowUp
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.flowup_chatbot import FlowUpChatbot

def test_chatbot():
    """Test du chatbot final"""
    print("🤖 Test du Chatbot FlowUp Final")
    print("=" * 50)
    
    # Initialiser le chatbot
    chatbot = FlowUpChatbot()
    
    # Messages de test
    test_messages = [
        {
            "message": "Bonjour, puis je avoir une estimation de livraison pour ma commande car cela fait 1 semaine que j'ai commandé et payé.",
            "context": {"order_date": datetime.now() - timedelta(days=7)}
        },
        {
            "message": "après avoir différentes manipulation mon pc ne redémarre toujours pas je demande l'échange ou le remboursement",
            "context": {}
        },
        {
            "message": "nous avons seulement recu un ecran sur l'ensemble de la commande",
            "context": {}
        },
        {
            "message": "j'aimerais savoir s'il est possible d'ajouter un SSD en plus ?",
            "context": {}
        },
        {
            "message": "en pleine parti Cs mon ordinateur c'est éteint avec préparation de la réparation automatique les leds de la carte graphique s'éteigne",
            "context": {}
        },
        {
            "message": "j'ai un message alerte surchauffe cpu après 5 minute mon pc s'éteint",
            "context": {}
        },
        {
            "message": "j'habite maintenant au 12b rue madeleine laffitte, Montreuil, 93100. Serait-il possible de changer l'adresse ?",
            "context": {}
        },
        {
            "message": "ça va faire presque 1 mois si vous ne pouvez pas renvoyer une je demande un remboursement total",
            "context": {"order_date": datetime.now() - timedelta(days=25)}
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_messages, 1):
        print(f"\n🔄 Test {i}/{len(test_messages)}")
        print(f"Message: {test_case['message'][:60]}...")
        
        try:
            # Traiter le message
            response = chatbot.process_message(
                message=test_case["message"],
                context=test_case["context"]
            )
            
            # Afficher les résultats
            print(f"✅ UC détecté: {response.uc_detected.uc_id} ({response.uc_detected.confidence:.1%})")
            print(f"📊 Catégorie: {response.uc_detected.category.value}")
            print(f"🚨 Escalade: {'Oui' if response.requires_escalation else 'Non'}")
            if response.escalation_reason:
                print(f"   Raison: {response.escalation_reason}")
            
            # Afficher un extrait de la réponse
            response_preview = response.content[:100] + "..." if len(response.content) > 100 else response.content
            print(f"💬 Réponse: {response_preview}")
            
            results.append({
                "message": test_case["message"],
                "uc_detected": response.uc_detected.uc_id,
                "confidence": response.uc_detected.confidence,
                "category": response.uc_detected.category.value,
                "escalation": response.requires_escalation,
                "response_length": len(response.content)
            })
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            results.append({
                "message": test_case["message"],
                "error": str(e)
            })
    
    # Statistiques finales
    print(f"\n📊 STATISTIQUES FINALES")
    print("=" * 50)
    
    successful_tests = [r for r in results if "error" not in r]
    escalation_count = sum(1 for r in successful_tests if r.get("escalation", False))
    
    print(f"✅ Tests réussis: {len(successful_tests)}/{len(test_messages)}")
    print(f"🚨 Escalades détectées: {escalation_count}")
    print(f"📈 Taux d'escalade: {escalation_count/len(successful_tests)*100:.1f}%")
    
    # Distribution des catégories
    categories = {}
    for result in successful_tests:
        cat = result.get("category", "UNKNOWN")
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📋 Distribution des catégories:")
    for category, count in categories.items():
        print(f"  • {category}: {count}")
    
    # Statistiques du chatbot
    stats = chatbot.get_stats()
    print(f"\n🔧 Configuration du chatbot:")
    print(f"  • UC définis: {stats['uc_definitions_loaded']}")
    print(f"  • Templates: {stats['response_templates_loaded']}")
    print(f"  • Règles métier: {stats['business_rules_loaded']}")
    print(f"  • Mots-clés critiques: {stats['critical_keywords']}")
    
    # Sauvegarder les résultats
    with open("final_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "statistics": {
                "total_tests": len(test_messages),
                "successful_tests": len(successful_tests),
                "escalation_count": escalation_count,
                "escalation_rate": escalation_count/len(successful_tests)*100 if successful_tests else 0,
                "categories": categories
            }
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Résultats sauvegardés dans 'final_test_results.json'")
    
    return results

def test_uc_validation():
    """Test de validation des UC"""
    print("\n🔍 Test de validation des UC")
    print("-" * 40)
    
    chatbot = FlowUpChatbot()
    
    # Tester quelques UC
    test_ucs = ["UC_337", "UC_263", "UC_269", "UC_426", "UC_313", "UC_306", "UC_Unknown"]
    
    for uc_id in test_ucs:
        is_valid = chatbot.validate_uc(uc_id)
        if is_valid:
            uc_info = chatbot.get_uc_info(uc_id)
            print(f"✅ {uc_id}: {uc_info.get('name', 'N/A')}")
            print(f"   Catégorie: {uc_info.get('category', 'N/A')}")
            print(f"   Priorité: {uc_info.get('priority', 'N/A')}")
            print(f"   Auto-escalade: {uc_info.get('auto_escalate', False)}")
        else:
            print(f"❌ {uc_id}: Non trouvé")

def main():
    """Fonction principale"""
    print("🚀 FlowUp Support Bot - Test du Système Final")
    print("=" * 60)
    
    try:
        # Test 1: Validation des UC
        test_uc_validation()
        
        # Test 2: Chatbot complet
        results = test_chatbot()
        
        # Résumé final
        print(f"\n🎉 RÉSUMÉ FINAL")
        print("=" * 60)
        
        successful = len([r for r in results if "error" not in r])
        total = len(results)
        
        print(f"✅ Tests réussis: {successful}/{total}")
        print(f"📊 Taux de succès: {successful/total*100:.1f}%")
        
        if successful == total:
            print("\n🏆 TOUS LES TESTS SONT PASSÉS!")
            print("✅ Le chatbot FlowUp est opérationnel")
        else:
            print(f"\n⚠️ {total - successful} test(s) ont échoué")
            print("🔧 Des corrections sont nécessaires")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
