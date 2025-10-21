"""
Système de monitoring et amélioration continue
Implémentation du plan d'optimisation avec métriques temps réel
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

@dataclass
class PerformanceMetrics:
    """Métriques de performance du système"""
    timestamp: datetime
    uc_detection_accuracy: float
    response_time_ms: float
    escalation_rate: float
    client_satisfaction: float
    odoo_check_success: float
    rag_relevance: float
    total_requests: int
    successful_requests: int

@dataclass
class ErrorPattern:
    """Pattern d'erreur détecté"""
    pattern_type: str
    frequency: int
    affected_ucs: List[str]
    suggested_fix: str
    severity: str

class SystemMonitor:
    """
    Système de monitoring et amélioration continue
    
    FONCTIONNALITÉS:
    - Métriques temps réel
    - Détection de patterns d'erreur
    - Optimisation automatique
    - Dashboard de performance
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Stockage des métriques
        self.metrics_history = deque(maxlen=1000)  # 1000 dernières métriques
        self.error_patterns = []
        self.performance_trends = {}
        
        # Configuration des seuils
        self.thresholds = {
            "uc_detection_accuracy": {"warning": 0.7, "critical": 0.5},
            "response_time_ms": {"warning": 2000, "critical": 5000},
            "escalation_rate": {"warning": 0.3, "critical": 0.5},
            "client_satisfaction": {"warning": 3.5, "critical": 3.0},
            "odoo_check_success": {"warning": 0.8, "critical": 0.6},
            "rag_relevance": {"warning": 0.6, "critical": 0.4}
        }
        
        # Compteurs en temps réel
        self.real_time_counters = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "escalated_requests": 0,
            "uc_detections": defaultdict(int),
            "response_times": deque(maxlen=100),
            "error_types": defaultdict(int)
        }
    
    def track_request(self, request_data: Dict[str, Any]) -> None:
        """Enregistre une requête pour monitoring"""
        start_time = time.time()
        
        try:
            # Incrémenter compteurs
            self.real_time_counters["total_requests"] += 1
            
            # Tracker UC détecté
            uc_detected = request_data.get("uc_detected", "UNKNOWN")
            self.real_time_counters["uc_detections"][uc_detected] += 1
            
            # Tracker temps de réponse
            response_time = (time.time() - start_time) * 1000  # en ms
            self.real_time_counters["response_times"].append(response_time)
            
            # Tracker succès/échec
            if request_data.get("success", False):
                self.real_time_counters["successful_requests"] += 1
            else:
                self.real_time_counters["failed_requests"] += 1
                error_type = request_data.get("error_type", "unknown")
                self.real_time_counters["error_types"][error_type] += 1
            
            # Tracker escalades
            if request_data.get("needs_escalation", False):
                self.real_time_counters["escalated_requests"] += 1
            
            # Générer métriques si nécessaire
            if self._should_generate_metrics():
                self._generate_performance_metrics()
            
        except Exception as e:
            self.logger.error(f"Erreur tracking requête: {str(e)}")
    
    def _should_generate_metrics(self) -> bool:
        """Détermine si on doit générer des métriques"""
        # Générer métriques toutes les 10 requêtes ou toutes les 5 minutes
        return (
            self.real_time_counters["total_requests"] % 10 == 0 or
            self._time_since_last_metrics() > 300  # 5 minutes
        )
    
    def _time_since_last_metrics(self) -> float:
        """Temps écoulé depuis les dernières métriques"""
        if not self.metrics_history:
            return float('inf')
        
        last_metrics = self.metrics_history[-1]
        return (datetime.now() - last_metrics.timestamp).total_seconds()
    
    def _generate_performance_metrics(self) -> None:
        """Génère les métriques de performance"""
        try:
            # Calculer les métriques
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                uc_detection_accuracy=self._calculate_uc_accuracy(),
                response_time_ms=self._calculate_avg_response_time(),
                escalation_rate=self._calculate_escalation_rate(),
                client_satisfaction=self._calculate_satisfaction(),
                odoo_check_success=self._calculate_odoo_success(),
                rag_relevance=self._calculate_rag_relevance(),
                total_requests=self.real_time_counters["total_requests"],
                successful_requests=self.real_time_counters["successful_requests"]
            )
            
            # Ajouter à l'historique
            self.metrics_history.append(metrics)
            
            # Vérifier les seuils
            self._check_thresholds(metrics)
            
            # Détecter les patterns d'erreur
            self._detect_error_patterns()
            
            self.logger.info(f"Métriques générées: UC accuracy={metrics.uc_detection_accuracy:.1%}")
            
        except Exception as e:
            self.logger.error(f"Erreur génération métriques: {str(e)}")
    
    def _calculate_uc_accuracy(self) -> float:
        """Calcule la précision de détection UC"""
        total = self.real_time_counters["total_requests"]
        successful = self.real_time_counters["successful_requests"]
        
        if total == 0:
            return 0.0
        
        return successful / total
    
    def _calculate_avg_response_time(self) -> float:
        """Calcule le temps de réponse moyen"""
        response_times = list(self.real_time_counters["response_times"])
        
        if not response_times:
            return 0.0
        
        return sum(response_times) / len(response_times)
    
    def _calculate_escalation_rate(self) -> float:
        """Calcule le taux d'escalade"""
        total = self.real_time_counters["total_requests"]
        escalated = self.real_time_counters["escalated_requests"]
        
        if total == 0:
            return 0.0
        
        return escalated / total
    
    def _calculate_satisfaction(self) -> float:
        """Calcule la satisfaction client (simulé)"""
        # Simulation basée sur le taux de succès
        success_rate = self._calculate_uc_accuracy()
        
        # Mapping: 0.5 -> 3.0, 0.8 -> 4.0, 1.0 -> 5.0
        return 3.0 + (success_rate - 0.5) * 2.0 if success_rate >= 0.5 else 3.0
    
    def _calculate_odoo_success(self) -> float:
        """Calcule le taux de succès Odoo"""
        # Simulation basée sur les erreurs
        total_errors = sum(self.real_time_counters["error_types"].values())
        total_requests = self.real_time_counters["total_requests"]
        
        if total_requests == 0:
            return 1.0
        
        success_rate = 1.0 - (total_errors / total_requests)
        return max(0.0, success_rate)
    
    def _calculate_rag_relevance(self) -> float:
        """Calcule la pertinence RAG"""
        # Simulation basée sur le taux de succès
        return self._calculate_uc_accuracy() * 0.9  # Légèrement inférieur à l'accuracy UC
    
    def _check_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Vérifie les seuils de performance"""
        alerts = []
        
        for metric_name, threshold in self.thresholds.items():
            value = getattr(metrics, metric_name)
            warning_threshold = threshold["warning"]
            critical_threshold = threshold["critical"]
            
            if value <= critical_threshold:
                alerts.append({
                    "type": "CRITICAL",
                    "metric": metric_name,
                    "value": value,
                    "threshold": critical_threshold,
                    "message": f"CRITIQUE: {metric_name} = {value:.1%} (seuil: {critical_threshold:.1%})"
                })
            elif value <= warning_threshold:
                alerts.append({
                    "type": "WARNING",
                    "metric": metric_name,
                    "value": value,
                    "threshold": warning_threshold,
                    "message": f"ATTENTION: {metric_name} = {value:.1%} (seuil: {warning_threshold:.1%})"
                })
        
        # Traiter les alertes
        for alert in alerts:
            self.logger.warning(alert["message"])
            self._handle_alert(alert)
    
    def _handle_alert(self, alert: Dict[str, Any]) -> None:
        """Traite une alerte de performance"""
        if alert["type"] == "CRITICAL":
            # Actions critiques
            self._trigger_critical_actions(alert)
        elif alert["type"] == "WARNING":
            # Actions préventives
            self._trigger_warning_actions(alert)
    
    def _trigger_critical_actions(self, alert: Dict[str, Any]) -> None:
        """Déclenche les actions critiques"""
        metric = alert["metric"]
        
        if metric == "uc_detection_accuracy":
            self._suggest_uc_detector_fix()
        elif metric == "response_time_ms":
            self._suggest_performance_optimization()
        elif metric == "client_satisfaction":
            self._suggest_satisfaction_improvement()
    
    def _trigger_warning_actions(self, alert: Dict[str, Any]) -> None:
        """Déclenche les actions préventives"""
        # Actions préventives moins urgentes
        self.logger.info(f"Action préventive pour {alert['metric']}")
    
    def _suggest_uc_detector_fix(self) -> None:
        """Suggère des corrections pour le détecteur UC"""
        suggestions = [
            "Vérifier les patterns de détection UC_263",
            "Ajuster les seuils de confiance",
            "Analyser les faux positifs récents",
            "Mettre à jour les mots-clés"
        ]
        
        for suggestion in suggestions:
            self.logger.info(f"SUGGESTION: {suggestion}")
    
    def _suggest_performance_optimization(self) -> None:
        """Suggère des optimisations de performance"""
        suggestions = [
            "Optimiser les requêtes Odoo",
            "Mettre en cache les réponses fréquentes",
            "Réduire la complexité des détections",
            "Paralléliser les traitements"
        ]
        
        for suggestion in suggestions:
            self.logger.info(f"OPTIMISATION: {suggestion}")
    
    def _suggest_satisfaction_improvement(self) -> None:
        """Suggère des améliorations de satisfaction"""
        suggestions = [
            "Améliorer la personnalisation des réponses",
            "Réduire les escalades inutiles",
            "Optimiser les templates de réponse",
            "Améliorer la détection d'intent"
        ]
        
        for suggestion in suggestions:
            self.logger.info(f"AMÉLIORATION: {suggestion}")
    
    def _detect_error_patterns(self) -> None:
        """Détecte les patterns d'erreur"""
        error_types = dict(self.real_time_counters["error_types"])
        
        for error_type, count in error_types.items():
            if count > 5:  # Seuil d'alerte
                pattern = ErrorPattern(
                    pattern_type=error_type,
                    frequency=count,
                    affected_ucs=self._get_affected_ucs(error_type),
                    suggested_fix=self._get_suggested_fix(error_type),
                    severity="HIGH" if count > 10 else "MEDIUM"
                )
                
                self.error_patterns.append(pattern)
                self.logger.warning(f"Pattern d'erreur détecté: {error_type} ({count} occurrences)")
    
    def _get_affected_ucs(self, error_type: str) -> List[str]:
        """Détermine les UC affectés par un type d'erreur"""
        # Mapping simplifié
        error_uc_mapping = {
            "detection_error": ["UC_263", "UC_336", "UC_337"],
            "odoo_error": ["UC_336", "UC_337", "UC_421"],
            "response_error": ["ALL"]
        }
        
        return error_uc_mapping.get(error_type, ["UNKNOWN"])
    
    def _get_suggested_fix(self, error_type: str) -> str:
        """Génère une suggestion de correction"""
        fixes = {
            "detection_error": "Vérifier les patterns de détection et ajuster les seuils",
            "odoo_error": "Vérifier la connectivité Odoo et les credentials",
            "response_error": "Vérifier les templates de réponse et la logique de génération"
        }
        
        return fixes.get(error_type, "Analyser les logs pour identifier la cause")
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Retourne le dashboard de performance"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest_metrics = self.metrics_history[-1]
        
        return {
            "timestamp": latest_metrics.timestamp.isoformat(),
            "performance": {
                "uc_detection_accuracy": {
                    "current": latest_metrics.uc_detection_accuracy,
                    "threshold": self.thresholds["uc_detection_accuracy"],
                    "status": self._get_status(latest_metrics.uc_detection_accuracy, 
                                             self.thresholds["uc_detection_accuracy"])
                },
                "response_time_ms": {
                    "current": latest_metrics.response_time_ms,
                    "threshold": self.thresholds["response_time_ms"],
                    "status": self._get_status(latest_metrics.response_time_ms, 
                                             self.thresholds["response_time_ms"], reverse=True)
                },
                "escalation_rate": {
                    "current": latest_metrics.escalation_rate,
                    "threshold": self.thresholds["escalation_rate"],
                    "status": self._get_status(latest_metrics.escalation_rate, 
                                             self.thresholds["escalation_rate"])
                },
                "client_satisfaction": {
                    "current": latest_metrics.client_satisfaction,
                    "threshold": self.thresholds["client_satisfaction"],
                    "status": self._get_status(latest_metrics.client_satisfaction, 
                                             self.thresholds["client_satisfaction"])
                }
            },
            "trends": self._calculate_trends(),
            "error_patterns": [asdict(pattern) for pattern in self.error_patterns[-5:]],
            "recommendations": self._generate_recommendations()
        }
    
    def _get_status(self, value: float, threshold: Dict, reverse: bool = False) -> str:
        """Détermine le statut d'une métrique"""
        if reverse:
            # Pour les métriques où plus c'est mieux (temps de réponse)
            if value <= threshold["critical"]:
                return "CRITICAL"
            elif value <= threshold["warning"]:
                return "WARNING"
            else:
                return "OK"
        else:
            # Pour les métriques où plus c'est mieux
            if value <= threshold["critical"]:
                return "CRITICAL"
            elif value <= threshold["warning"]:
                return "WARNING"
            else:
                return "OK"
    
    def _calculate_trends(self) -> Dict[str, str]:
        """Calcule les tendances de performance"""
        if len(self.metrics_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent = self.metrics_history[-1]
        previous = self.metrics_history[-2]
        
        trends = {}
        
        # Tendance précision UC
        uc_trend = "stable"
        if recent.uc_detection_accuracy > previous.uc_detection_accuracy + 0.05:
            uc_trend = "improving"
        elif recent.uc_detection_accuracy < previous.uc_detection_accuracy - 0.05:
            uc_trend = "declining"
        
        trends["uc_detection"] = uc_trend
        
        # Tendance temps de réponse
        response_trend = "stable"
        if recent.response_time_ms < previous.response_time_ms - 100:
            response_trend = "improving"
        elif recent.response_time_ms > previous.response_time_ms + 100:
            response_trend = "declining"
        
        trends["response_time"] = response_trend
        
        return trends
    
    def _generate_recommendations(self) -> List[str]:
        """Génère des recommandations d'amélioration"""
        recommendations = []
        
        if not self.metrics_history:
            return recommendations
        
        latest = self.metrics_history[-1]
        
        # Recommandations basées sur les métriques
        if latest.uc_detection_accuracy < 0.8:
            recommendations.append("Améliorer la détection UC - analyser les faux positifs")
        
        if latest.response_time_ms > 2000:
            recommendations.append("Optimiser les performances - réduire les temps de réponse")
        
        if latest.escalation_rate > 0.3:
            recommendations.append("Réduire les escalades - améliorer la résolution automatique")
        
        if latest.client_satisfaction < 4.0:
            recommendations.append("Améliorer la satisfaction client - personnaliser les réponses")
        
        return recommendations
    
    def get_system_health(self) -> Dict[str, Any]:
        """Retourne l'état de santé du système"""
        dashboard = self.get_performance_dashboard()
        
        if dashboard["status"] == "no_data":
            return {"status": "no_data", "message": "Aucune donnée disponible"}
        
        # Calculer le score de santé global
        health_score = self._calculate_health_score(dashboard)
        
        return {
            "status": "healthy" if health_score > 0.8 else "degraded" if health_score > 0.6 else "critical",
            "health_score": health_score,
            "dashboard": dashboard,
            "uptime": self._calculate_uptime(),
            "last_update": datetime.now().isoformat()
        }
    
    def _calculate_health_score(self, dashboard: Dict) -> float:
        """Calcule le score de santé global"""
        performance = dashboard["performance"]
        score = 0.0
        total_metrics = 0
        
        for metric_name, metric_data in performance.items():
            if metric_data["status"] == "OK":
                score += 1.0
            elif metric_data["status"] == "WARNING":
                score += 0.7
            elif metric_data["status"] == "CRITICAL":
                score += 0.3
            
            total_metrics += 1
        
        return score / total_metrics if total_metrics > 0 else 0.0
    
    def _calculate_uptime(self) -> str:
        """Calcule le temps de fonctionnement"""
        if not self.metrics_history:
            return "0 minutes"
        
        first_metric = self.metrics_history[0]
        uptime_seconds = (datetime.now() - first_metric.timestamp).total_seconds()
        
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{hours}h {minutes}m"

# Test du système de monitoring
def test_system_monitor():
    """Test du système de monitoring"""
    monitor = SystemMonitor()
    
    # Simuler des requêtes
    test_requests = [
        {"uc_detected": "UC_263", "success": True, "needs_escalation": False},
        {"uc_detected": "UC_336", "success": True, "needs_escalation": False},
        {"uc_detected": "UC_337", "success": False, "error_type": "detection_error", "needs_escalation": True},
        {"uc_detected": "UC_421", "success": True, "needs_escalation": False},
        {"uc_detected": "UC_263", "success": False, "error_type": "odoo_error", "needs_escalation": True}
    ]
    
    print("🧪 TEST SYSTÈME DE MONITORING")
    print("=" * 35)
    
    # Tracker les requêtes
    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. Tracking requête {i}")
        monitor.track_request(request)
        
        # Afficher les métriques si générées
        if i % 5 == 0:
            dashboard = monitor.get_performance_dashboard()
            if dashboard["status"] != "no_data":
                print(f"   Dashboard généré: {len(monitor.metrics_history)} métriques")
    
    # Afficher l'état final
    health = monitor.get_system_health()
    print(f"\n📊 ÉTAT DU SYSTÈME:")
    print(f"   Status: {health['status']}")
    print(f"   Health Score: {health.get('health_score', 0):.1%}")
    print(f"   Uptime: {health.get('uptime', 'N/A')}")
    
    if health.get('dashboard', {}).get('performance'):
        perf = health['dashboard']['performance']
        print(f"\n📈 PERFORMANCE:")
        for metric, data in perf.items():
            print(f"   {metric}: {data['current']:.1%} ({data['status']})")

if __name__ == "__main__":
    test_system_monitor()
