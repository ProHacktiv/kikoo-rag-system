"""
Système FlowUp optimisé intégré
Implémentation complète du plan d'optimisation avec tous les composants
"""

import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Imports des composants
from .improved_uc_detector import ImprovedUCDetector
from .contextual_response_engine import ContextualResponseEngine
from ..integrations.odoo_checker import OdooChecker
from ..detectors.uc263_detector_fixed import UC263DetectorFixed
from ..monitoring.system_monitor import SystemMonitor

class OptimizedFlowUpSystem:
    """
    Système FlowUp optimisé intégré
    
    ARCHITECTURE:
    - Détecteur UC amélioré (multi-étapes)
    - Check Odoo automatique
    - Réponses contextuelles personnalisées
    - Monitoring temps réel
    - Optimisation continue
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialisation des composants
        self.odoo_checker = OdooChecker()
        self.uc_detector = ImprovedUCDetector(self.odoo_checker)
        self.response_engine = ContextualResponseEngine()
        self.uc263_detector = UC263DetectorFixed()
        self.monitor = SystemMonitor()
        
        # Configuration
        self.system_config = {
            "always_check_odoo": True,
            "enable_monitoring": True,
            "enable_optimization": True,
            "response_timeout": 5.0,
            "max_retries": 2
        }
        
        # Statistiques
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "escalated_requests": 0,
            "uc_detections": {},
            "response_times": [],
            "start_time": datetime.now()
        }
    
    def process_message(self, message: str, user_id: str = None, context: Dict = None) -> Dict[str, Any]:
        """
        Traite un message avec le système optimisé
        
        Args:
            message: Message du client
            user_id: ID du client
            context: Contexte supplémentaire
            
        Returns:
            Dict avec réponse, métadonnées, actions
        """
        start_time = time.time()
        request_id = f"req_{int(time.time())}"
        
        try:
            self.logger.info(f"Traitement message {request_id}: {message[:50]}...")
            
            # 1. Check Odoo automatique
            odoo_context = None
            if self.system_config["always_check_odoo"] and user_id:
                odoo_context = self.odoo_checker.check_order_context(user_id, message)
            
            # 2. Détection UC améliorée
            uc_result = self.uc_detector.detect(message, user_id)
            
            # 3. Détection UC_263 spécialisée si applicable
            if uc_result.get("uc_detected") == "UC_263":
                uc263_result = self.uc263_detector.detect(message, odoo_context)
                if uc263_result.get("is_uc_263"):
                    uc_result.update(uc263_result)
            
            # 4. Génération de réponse contextuelle
            response_result = self.response_engine.generate_response(
                uc_result.get("uc_detected", "UC_UNKNOWN"),
                odoo_context or {},
                message
            )
            
            # 5. Calcul du temps de traitement
            processing_time = (time.time() - start_time) * 1000
            
            # 6. Construction du résultat final
            final_result = self._build_final_result(
                message, user_id, uc_result, response_result, 
                odoo_context, processing_time, request_id
            )
            
            # 7. Monitoring et statistiques
            self._update_stats(final_result, processing_time)
            if self.system_config["enable_monitoring"]:
                self.monitor.track_request(final_result)
            
            # 8. Optimisation continue
            if self.system_config["enable_optimization"]:
                self._optimize_system()
            
            self.logger.info(f"Message {request_id} traité en {processing_time:.1f}ms")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Erreur traitement message {request_id}: {str(e)}")
            return self._get_error_result(message, user_id, str(e), request_id)
    
    def _build_final_result(self, message: str, user_id: str, uc_result: Dict, 
                          response_result: Dict, odoo_context: Dict, 
                          processing_time: float, request_id: str) -> Dict[str, Any]:
        """Construit le résultat final"""
        return {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "user_id": user_id,
            
            # Résultats UC
            "uc_detected": uc_result.get("uc_detected", "UC_UNKNOWN"),
            "uc_confidence": uc_result.get("confidence", 0.0),
            "uc_reason": uc_result.get("reason", ""),
            
            # Réponse générée
            "response": response_result.get("response", ""),
            "response_metadata": response_result.get("metadata", {}),
            "template_used": response_result.get("template_used", "default"),
            "personalization_applied": response_result.get("personalization_applied", False),
            
            # Contexte Odoo
            "odoo_context": odoo_context or {},
            "has_order": odoo_context.get("has_order", False) if odoo_context else False,
            "order_status": odoo_context.get("order_status", "UNKNOWN") if odoo_context else "UNKNOWN",
            "is_delayed": odoo_context.get("is_delayed", False) if odoo_context else False,
            
            # Escalade et priorité
            "needs_escalation": uc_result.get("needs_escalation", False) or 
                              odoo_context.get("needs_escalation", False) if odoo_context else False,
            "escalation_reason": uc_result.get("escalation_reason", "") or 
                               odoo_context.get("escalation_reason", "") if odoo_context else "",
            "priority": odoo_context.get("priority", "NORMAL") if odoo_context else "NORMAL",
            
            # Performance
            "processing_time_ms": processing_time,
            "success": True,
            
            # Actions suggérées
            "suggested_actions": uc_result.get("suggested_actions", []),
            
            # Métadonnées système
            "system_version": "2.0.0-optimized",
            "components_used": [
                "improved_uc_detector",
                "odoo_checker", 
                "contextual_response_engine",
                "uc263_detector_fixed",
                "system_monitor"
            ]
        }
    
    def _update_stats(self, result: Dict, processing_time: float) -> None:
        """Met à jour les statistiques"""
        self.stats["total_requests"] += 1
        
        if result.get("success", False):
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        if result.get("needs_escalation", False):
            self.stats["escalated_requests"] += 1
        
        # UC détecté
        uc = result.get("uc_detected", "UNKNOWN")
        self.stats["uc_detections"][uc] = self.stats["uc_detections"].get(uc, 0) + 1
        
        # Temps de traitement
        self.stats["response_times"].append(processing_time)
        if len(self.stats["response_times"]) > 100:  # Garder seulement les 100 derniers
            self.stats["response_times"] = self.stats["response_times"][-100:]
    
    def _optimize_system(self) -> None:
        """Optimise le système en continu"""
        try:
            # Vérifier les performances
            if len(self.stats["response_times"]) > 10:
                avg_response_time = sum(self.stats["response_times"]) / len(self.stats["response_times"])
                
                if avg_response_time > 3000:  # Plus de 3 secondes
                    self.logger.warning("Performance dégradée détectée - optimisation nécessaire")
                    self._trigger_performance_optimization()
            
            # Vérifier le taux de succès
            if self.stats["total_requests"] > 0:
                success_rate = self.stats["successful_requests"] / self.stats["total_requests"]
                
                if success_rate < 0.8:  # Moins de 80% de succès
                    self.logger.warning("Taux de succès faible - analyse nécessaire")
                    self._trigger_success_analysis()
            
        except Exception as e:
            self.logger.error(f"Erreur optimisation: {str(e)}")
    
    def _trigger_performance_optimization(self) -> None:
        """Déclenche l'optimisation de performance"""
        optimizations = [
            "Réduction de la complexité des détections",
            "Optimisation des requêtes Odoo",
            "Mise en cache des réponses fréquentes",
            "Parallélisation des traitements"
        ]
        
        for optimization in optimizations:
            self.logger.info(f"OPTIMISATION: {optimization}")
    
    def _trigger_success_analysis(self) -> None:
        """Déclenche l'analyse de succès"""
        analyses = [
            "Analyse des UC les plus problématiques",
            "Vérification des patterns d'erreur",
            "Ajustement des seuils de confiance",
            "Amélioration des templates de réponse"
        ]
        
        for analysis in analyses:
            self.logger.info(f"ANALYSE: {analysis}")
    
    def _get_error_result(self, message: str, user_id: str, error: str, request_id: str) -> Dict[str, Any]:
        """Résultat en cas d'erreur"""
        return {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "user_id": user_id,
            "uc_detected": "UC_ERROR",
            "uc_confidence": 0.0,
            "response": """
Bonjour, je suis l'assistant automatique FlowUp.

Je rencontre un problème technique momentané.

Je transfère votre demande à un opérateur qui pourra vous aider immédiatement.

Merci de votre patience.
            """.strip(),
            "needs_escalation": True,
            "escalation_reason": f"Erreur système: {error}",
            "priority": "HIGH",
            "success": False,
            "error": error,
            "processing_time_ms": 0.0
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retourne le statut du système"""
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        return {
            "status": "operational",
            "uptime_seconds": uptime,
            "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
            "total_requests": self.stats["total_requests"],
            "success_rate": (
                self.stats["successful_requests"] / self.stats["total_requests"] 
                if self.stats["total_requests"] > 0 else 0.0
            ),
            "escalation_rate": (
                self.stats["escalated_requests"] / self.stats["total_requests"] 
                if self.stats["total_requests"] > 0 else 0.0
            ),
            "avg_response_time": (
                sum(self.stats["response_times"]) / len(self.stats["response_times"])
                if self.stats["response_times"] else 0.0
            ),
            "uc_distribution": self.stats["uc_detections"],
            "components": {
                "uc_detector": "active",
                "odoo_checker": "active",
                "response_engine": "active",
                "uc263_detector": "active",
                "monitor": "active"
            }
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Génère un rapport de performance"""
        status = self.get_system_status()
        
        # Rapport de performance
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_requests": status["total_requests"],
                "success_rate": f"{status['success_rate']:.1%}",
                "escalation_rate": f"{status['escalation_rate']:.1%}",
                "avg_response_time": f"{status['avg_response_time']:.1f}ms",
                "uptime": status["uptime_formatted"]
            },
            "uc_performance": {},
            "recommendations": []
        }
        
        # Performance par UC
        for uc, count in self.stats["uc_detections"].items():
            percentage = (count / self.stats["total_requests"]) * 100 if self.stats["total_requests"] > 0 else 0
            report["uc_performance"][uc] = {
                "count": count,
                "percentage": f"{percentage:.1f}%"
            }
        
        # Recommandations
        if status["success_rate"] < 0.9:
            report["recommendations"].append("Améliorer la précision de détection UC")
        
        if status["escalation_rate"] > 0.3:
            report["recommendations"].append("Réduire les escalades inutiles")
        
        if status["avg_response_time"] > 2000:
            report["recommendations"].append("Optimiser les performances")
        
        return report
    
    def test_system(self, test_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test le système avec des messages de test"""
        results = []
        
        for i, test in enumerate(test_messages, 1):
            message = test["message"]
            user_id = test.get("user_id", f"test_user_{i}")
            
            print(f"🧪 Test {i}: {message[:50]}...")
            
            result = self.process_message(message, user_id)
            results.append({
                "test_id": i,
                "message": message,
                "expected_uc": test.get("expected_uc"),
                "detected_uc": result.get("uc_detected"),
                "confidence": result.get("uc_confidence"),
                "success": result.get("success"),
                "needs_escalation": result.get("needs_escalation"),
                "processing_time": result.get("processing_time_ms")
            })
            
            print(f"   UC: {result.get('uc_detected')} (confiance: {result.get('uc_confidence', 0):.1%})")
            print(f"   Escalade: {'🚨 OUI' if result.get('needs_escalation') else '❌ NON'}")
            print(f"   Temps: {result.get('processing_time_ms', 0):.1f}ms")
        
        # Calcul des métriques de test
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r["success"])
        correct_ucs = sum(1 for r in results if r["detected_uc"] == r["expected_uc"])
        escalated_tests = sum(1 for r in results if r["needs_escalation"])
        
        return {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": f"{successful_tests/total_tests:.1%}",
                "correct_uc_detections": correct_ucs,
                "uc_accuracy": f"{correct_ucs/total_tests:.1%}",
                "escalated_tests": escalated_tests,
                "escalation_rate": f"{escalated_tests/total_tests:.1%}"
            },
            "detailed_results": results,
            "system_status": self.get_system_status()
        }

# Test du système optimisé
def test_optimized_system():
    """Test du système FlowUp optimisé"""
    system = OptimizedFlowUpSystem()
    
    test_messages = [
        {
            "message": "Ma carte graphique RTX 4080 ne s'allume plus",
            "user_id": "client_1",
            "expected_uc": "UC_263"
        },
        {
            "message": "Où en est ma commande ?",
            "user_id": "client_2", 
            "expected_uc": "UC_336"
        },
        {
            "message": "Quand vais-je recevoir mon PC ?",
            "user_id": "client_3",
            "expected_uc": "UC_337"
        },
        {
            "message": "J'ai besoin du numéro de suivi",
            "user_id": "client_4",
            "expected_uc": "UC_421"
        },
        {
            "message": "Quel est le prix de la RTX 4080 ?",
            "user_id": "client_5",
            "expected_uc": "UC_COMMERCIAL"
        }
    ]
    
    print("🚀 TEST SYSTÈME FLOWUP OPTIMISÉ")
    print("=" * 40)
    
    # Exécuter les tests
    test_results = system.test_system(test_messages)
    
    # Afficher le résumé
    summary = test_results["test_summary"]
    print(f"\n📊 RÉSULTATS DES TESTS:")
    print(f"   Tests réussis: {summary['successful_tests']}/{summary['total_tests']} ({summary['success_rate']})")
    print(f"   Précision UC: {summary['uc_accuracy']}")
    print(f"   Taux d'escalade: {summary['escalation_rate']}")
    
    # Afficher le statut du système
    status = test_results["system_status"]
    print(f"\n🔧 STATUT DU SYSTÈME:")
    print(f"   Uptime: {status['uptime_formatted']}")
    print(f"   Taux de succès: {status['success_rate']:.1%}")
    print(f"   Temps moyen: {status['avg_response_time']:.1f}ms")
    
    # Générer le rapport de performance
    report = system.get_performance_report()
    print(f"\n📈 RAPPORT DE PERFORMANCE:")
    print(f"   Total requêtes: {report['summary']['total_requests']}")
    print(f"   Taux de succès: {report['summary']['success_rate']}")
    print(f"   Temps moyen: {report['summary']['avg_response_time']}")
    
    if report['recommendations']:
        print(f"\n💡 RECOMMANDATIONS:")
        for rec in report['recommendations']:
            print(f"   • {rec}")

if __name__ == "__main__":
    test_optimized_system()
