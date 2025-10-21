"""
FlowUp Chatbot Enhanced - Version avec détection UC_336 spécialisée
Système optimisé pour les réponses aux UC avec détecteur UC_336
"""

import yaml
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Imports des détecteurs spécialisés
from ..detectors.uc336_detector import UC336Detector
from ..templates.uc336_responses import generate_uc336_response, validate_response_safety

logger = logging.getLogger(__name__)

class Category(Enum):
    DELIVERY = "DELIVERY"
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    SALES = "SALES"
    RETURNS = "RETURNS"
    BILLING = "BILLING"
    RGB = "RGB"
    GAMING = "GAMING"
    CUSTOMER_CARE = "CUSTOMER_CARE"
    UNKNOWN = "UNKNOWN"

class Priority(Enum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class UCDetection:
    """Détection d'un UC"""
    uc_id: str
    name: str
    confidence: float
    keywords_found: List[str]
    category: Category
    priority: Priority
    auto_escalate: bool

@dataclass
class ChatbotResponse:
    """Réponse du chatbot"""
    content: str
    uc_detected: UCDetection
    requires_escalation: bool
    escalation_reason: Optional[str] = None

class EnhancedFlowUpChatbot:
    """Chatbot FlowUp avec détection UC_336 spécialisée"""
    
    def __init__(self, config_path: str = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/uc_mappings.yaml"):
        self.config_path = config_path
        self.uc_definitions = {}
        self.response_templates = {}
        self.business_rules = {}
        
        # Détecteur spécialisé UC_336
        self.uc336_detector = UC336Detector()
        
        # Charger la configuration
        self._load_configuration()
        
        # Patterns critiques
        self.critical_keywords = [
            "remboursement", "rembourser", "échange", "retour", "avocat",
            "1 mois", "2 semaine", "toujours pas", "aucune nouvelle",
            "urgent", "rapidement", "inadmissible", "scandaleux"
        ]
    
    def _load_configuration(self):
        """Charge la configuration YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.uc_definitions = config.get('uc_definitions', {})
            self.response_templates = config.get('response_templates', {})
            self.business_rules = config.get('business_rules', {})
            
            logger.info(f"Configuration chargée: {len(self.uc_definitions)} UC")
            
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            self.uc_definitions = {}
    
    def process_message(self, message: str, context: Dict = None) -> ChatbotResponse:
        """
        Traite un message avec détection UC_336 prioritaire
        
        Args:
            message: Message du client
            context: Contexte additionnel (optionnel)
        
        Returns:
            ChatbotResponse: Réponse générée
        """
        context = context or {}
        message_lower = message.lower()
        
        # 1. DÉTECTION UC_336 EN PRIORITÉ
        uc336_result = self.uc336_detector.detect(message, context.get("order_data"))
        
        if uc336_result["is_uc_336"]:
            logger.info(f"UC_336 détecté avec confiance {uc336_result['confidence']:.1f}%")
            
            # Générer réponse UC_336 spécialisée
            response_content = generate_uc336_response(uc336_result, context.get("order_data"))
            
            # Valider la sécurité de la réponse
            if not validate_response_safety(response_content):
                logger.warning("Réponse UC_336 contient des promesses dangereuses")
                response_content = self._get_safe_fallback_response()
            
            return ChatbotResponse(
                content=response_content,
                uc_detected=UCDetection(
                    uc_id="UC_336",
                    name="Statut précommande",
                    confidence=uc336_result["confidence"] / 100,
                    keywords_found=[],
                    category=Category.SALES,
                    priority=Priority.HIGH if uc336_result["should_escalate"] else Priority.MEDIUM,
                    auto_escalate=uc336_result["should_escalate"]
                ),
                requires_escalation=uc336_result["should_escalate"],
                escalation_reason="Retard dépassé" if uc336_result["should_escalate"] else None
            )
        
        # 2. DÉTECTION UC STANDARD (si pas UC_336)
        uc_detection = self._detect_primary_uc(message_lower)
        
        # 3. Vérifier l'escalade
        requires_escalation, escalation_reason = self._check_escalation(message_lower, context)
        
        # 4. Générer la réponse
        response_content = self._generate_response(uc_detection, context, requires_escalation)
        
        return ChatbotResponse(
            content=response_content,
            uc_detected=uc_detection,
            requires_escalation=requires_escalation,
            escalation_reason=escalation_reason
        )
    
    def _detect_primary_uc(self, message: str) -> UCDetection:
        """Détecte l'UC principal dans le message (méthode standard)"""
        best_uc = None
        best_confidence = 0.0
        best_keywords = []
        
        for uc_id, config in self.uc_definitions.items():
            confidence = 0.0
            keywords_found = []
            
            # Vérifier chaque mot-clé
            for keyword in config.get('keywords', []):
                if keyword in message:
                    confidence += 0.3
                    keywords_found.append(keyword)
            
            # Bonus pour patterns spécifiques
            if self._check_specific_patterns(message, uc_id):
                confidence += 0.2
            
            # Garder le meilleur UC
            if confidence > best_confidence:
                best_confidence = confidence
                best_uc = uc_id
                best_keywords = keywords_found
        
        # Créer l'objet de détection
        if best_uc and best_confidence >= 0.3:
            config = self.uc_definitions[best_uc]
            return UCDetection(
                uc_id=best_uc,
                name=config.get('name', ''),
                confidence=min(best_confidence, 1.0),
                keywords_found=best_keywords,
                category=Category(config.get('category', 'UNKNOWN')),
                priority=Priority(config.get('priority', 'MEDIUM')),
                auto_escalate=config.get('auto_escalate', False)
            )
        else:
            # UC inconnu
            return UCDetection(
                uc_id="UC_Unknown",
                name="Demande non identifiée",
                confidence=0.5,
                keywords_found=[],
                category=Category.UNKNOWN,
                priority=Priority.LOW,
                auto_escalate=False
            )
    
    def _check_specific_patterns(self, message: str, uc_id: str) -> bool:
        """Vérifie les patterns spécifiques pour certains UC"""
        specific_patterns = {
            "UC_337": [r"combien.*temps", r"quand.*recevoir", r"estimation.*livraison"],
            "UC_263": [r"carte.*graphique.*problème", r"gpu.*défaillant", r"artefacts.*écran"],
            "UC_269": [r"surchauffe.*cpu", r"température.*élevée", r"ventilateur.*bruit"],
            "UC_426": [r"pas.*reçu", r"jamais.*arrivé", r"colis.*perdu"],
            "UC_313": [r"garantie.*échange", r"remboursement.*défaut", r"cassé.*remplacement"]
        }
        
        patterns = specific_patterns.get(uc_id, [])
        return any(re.search(pattern, message) for pattern in patterns)
    
    def _check_escalation(self, message: str, context: Dict) -> Tuple[bool, Optional[str]]:
        """Vérifie si escalade nécessaire"""
        # Vérifier les mots-clés critiques
        for keyword in self.critical_keywords:
            if keyword in message:
                return True, f"Mot-clé critique: {keyword}"
        
        # Vérifier les délais
        if context.get("order_date"):
            days_elapsed = self._calculate_business_days(context["order_date"])
            max_delay = self.business_rules.get("max_delivery_delay", 12)
            if days_elapsed > max_delay:
                return True, f"Délai dépassé: {days_elapsed} jours"
        
        return False, None
    
    def _calculate_business_days(self, order_date: datetime) -> int:
        """Calcule les jours ouvrés depuis la commande"""
        business_days = 0
        current = order_date
        today = datetime.now()
        
        while current < today:
            if current.weekday() < 5:  # Lundi-Vendredi
                business_days += 1
            current += timedelta(days=1)
        
        return business_days
    
    def _generate_response(self, uc_detection: UCDetection, context: Dict, requires_escalation: bool) -> str:
        """Génère la réponse finale"""
        # Greeting obligatoire
        response_parts = [self.response_templates.get("greeting", "Bonjour, je suis l'assistant automatique FlowUp.")]
        
        # Réponse spécifique à l'UC
        uc_response = self._get_uc_response(uc_detection, context)
        response_parts.append(uc_response)
        
        # Escalade si nécessaire
        if requires_escalation:
            escalation_response = self._get_escalation_response(uc_detection.priority)
            response_parts.append(escalation_response)
        
        # Clôture
        response_parts.append("Puis-je vous aider pour autre chose ?")
        
        return "\n\n".join(response_parts)
    
    def _get_uc_response(self, uc_detection: UCDetection, context: Dict) -> str:
        """Récupère la réponse spécifique à l'UC"""
        uc_id = uc_detection.uc_id
        
        # Récupérer le template
        template = self.response_templates.get(uc_id, {})
        
        if not template:
            return self._get_fallback_response(uc_detection)
        
        # Sélectionner le bon template selon le contexte
        if uc_id == "UC_337":  # Estimation livraison
            if context.get("days_elapsed", 0) > 12:
                return template.get("delay_exceeded", "")
            elif context.get("order_id"):
                return template.get("within_delay", "")
            else:
                return template.get("no_context", "")
        
        # Template par défaut
        return template.get("template", template.get("diagnostic", ""))
    
    def _get_fallback_response(self, uc_detection: UCDetection) -> str:
        """Réponse de fallback par catégorie"""
        fallback_responses = {
            Category.DELIVERY: "Je vais vérifier le statut de votre commande et vous donner des informations précises sur la livraison.",
            Category.HARDWARE: "Je comprends votre problème technique. Notre équipe va vous aider à le résoudre rapidement.",
            Category.SOFTWARE: "Je vais vous assister avec ce problème logiciel. Notre support technique va vous guider.",
            Category.SALES: "Je vais traiter votre demande commerciale et vous apporter les informations nécessaires.",
            Category.RETURNS: "Je comprends votre demande de retour/échange. Notre équipe SAV va vous contacter.",
            Category.BILLING: "Je vais vérifier les informations de paiement et vous aider avec votre demande.",
            Category.RGB: "Je vais vous aider avec votre problème d'éclairage RGB.",
            Category.GAMING: "Je vais vous assister avec ce problème de performance gaming.",
            Category.CUSTOMER_CARE: "Je vais traiter votre demande et vous apporter l'aide nécessaire.",
            Category.UNKNOWN: "Je vais analyser votre demande et vous apporter une réponse personnalisée."
        }
        
        return fallback_responses.get(uc_detection.category, "Je vais traiter votre demande.")
    
    def _get_escalation_response(self, priority: Priority) -> str:
        """Récupère la réponse d'escalade"""
        escalation_templates = self.response_templates.get("escalation", {})
        
        if priority == Priority.URGENT:
            return escalation_templates.get("urgent", """
🚨 **ESCALADE URGENTE - PRIORITÉ ABSOLUE**
Votre situation a été classée comme critique.
Un responsable va vous contacter dans l'heure.
""")
        else:
            return escalation_templates.get("standard", """
⚠️ **ESCALADE PRIORITAIRE**
Votre demande nécessite une attention particulière et a été transmise 
à notre équipe spécialisée qui vous contactera dans les plus brefs délais.
""")
    
    def _get_safe_fallback_response(self) -> str:
        """Réponse de fallback sécurisée"""
        return """
Bonjour, je suis l'assistant automatique FlowUp.

Je vais traiter votre demande et vous apporter une réponse personnalisée.

Puis-je vous aider pour autre chose ?
"""
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du chatbot"""
        return {
            "uc_definitions_loaded": len(self.uc_definitions),
            "response_templates_loaded": len(self.response_templates),
            "business_rules_loaded": len(self.business_rules),
            "critical_keywords": len(self.critical_keywords),
            "uc336_detector_available": True
        }
    
    def validate_uc(self, uc_id: str) -> bool:
        """Valide qu'un UC existe"""
        return uc_id in self.uc_definitions
    
    def get_uc_info(self, uc_id: str) -> Dict:
        """Récupère les informations d'un UC"""
        return self.uc_definitions.get(uc_id, {})
    
    def test_uc336_detection(self, message: str, order_data: Dict = None) -> str:
        """Test de détection UC_336 pour debug"""
        result = self.uc336_detector.detect(message, order_data)
        return self.uc336_detector.get_detection_summary(message, order_data)
