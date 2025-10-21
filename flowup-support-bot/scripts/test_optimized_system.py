#!/usr/bin/env python3
"""
Test du système FlowUp optimisé
Script de test complet pour valider toutes les améliorations
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Ajouter le chemin src au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_uc263_detector_fixed():
    """Test du détecteur UC_263 corrigé"""
    print("🧪 TEST DÉTECTEUR UC_263 CORRIGÉ")
    print("=" * 40)
    
    try:
        from detectors.uc263_detector_fixed import UC263DetectorFixed
        
        detector = UC263DetectorFixed()
        
        # Tests positifs (vrais problèmes techniques)
        positive_cases = [
            "Mon PC ne s'allume plus depuis hier, la carte graphique fait du bruit",
            "J'ai des artefacts sur l'écran, ma RTX 3080 crash",
            "Depuis que j'ai reçu mon PC, la carte graphique surchauffe",
            "Ma carte graphique ne fonctionne plus, écran noir au démarrage"
        ]
        
        # Tests négatifs (questions commerciales)
        negative_cases = [
            "Quel est le prix de la carte graphique RTX 4080 ?",
            "Quelle carte graphique recommandez-vous pour du gaming ?",
            "La RTX 4070 est-elle disponible en stock ?",
            "Quelle est la différence entre RTX 4060 et RTX 4070 ?"
        ]
        
        print("\n✅ CAS POSITIFS (problèmes techniques):")
        positive_success = 0
        for i, case in enumerate(positive_cases, 1):
            result = detector.detect(case)
            is_detected = result['is_uc_263']
            status = "✅ DÉTECTÉ" if is_detected else "❌ MANQUÉ"
            print(f"{i}. {status} - {case[:50]}...")
            print(f"   Confiance: {result['confidence']:.1%}")
            if is_detected:
                positive_success += 1
        
        print("\n❌ CAS NÉGATIFS (questions commerciales):")
        negative_success = 0
        for i, case in enumerate(negative_cases, 1):
            result = detector.detect(case)
            is_detected = result['is_uc_263']
            status = "✅ REJETÉ" if not is_detected else "❌ FAUX POSITIF"
            print(f"{i}. {status} - {case[:50]}...")
            print(f"   Confiance: {result['confidence']:.1%}")
            if not is_detected:
                negative_success += 1
        
        # Calcul des métriques
        positive_accuracy = positive_success / len(positive_cases)
        negative_accuracy = negative_success / len(negative_cases)
        overall_accuracy = (positive_success + negative_success) / (len(positive_cases) + len(negative_cases))
        
        print(f"\n📊 RÉSULTATS UC_263:")
        print(f"   Positifs: {positive_success}/{len(positive_cases)} ({positive_accuracy:.1%})")
        print(f"   Négatifs: {negative_success}/{len(negative_cases)} ({negative_accuracy:.1%})")
        print(f"   Global: {overall_accuracy:.1%}")
        
        return {
            "positive_accuracy": positive_accuracy,
            "negative_accuracy": negative_accuracy,
            "overall_accuracy": overall_accuracy,
            "status": "✅ SUCCÈS" if overall_accuracy >= 0.9 else "❌ ÉCHEC"
        }
        
    except Exception as e:
        print(f"❌ Erreur test UC_263: {str(e)}")
        return {"status": "❌ ERREUR", "error": str(e)}

def test_odoo_checker():
    """Test du vérificateur Odoo"""
    print("\n🧪 TEST VÉRIFICATEUR ODOO")
    print("=" * 30)
    
    try:
        from integrations.odoo_checker import OdooChecker
        
        checker = OdooChecker()
        
        test_cases = [
            {
                "user_id": "client_test_1",
                "message": "Ma carte graphique ne fonctionne plus",
                "expected": "Check Odoo effectué"
            },
            {
                "user_id": "client_test_2", 
                "message": "Où en est ma commande ?",
                "expected": "Check Odoo effectué"
            }
        ]
        
        success_count = 0
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. Test: {case['user_id']}")
            print(f"   Message: {case['message']}")
            
            try:
                context = checker.check_order_context(case['user_id'], case['message'])
                print(f"   Résultat: ✅ {case['expected']}")
                print(f"   Commande: {'✅ Trouvée' if context.get('has_order') else '❌ Non trouvée'}")
                print(f"   Escalade: {'🚨 OUI' if context.get('needs_escalation') else '❌ NON'}")
                success_count += 1
                
            except Exception as e:
                print(f"   Erreur: ❌ {str(e)}")
        
        success_rate = success_count / len(test_cases)
        print(f"\n📊 RÉSULTATS ODOO:")
        print(f"   Succès: {success_count}/{len(test_cases)} ({success_rate:.1%})")
        
        return {
            "success_rate": success_rate,
            "status": "✅ SUCCÈS" if success_rate >= 0.5 else "❌ ÉCHEC"
        }
        
    except Exception as e:
        print(f"❌ Erreur test Odoo: {str(e)}")
        return {"status": "❌ ERREUR", "error": str(e)}

def test_improved_uc_detector():
    """Test du détecteur UC amélioré"""
    print("\n🧪 TEST DÉTECTEUR UC AMÉLIORÉ")
    print("=" * 35)
    
    try:
        from core.improved_uc_detector import ImprovedUCDetector
        
        detector = ImprovedUCDetector()
        
        test_cases = [
            {
                "message": "Ma carte graphique RTX 4080 ne s'allume plus",
                "expected_uc": "UC_263",
                "description": "Problème technique GPU"
            },
            {
                "message": "Où en est ma commande ?",
                "expected_uc": "UC_336", 
                "description": "Demande de statut"
            },
            {
                "message": "Quand vais-je recevoir mon PC ?",
                "expected_uc": "UC_337",
                "description": "Demande de délai"
            },
            {
                "message": "J'ai besoin du numéro de suivi",
                "expected_uc": "UC_421",
                "description": "Demande de tracking"
            }
        ]
        
        correct_detections = 0
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. {case['description']}")
            print(f"   Message: {case['message']}")
            
            result = detector.detect(case['message'])
            detected_uc = result.get('uc_detected', 'UNKNOWN')
            confidence = result.get('confidence', 0)
            
            is_correct = detected_uc == case['expected_uc']
            status = "✅ CORRECT" if is_correct else "❌ INCORRECT"
            print(f"   Résultat: {status}")
            print(f"   UC: {detected_uc} (attendu: {case['expected_uc']})")
            print(f"   Confiance: {confidence:.1%}")
            print(f"   Escalade: {'🚨 OUI' if result.get('needs_escalation') else '❌ NON'}")
            
            if is_correct:
                correct_detections += 1
        
        accuracy = correct_detections / len(test_cases)
        print(f"\n📊 RÉSULTATS DÉTECTEUR AMÉLIORÉ:")
        print(f"   Précision: {correct_detections}/{len(test_cases)} ({accuracy:.1%})")
        
        return {
            "accuracy": accuracy,
            "status": "✅ SUCCÈS" if accuracy >= 0.75 else "❌ ÉCHEC"
        }
        
    except Exception as e:
        print(f"❌ Erreur test détecteur amélioré: {str(e)}")
        return {"status": "❌ ERREUR", "error": str(e)}

def test_contextual_response_engine():
    """Test du moteur de réponses contextuelles"""
    print("\n🧪 TEST MOTEUR RÉPONSES CONTEXTUELLES")
    print("=" * 45)
    
    try:
        from core.contextual_response_engine import ContextualResponseEngine
        
        engine = ContextualResponseEngine()
        
        test_cases = [
            {
                "uc": "UC_263",
                "context": {
                    "customer_name": "Jean Dupont",
                    "has_order": True,
                    "gpu_products": [{"name": "RTX 4080"}],
                    "days_since_order": 5,
                    "priority": "HIGH"
                },
                "message": "Ma carte graphique ne fonctionne plus"
            },
            {
                "uc": "UC_336",
                "context": {
                    "customer_name": "Marie Martin",
                    "has_order": True,
                    "order_reference": "CMD-2024-001",
                    "days_since_order": 8,
                    "order_status": "en cours"
                },
                "message": "Où en est ma commande ?"
            }
        ]
        
        successful_responses = 0
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. UC: {case['uc']}")
            print(f"   Client: {case['context']['customer_name']}")
            
            result = engine.generate_response(
                case['uc'], 
                case['context'], 
                case['message']
            )
            
            has_response = bool(result.get('response'))
            is_personalized = result.get('personalization_applied', False)
            
            print(f"   Réponse: {'✅ Générée' if has_response else '❌ Manquante'}")
            print(f"   Template: {result.get('template_used', 'N/A')}")
            print(f"   Personnalisé: {'✅ OUI' if is_personalized else '❌ NON'}")
            
            if has_response and is_personalized:
                successful_responses += 1
        
        success_rate = successful_responses / len(test_cases)
        print(f"\n📊 RÉSULTATS MOTEUR RÉPONSES:")
        print(f"   Succès: {successful_responses}/{len(test_cases)} ({success_rate:.1%})")
        
        return {
            "success_rate": success_rate,
            "status": "✅ SUCCÈS" if success_rate >= 0.8 else "❌ ÉCHEC"
        }
        
    except Exception as e:
        print(f"❌ Erreur test moteur réponses: {str(e)}")
        return {"status": "❌ ERREUR", "error": str(e)}

def test_system_monitor():
    """Test du système de monitoring"""
    print("\n🧪 TEST SYSTÈME DE MONITORING")
    print("=" * 35)
    
    try:
        from monitoring.system_monitor import SystemMonitor
        
        monitor = SystemMonitor()
        
        # Simuler des requêtes
        test_requests = [
            {"uc_detected": "UC_263", "success": True, "needs_escalation": False},
            {"uc_detected": "UC_336", "success": True, "needs_escalation": False},
            {"uc_detected": "UC_337", "success": False, "error_type": "detection_error", "needs_escalation": True},
            {"uc_detected": "UC_421", "success": True, "needs_escalation": False},
            {"uc_detected": "UC_263", "success": False, "error_type": "odoo_error", "needs_escalation": True}
        ]
        
        print("Tracking des requêtes...")
        for i, request in enumerate(test_requests, 1):
            print(f"   {i}. Tracking requête {i}")
            monitor.track_request(request)
        
        # Vérifier l'état du système
        health = monitor.get_system_health()
        print(f"\n📊 ÉTAT DU SYSTÈME:")
        print(f"   Status: {health.get('status', 'UNKNOWN')}")
        print(f"   Health Score: {health.get('health_score', 0):.1%}")
        print(f"   Uptime: {health.get('uptime', 'N/A')}")
        
        return {
            "status": health.get('status', 'UNKNOWN'),
            "health_score": health.get('health_score', 0),
            "monitoring_status": "✅ ACTIF" if health.get('status') != 'no_data' else "❌ INACTIF"
        }
        
    except Exception as e:
        print(f"❌ Erreur test monitoring: {str(e)}")
        return {"status": "❌ ERREUR", "error": str(e)}

def main():
    """Test principal du système optimisé"""
    print("🚀 TEST SYSTÈME FLOWUP OPTIMISÉ")
    print("=" * 50)
    print("Version: 2.0.0 - Plan d'optimisation implémenté")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Résultats des tests
    test_results = {}
    
    # 1. Test détecteur UC_263 corrigé
    test_results["uc263_detector"] = test_uc263_detector_fixed()
    
    # 2. Test vérificateur Odoo
    test_results["odoo_checker"] = test_odoo_checker()
    
    # 3. Test détecteur UC amélioré
    test_results["improved_detector"] = test_improved_uc_detector()
    
    # 4. Test moteur de réponses contextuelles
    test_results["response_engine"] = test_contextual_response_engine()
    
    # 5. Test système de monitoring
    test_results["system_monitor"] = test_system_monitor()
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ FINAL DES TESTS")
    print("=" * 50)
    
    total_tests = len(test_results)
    successful_tests = sum(1 for result in test_results.values() 
                          if result.get('status', '').startswith('✅'))
    
    print(f"Tests exécutés: {total_tests}")
    print(f"Tests réussis: {successful_tests}")
    print(f"Taux de succès: {successful_tests/total_tests:.1%}")
    
    print("\n📋 DÉTAIL DES RÉSULTATS:")
    for test_name, result in test_results.items():
        status = result.get('status', '❌ INCONNU')
        print(f"   {test_name}: {status}")
        
        if 'accuracy' in result:
            print(f"      Précision: {result['accuracy']:.1%}")
        if 'success_rate' in result:
            print(f"      Taux de succès: {result['success_rate']:.1%}")
        if 'health_score' in result:
            print(f"      Score de santé: {result['health_score']:.1%}")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    if successful_tests < total_tests:
        print("   • Corriger les composants en échec")
        print("   • Vérifier les dépendances")
        print("   • Améliorer la robustesse")
    else:
        print("   • Système opérationnel")
        print("   • Prêt pour la production")
        print("   • Monitoring actif recommandé")
    
    # Sauvegarder les résultats
    results_file = "test_results_optimized.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests/total_tests,
            "detailed_results": test_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans: {results_file}")
    
    return test_results

if __name__ == "__main__":
    main()
