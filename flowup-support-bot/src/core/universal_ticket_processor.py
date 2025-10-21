"""
Processeur principal unifié pour tous les tickets FlowUp.
Intégration complète avec l'analyse des 50 tickets.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from .universal_intent_analyzer import UniversalIntentAnalyzer, Category, Priority
from .universal_response_generator import UniversalResponseGenerator

class UniversalTicketProcessor:
    """Processeur principal unifié pour tous les tickets"""
    
    def __init__(self, config: Dict = None, odoo_client=None):
        self.intent_analyzer = UniversalIntentAnalyzer()
        self.response_generator = UniversalResponseGenerator(odoo_client)
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)
        
        # Statistiques de performance
        self.stats = {
            "total_processed": 0,
            "category_correct": 0,
            "uc_correct": 0,
            "escalated": 0,
            "by_category": {},
            "by_priority": {}
        }
    
    def _default_config(self) -> Dict:
        """Configuration par défaut basée sur l'analyse des 50 tickets"""
        return {
            "always_present_bot": True,
            "always_check_odoo": True,
            "legal_delay_days": 12,
            "escalation_response_time": "2 heures",
            "auto_escalate_refunds": True,
            "confidence_threshold": 0.6,
            "max_auto_attempts": 3
        }
    
    def process(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un ticket complet
        
        Args:
            ticket: {
                "id": str,
                "message": str,
                "user_id": str,
                "category_expected": str (optional),
                "uc_expected": int (optional),
                "context": dict (optional)
            }
        
        Returns:
            {
                "ticket_id": str,
                "detected_category": str,
                "detected_uc": int,
                "confidence": float,
                "response": str,
                "escalate": bool,
                "escalation_reason": str,
                "priority": str,
                "actions_taken": list,
                "performance": dict,
                "processing_time": float
            }
        """
        start_time = datetime.now()
        
        try:
            # 1. Analyse du message
            intent_result = self.intent_analyzer.analyze(
                message=ticket["message"],
                ticket_context=ticket.get("context", {})
            )
            
            self.logger.info(f"Ticket {ticket['id']} - Detected: {intent_result.category.value}, UC: {intent_result.uc_id}")
            
            # 2. Enrichir le contexte avec les données utilisateur
            enriched_context = self._enrich_context(ticket, intent_result)
            
            # 3. Générer la réponse
            response = self.response_generator.generate(intent_result, enriched_context)
            
            # 4. Logger les actions
            actions = self._log_actions(intent_result, enriched_context)
            
            # 5. Calculer les métriques de performance
            performance = self._calculate_performance(ticket, intent_result)
            
            # 6. Construire le résultat
            result = {
                "ticket_id": ticket["id"],
                "detected_category": intent_result.category.value,
                "detected_uc": intent_result.uc_id,
                "confidence": intent_result.confidence,
                "response": response,
                "escalate": intent_result.requires_escalation,
                "escalation_reason": intent_result.escalation_reason,
                "priority": intent_result.priority.value,
                "actions_taken": actions,
                "performance": performance,
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
            # 7. Mettre à jour les statistiques
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing ticket {ticket['id']}: {e}")
            return self._generate_error_response(ticket["id"], str(e))
    
    def _enrich_context(self, ticket: Dict, intent) -> Dict:
        """Enrichit le contexte avec les données métier"""
        context = ticket.copy()
        
        # Ajouter les infos de timing
        if "date" in ticket:
            try:
                ticket_date = datetime.fromisoformat(ticket["date"])
                context["days_since_ticket"] = (datetime.now() - ticket_date).days
            except:
                context["days_since_ticket"] = 0
        
        # Ajouter l'historique si disponible
        context["has_previous_tickets"] = "previous_ticket" in ticket.get("context", {})
        
        # Ajouter les infos intent
        context["intent"] = intent
        
        # Ajouter les règles métier
        context["business_rules"] = self._get_business_rules(intent)
        
        return context
    
    def _get_business_rules(self, intent) -> Dict:
        """Applique les règles métier selon la catégorie"""
        rules = {
            "legal_delay_days": 12,
            "escalation_required": intent.requires_escalation,
            "priority": intent.priority.value,
            "auto_resolution_attempts": 0
        }
        
        # Règles spécifiques par catégorie
        if intent.category.value == "DELIVERY":
            rules.update({
                "check_odoo_required": True,
                "tracking_available": False,
                "delay_calculation": True
            })
        elif intent.category.value == "HARDWARE":
            rules.update({
                "technical_solutions": True,
                "escalation_after_attempts": 3
            })
        elif intent.category.value == "SALES":
            rules.update({
                "check_odoo_required": True,
                "commercial_support": True
            })
        
        return rules
    
    def _log_actions(self, intent, context: Dict) -> List[str]:
        """Enregistre les actions prises"""
        actions = ["bot_presented"]
        
        # Actions selon la catégorie
        if intent.category.value in ["DELIVERY", "SALES"]:
            actions.append("odoo_checked")
        
        if intent.requires_escalation:
            actions.append(f"escalated_{intent.priority.value}")
        
        # Actions spécifiques par UC
        delivery_ucs = [337, 421, 426, 423, 432]
        hardware_ucs = [263, 267, 269, 270, 284]
        software_ucs = [277, 272, 289, 273, 286]
        
        if intent.uc_id in delivery_ucs:
            actions.append("delivery_status_provided")
        elif intent.uc_id in hardware_ucs:
            actions.append("technical_solution_provided")
        elif intent.uc_id in software_ucs:
            actions.append("software_solution_provided")
        
        # Actions selon les règles métier
        if context.get("business_rules", {}).get("check_odoo_required"):
            actions.append("odoo_integration_used")
        
        if context.get("business_rules", {}).get("technical_solutions"):
            actions.append("knowledge_base_searched")
        
        return actions
    
    def _calculate_performance(self, ticket: Dict, intent) -> Dict:
        """Calcule les métriques de performance"""
        perf = {
            "category_match": False,
            "uc_match": False,
            "confidence": intent.confidence,
            "escalation_correct": False,
            "response_quality": 0
        }
        
        # Vérifier la correspondance catégorie
        if "category_expected" in ticket:
            perf["category_match"] = ticket["category_expected"] == intent.category.value
        
        # Vérifier la correspondance UC
        if "uc_expected" in ticket:
            perf["uc_match"] = ticket["uc_expected"] == intent.uc_id
        
        # Vérifier l'escalade
        if "escalate_expected" in ticket:
            perf["escalation_correct"] = ticket["escalate_expected"] == intent.requires_escalation
        
        # Score de qualité de réponse
        response_quality = 0
        if intent.confidence > 0.8:
            response_quality += 40
        if intent.uc_id > 0:  # UC détecté
            response_quality += 30
        if not intent.requires_escalation:  # Résolution automatique
            response_quality += 30
        
        perf["response_quality"] = response_quality
        
        # Score global
        score = 0
        if perf["category_match"]:
            score += 40
        if perf["uc_match"]:
            score += 40
        score += int(perf["confidence"] * 20)
        
        perf["score"] = score
        return perf
    
    def _update_stats(self, result: Dict):
        """Met à jour les statistiques globales"""
        self.stats["total_processed"] += 1
        
        if result["performance"]["category_match"]:
            self.stats["category_correct"] += 1
        
        if result["performance"]["uc_match"]:
            self.stats["uc_correct"] += 1
        
        if result["escalate"]:
            self.stats["escalated"] += 1
        
        # Par catégorie
        cat = result["detected_category"]
        if cat not in self.stats["by_category"]:
            self.stats["by_category"][cat] = 0
        self.stats["by_category"][cat] += 1
        
        # Par priorité
        priority = result["priority"]
        if priority not in self.stats["by_priority"]:
            self.stats["by_priority"][priority] = 0
        self.stats["by_priority"][priority] += 1
    
    def _generate_error_response(self, ticket_id: str, error: str) -> Dict:
        """Génère une réponse d'erreur"""
        return {
            "ticket_id": ticket_id,
            "detected_category": "UNKNOWN",
            "detected_uc": 0,
            "confidence": 0.0,
            "response": "Je rencontre un problème technique. Je transfère votre demande à un opérateur.",
            "escalate": True,
            "escalation_reason": f"Erreur technique: {error}",
            "priority": "HIGH",
            "actions_taken": ["error_occurred"],
            "performance": {"score": 0},
            "processing_time": 0.0
        }
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de performance"""
        if self.stats["total_processed"] == 0:
            return self.stats
        
        return {
            **self.stats,
            "category_accuracy": self.stats["category_correct"] / self.stats["total_processed"],
            "uc_accuracy": self.stats["uc_correct"] / self.stats["total_processed"],
            "escalation_rate": self.stats["escalated"] / self.stats["total_processed"]
        }
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.stats = {
            "total_processed": 0,
            "category_correct": 0,
            "uc_correct": 0,
            "escalated": 0,
            "by_category": {},
            "by_priority": {}
        }
    
    def process_batch(self, tickets: List[Dict]) -> List[Dict]:
        """Traite un batch de tickets"""
        results = []
        
        for ticket in tickets:
            result = self.process(ticket)
            results.append(result)
        
        return results
    
    def get_performance_report(self) -> Dict:
        """Génère un rapport de performance détaillé"""
        stats = self.get_stats()
        
        report = {
            "summary": {
                "total_processed": stats["total_processed"],
                "category_accuracy": f"{stats['category_accuracy']:.1%}",
                "uc_accuracy": f"{stats['uc_accuracy']:.1%}",
                "escalation_rate": f"{stats['escalation_rate']:.1%}"
            },
            "distribution": {
                "by_category": stats["by_category"],
                "by_priority": stats["by_priority"]
            },
            "recommendations": self._generate_recommendations(stats)
        }
        
        return report
    
    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """Génère des recommandations basées sur les statistiques"""
        recommendations = []
        
        if stats["category_accuracy"] < 0.8:
            recommendations.append("Améliorer la détection de catégorie - ajouter plus de mots-clés")
        
        if stats["uc_accuracy"] < 0.7:
            recommendations.append("Affiner le mapping UC - analyser les faux positifs")
        
        if stats["escalation_rate"] > 0.5:
            recommendations.append("Réduire le taux d'escalade - améliorer les solutions automatiques")
        
        if not recommendations:
            recommendations.append("Performance excellente - maintenir la configuration actuelle")
        
        return recommendations
