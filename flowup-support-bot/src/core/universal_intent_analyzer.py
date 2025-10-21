"""
Analyseur d'intent unifié pour tous les tickets FlowUp.
Basé sur l'analyse des 50 tickets réels.
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class Category(Enum):
    DELIVERY = "DELIVERY"
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    SALES = "SALES"
    UNKNOWN = "UNKNOWN"

class Priority(Enum):
    IMMEDIATE = "IMMEDIATE"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"

@dataclass
class IntentResult:
    category: Category
    uc_id: int
    confidence: float
    priority: Priority
    keywords_matched: List[str]
    requires_escalation: bool
    escalation_reason: Optional[str]

class UniversalIntentAnalyzer:
    """Analyseur d'intent unifié pour tous les tickets"""
    
    def __init__(self):
        # Mapping UC basé sur l'analyse des 50 tickets
        self.UC_MAPPINGS = {
            # DELIVERY - 19 tickets
            421: {"keywords": ["suivi", "tracking", "numéro", "suivre", "où est"], "category": Category.DELIVERY},
            337: {"keywords": ["délai", "quand", "recevoir", "estimation", "livraison", "semaine"], "category": Category.DELIVERY},
            426: {"keywords": ["pas reçu", "manque", "incomplet", "seulement", "uniquement"], "category": Category.DELIVERY},
            423: {"keywords": ["mauvais", "erreur", "adresse", "livraison"], "category": Category.DELIVERY},
            432: {"keywords": ["endommagé", "cassé", "abîmé", "livraison"], "category": Category.DELIVERY},
            
            # HARDWARE - 13 tickets
            263: {"keywords": ["carte graphique", "gpu", "rtx", "geforce", "graphique"], "category": Category.HARDWARE},
            269: {"keywords": ["surchauffe", "température", "ventilateur", "refroidissement", "chaud"], "category": Category.HARDWARE},
            267: {"keywords": ["alimentation", "démarre pas", "s'allume pas", "power"], "category": Category.HARDWARE},
            270: {"keywords": ["périphérique", "clavier", "souris", "usb"], "category": Category.HARDWARE},
            284: {"keywords": ["écran", "moniteur", "affichage", "noir"], "category": Category.HARDWARE},
            
            # SOFTWARE - 2 tickets
            277: {"keywords": ["réseau", "internet", "wifi", "connexion", "web"], "category": Category.SOFTWARE},
            272: {"keywords": ["windows", "système", "écran bleu", "activation", "os"], "category": Category.SOFTWARE},
            289: {"keywords": ["logiciel", "application", "programme"], "category": Category.SOFTWARE},
            273: {"keywords": ["pilote", "driver", "mise à jour"], "category": Category.SOFTWARE},
            286: {"keywords": ["bug", "erreur", "plantage"], "category": Category.SOFTWARE},
            
            # SALES - 11 tickets
            336: {"keywords": ["précommande", "disponibilité", "stock", "commander"], "category": Category.SALES},
            365: {"keywords": ["commande", "achat", "facture", "paiement"], "category": Category.SALES},
            335: {"keywords": ["prix", "coût", "tarif", "devis"], "category": Category.SALES},
            306: {"keywords": ["remboursement", "rembourser", "retour", "échange"], "category": Category.SALES},
            368: {"keywords": ["garantie", "sav", "réparation"], "category": Category.SALES},
        }
        
        # Triggers d'escalade basés sur l'analyse
        self.ESCALATION_TRIGGERS = {
            "immediate": [
                "remboursement", "rembourser", "échange", "retour",
                "1 mois", "3 semaines", "urgence", "avocat", "juridique"
            ],
            "high": [
                "pas reçu", "ne démarre pas", "carte graphique", "défaut",
                "ne marche pas", "problème", "dysfonctionnement"
            ],
            "normal": [
                "délai", "suivi", "question", "information", "quand"
            ]
        }
        
        # Patterns critiques identifiés
        self.CRITICAL_PATTERNS = {
            "ESCALADE_IMMEDIATE": [
                "remboursement", "rembourser", "échange", "retour",
                "1 mois", "3 semaines", "urgence", "avocat"
            ],
            "CHECK_ODOO_REQUIRED": [
                "ma commande", "mon pc", "j'ai commandé", "j'ai acheté"
            ],
            "MISSING_ITEMS": [
                "seulement", "uniquement", "manque", "pas tout reçu"
            ]
        }
    
    def analyze(self, message: str, ticket_context: Dict = None) -> IntentResult:
        """
        Analyse complète du message
        
        Args:
            message: Message du client
            ticket_context: Contexte du ticket (user_id, previous_tickets, etc.)
            
        Returns:
            IntentResult avec catégorie, UC, priorité, etc.
        """
        message_lower = message.lower()
        
        # 1. Détection de catégorie et UC
        category, uc_id, keywords = self._detect_category_and_uc(message_lower)
        
        # 2. Calcul de priorité
        priority = self._calculate_priority(message_lower, category)
        
        # 3. Vérification escalade
        requires_escalation, reason = self._check_escalation(message_lower, category, ticket_context)
        
        # 4. Calcul confidence
        confidence = self._calculate_confidence(keywords, message_lower)
        
        return IntentResult(
            category=category,
            uc_id=uc_id,
            confidence=confidence,
            priority=priority,
            keywords_matched=keywords,
            requires_escalation=requires_escalation,
            escalation_reason=reason
        )
    
    def _detect_category_and_uc(self, message: str) -> Tuple[Category, int, List[str]]:
        """Détecte la catégorie et l'UC basé sur les mots-clés"""
        best_score = 0
        best_uc = None
        best_category = Category.UNKNOWN
        matched_keywords = []
        
        for uc_id, config in self.UC_MAPPINGS.items():
            score = 0
            keywords_found = []
            
            for keyword in config["keywords"]:
                if keyword in message:
                    score += 1
                    keywords_found.append(keyword)
            
            # Bonus pour les patterns critiques
            if any(pattern in message for pattern in self.CRITICAL_PATTERNS["CHECK_ODOO_REQUIRED"]):
                if config["category"] in [Category.DELIVERY, Category.SALES]:
                    score += 2
            
            if any(pattern in message for pattern in self.CRITICAL_PATTERNS["MISSING_ITEMS"]):
                if config["category"] == Category.DELIVERY:
                    score += 3
            
            if score > best_score:
                best_score = score
                best_uc = uc_id
                best_category = config["category"]
                matched_keywords = keywords_found
        
        # Si aucun UC trouvé, analyser par patterns généraux
        if best_uc is None:
            best_category = self._fallback_category_detection(message)
            best_uc = 0
        
        return best_category, best_uc, matched_keywords
    
    def _calculate_priority(self, message: str, category: Category) -> Priority:
        """Calcule la priorité basée sur le message et la catégorie"""
        
        # Check immediate triggers
        for trigger in self.ESCALATION_TRIGGERS["immediate"]:
            if trigger in message:
                return Priority.IMMEDIATE
        
        # Check high priority
        for trigger in self.ESCALATION_TRIGGERS["high"]:
            if trigger in message:
                return Priority.HIGH
        
        # Catégories spécifiques
        if category == Category.SALES and "remboursement" in message:
            return Priority.IMMEDIATE
        
        if category == Category.DELIVERY and any(word in message for word in ["pas reçu", "manque", "incomplet"]):
            return Priority.HIGH
        
        if category == Category.HARDWARE and any(word in message for word in ["ne démarre pas", "ne marche pas"]):
            return Priority.HIGH
        
        return Priority.NORMAL
    
    def _check_escalation(self, message: str, category: Category, context: Dict) -> Tuple[bool, Optional[str]]:
        """Vérifie si escalade nécessaire"""
        
        # Remboursement = toujours escalade
        if "remboursement" in message or "rembourser" in message:
            return True, "Demande de remboursement"
        
        # Échange = toujours escalade
        if "échange" in message or "retour" in message:
            return True, "Demande d'échange/retour"
        
        # Délai dépassé (plus de 12 jours)
        if context and context.get("days_since_order", 0) > 12:
            return True, "Délai légal dépassé"
        
        # Problème non résolu après plusieurs tentatives
        if context and context.get("previous_tickets", 0) > 0:
            return True, "Problème récurrent"
        
        # Mentions juridiques
        if any(word in message for word in ["avocat", "juridique", "plainte"]):
            return True, "Mention juridique"
        
        # Urgence exprimée
        if any(word in message for word in ["urgent", "urgence", "immédiatement"]):
            return True, "Urgence exprimée"
        
        return False, None
    
    def _calculate_confidence(self, keywords: List[str], message: str) -> float:
        """Calcule le score de confiance"""
        if not keywords:
            return 0.5
        
        # Plus de mots-clés = plus de confiance
        base_confidence = min(0.7 + (len(keywords) * 0.1), 1.0)
        
        # Bonus si message structuré
        if len(message.split()) > 10:
            base_confidence = min(base_confidence + 0.1, 1.0)
        
        # Bonus pour patterns spécifiques
        if any(pattern in message for pattern in self.CRITICAL_PATTERNS["CHECK_ODOO_REQUIRED"]):
            base_confidence = min(base_confidence + 0.1, 1.0)
        
        return base_confidence
    
    def _fallback_category_detection(self, message: str) -> Category:
        """Détection de catégorie en fallback"""
        category_keywords = {
            Category.DELIVERY: ["livraison", "colis", "expédition", "suivi", "commande"],
            Category.HARDWARE: ["pc", "ordinateur", "composant", "écran", "carte"],
            Category.SOFTWARE: ["windows", "logiciel", "bug", "erreur", "système"],
            Category.SALES: ["commande", "prix", "facture", "paiement", "achat"]
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in message for kw in keywords):
                return category
        
        return Category.UNKNOWN
    
    def get_escalation_stats(self, tickets: List[Dict]) -> Dict:
        """Calcule les statistiques d'escalade pour un batch de tickets"""
        stats = {
            "total": len(tickets),
            "escalated": 0,
            "by_reason": {},
            "by_priority": {}
        }
        
        for ticket in tickets:
            result = self.analyze(ticket["message"], ticket.get("context", {}))
            
            if result.requires_escalation:
                stats["escalated"] += 1
                
                reason = result.escalation_reason or "Unknown"
                if reason not in stats["by_reason"]:
                    stats["by_reason"][reason] = 0
                stats["by_reason"][reason] += 1
                
                priority = result.priority.value
                if priority not in stats["by_priority"]:
                    stats["by_priority"][priority] = 0
                stats["by_priority"][priority] += 1
        
        return stats
