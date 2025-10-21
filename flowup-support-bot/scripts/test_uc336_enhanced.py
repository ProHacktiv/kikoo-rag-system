#!/usr/bin/env python3
"""
Test de la détection UC_336 améliorée
Validation sur les tickets réels UC_336
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.enhanced_flowup_chatbot import EnhancedFlowUpChatbot
from src.detectors.uc336_detector import UC336Detector

def test_uc336_detection():
    """Test de détection UC_336 sur des cas réels"""
    print("🧪 Test Détection UC_336 Améliorée")
    print("=" * 60)
    
    # Initialiser le chatbot amélioré
    chatbot = EnhancedFlowUpChatbot()
    
    # Cas de test UC_336 (doivent être détectés)
    positive_cases = [
        {
            "message": "Commande effectuée le 24/03 : ordre de fabrication toujours noté EN COURS, des infos ?",
            "expected": True,
            "description": "Demande de statut avec mention EN COURS"
        },
        {
            "message": "j'ai passé commande il y a une semaine j'aimerai savoir où en est la commande",
            "expected": True,
            "description": "Demande d'avancement récente"
        },
        {
            "message": "Bonjour, j'aimerais connaître l'avancement de ma commande",
            "expected": True,
            "description": "Demande d'avancement simple"
        },
        {
            "message": "Ma commande est toujours en fabrication, pouvez-vous me donner des nouvelles ?",
            "expected": True,
            "description": "Statut visible mentionné"
        },
        {
            "message": "Commande passée il y a 5 jours, où en est-elle ?",
            "expected": True,
            "description": "Demande de statut récente"
        }
    ]
    
    # Cas de test négatifs (ne doivent PAS être détectés comme UC_336)
    negative_cases = [
        {
            "message": "ma commande n'est pas livrée. 16 jours ouvrés depuis la commande",
            "expected": False,
            "description": "Retard explicite → UC_337"
        },
        {
            "message": "Quand vais-je recevoir ma commande ? C'est urgent",
            "expected": False,
            "description": "Focus livraison → UC_337"
        },
        {
            "message": "J'ai besoin du numéro de suivi de ma commande",
            "expected": False,
            "description": "Demande tracking → UC_421"
        },
        {
            "message": "Ma commande est défectueuse, je veux un remboursement",
            "expected": False,
            "description": "Remboursement → UC_306"
        },
        {
            "message": "Mon PC ne démarre pas, problème technique",
            "expected": False,
            "description": "Problème technique → UC_263"
        }
    ]
    
    print("🔍 Test des cas positifs (doivent détecter UC_336)")
    print("-" * 50)
    
    positive_success = 0
    for i, case in enumerate(positive_cases, 1):
        print(f"\n📋 Test {i}: {case['description']}")
        print(f"Message: {case['message']}")
        
        # Test avec le chatbot amélioré
        response = chatbot.process_message(case['message'])
        
        is_uc336 = response.uc_detected.uc_id == "UC_336"
        confidence = response.uc_detected.confidence * 100
        
        print(f"Résultat: {'✅ UC_336' if is_uc336 else '❌ Pas UC_336'}")
        print(f"Confiance: {confidence:.1f}%")
        print(f"Escalade: {'OUI' if response.requires_escalation else 'NON'}")
        
        if is_uc336 == case['expected']:
            positive_success += 1
            print("✅ SUCCÈS")
        else:
            print("❌ ÉCHEC")
    
    print(f"\n🔍 Test des cas négatifs (ne doivent PAS détecter UC_336)")
    print("-" * 50)
    
    negative_success = 0
    for i, case in enumerate(negative_cases, 1):
        print(f"\n📋 Test {i}: {case['description']}")
        print(f"Message: {case['message']}")
        
        # Test avec le chatbot amélioré
        response = chatbot.process_message(case['message'])
        
        is_uc336 = response.uc_detected.uc_id == "UC_336"
        confidence = response.uc_detected.confidence * 100
        
        print(f"Résultat: {'✅ UC_336' if is_uc336 else '❌ Pas UC_336'}")
        print(f"Confiance: {confidence:.1f}%")
        print(f"UC détecté: {response.uc_detected.uc_id}")
        
        if is_uc336 == case['expected']:
            negative_success += 1
            print("✅ SUCCÈS")
        else:
            print("❌ ÉCHEC")
    
    # Rapport final
    total_tests = len(positive_cases) + len(negative_cases)
    total_success = positive_success + negative_success
    
    print(f"\n📊 RAPPORT FINAL")
    print("=" * 60)
    print(f"✅ Tests positifs réussis: {positive_success}/{len(positive_cases)}")
    print(f"✅ Tests négatifs réussis: {negative_success}/{len(negative_cases)}")
    print(f"📈 Taux de succès global: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
    
    if total_success == total_tests:
        print(f"\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print(f"✅ La détection UC_336 est opérationnelle")
    else:
        print(f"\n⚠️ {total_tests - total_success} test(s) ont échoué")
        print(f"🔧 Des ajustements sont nécessaires")
    
    return total_success == total_tests

def test_uc336_with_order_data():
    """Test UC_336 avec données de commande"""
    print(f"\n🔧 Test UC_336 avec données de commande")
    print("-" * 50)
    
    chatbot = EnhancedFlowUpChatbot()
    
    # Simuler des données de commande
    order_data = {
        "order_date": datetime.now() - timedelta(days=5),
        "status": "EN COURS",
        "id": "CMD-2024-001"
    }
    
    context = {"order_data": order_data}
    
    message = "où en est ma commande ?"
    
    print(f"Message: {message}")
    print(f"Données commande: {order_data}")
    
    response = chatbot.process_message(message, context)
    
    print(f"\nRésultat:")
    print(f"UC détecté: {response.uc_detected.uc_id}")
    print(f"Confiance: {response.uc_detected.confidence*100:.1f}%")
    print(f"Escalade: {'OUI' if response.requires_escalation else 'NON'}")
    
    # Afficher un extrait de la réponse
    response_preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
    print(f"\nRéponse générée:")
    print(f"{response_preview}")
    
    return response.uc_detected.uc_id == "UC_336"

def test_detection_debug():
    """Test de debug de la détection"""
    print(f"\n🔍 Test de debug détection UC_336")
    print("-" * 50)
    
    chatbot = EnhancedFlowUpChatbot()
    
    test_messages = [
        "où en est ma commande ?",
        "j'aimerais connaître l'avancement",
        "ma commande est toujours en cours",
        "quand vais-je recevoir ma commande ?",
        "j'ai besoin du tracking"
    ]
    
    for message in test_messages:
        print(f"\n📝 Message: {message}")
        debug_info = chatbot.test_uc336_detection(message)
        print(debug_info)

def main():
    """Fonction principale de test"""
    print("🚀 FlowUp Support Bot - Test UC_336 Amélioré")
    print("=" * 70)
    
    try:
        # Test 1: Détection UC_336
        success1 = test_uc336_detection()
        
        # Test 2: Avec données de commande
        success2 = test_uc336_with_order_data()
        
        # Test 3: Debug
        test_detection_debug()
        
        # Résumé final
        print(f"\n🎯 RÉSUMÉ FINAL")
        print("=" * 70)
        
        if success1 and success2:
            print("✅ Détection UC_336: OPÉRATIONNELLE")
            print("✅ Intégration chatbot: OPÉRATIONNELLE")
            print("🎉 Le système UC_336 est prêt pour la production !")
        else:
            print("⚠️ Des problèmes ont été détectés")
            print("🔧 Des corrections sont nécessaires")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
