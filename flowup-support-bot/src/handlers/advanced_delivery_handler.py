# ==================== Advanced Delivery Handler (Claude Opus) ====================
# Handler spécialisé pour les problèmes de livraison - Version optimisée

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class DeliveryInfo:
    """Informations de livraison enrichies"""
    order_id: str
    tracking_number: Optional[str]
    carrier: Optional[str]
    estimated_date: Optional[datetime]
    current_location: Optional[str]
    delivery_address: str
    address_issues: List[str]

class AdvancedDeliveryHandler:
    """Handler spécialisé pour les problèmes de livraison - Version Claude Opus"""
    
    def __init__(self, odoo_integration=None, ups_tracker=None):
        self.odoo = odoo_integration
        self.ups_tracker = ups_tracker
        self.carriers = {
            "UPS": r"1Z[A-Z0-9]{16}",
            "Colissimo": r"\d{2}[A-Z]{2}\d{9}[A-Z]{2}",
            "DHL": r"\d{10,}",
            "Chronopost": r"[A-Z]{2}\d{9}[A-Z]{2}"
        }
        
        # Patterns pour détection avancée
        self.delivery_patterns = {
            "PACKAGE_MISSING": [
                r"pas reçu", r"jamais arrivé", r"perdu", 
                r"pas livré", r"introuvable", r"manque"
            ],
            "ADDRESS_CHANGE": [
                r"changement.*adresse", r"nouvelle adresse",
                r"déménagé", r"mauvaise adresse", r"changer.*adresse"
            ],
            "DELIVERY_ESTIMATE": [
                r"quand.*recevoir", r"estimation", 
                r"délai", r"combien.*temps", r"livraison"
            ],
            "TRACKING_ISSUE": [
                r"suivi", r"tracking", r"numéro.*suivi", r"où.*colis"
            ],
            "DELAY_EXCEEDED": [
                r"1 mois", r"2 semaine", r"toujours pas", r"aucune nouvelle",
                r"délai.*dépassé", r"retard"
            ]
        }
        
        # Mots-clés d'escalade
        self.escalation_keywords = [
            "urgent", "rapidement", "immédiatement", "au plus vite",
            "inadmissible", "scandaleux", "marre", "assez",
            "remboursement", "échange", "retour", "défectueux"
        ]
    
    def handle(self, ticket_message: str, context: Dict) -> Dict:
        """
        Traite spécifiquement les problèmes de livraison avec logique avancée
        """
        result = {
            "actions": [],
            "data": {},
            "escalate": False,
            "priority": "MEDIUM",
            "response_template": "delivery_general",
            "confidence": 0.8
        }
        
        # Détecter le type de problème
        delivery_issue = self._identify_issue(ticket_message)
        result["data"]["issue_type"] = delivery_issue
        
        # Extraire les informations de tracking
        tracking_info = self._extract_tracking_info(ticket_message)
        if tracking_info:
            result["data"]["tracking"] = tracking_info
            result["actions"].append(f"CHECK_TRACKING_{tracking_info['carrier']}")
            result["response_template"] = "delivery_tracking"
        
        # Vérifier les délais
        if context.get("order_date"):
            days_elapsed = self._calculate_business_days(context["order_date"])
            result["data"]["days_elapsed"] = days_elapsed
            
            if days_elapsed > 12:
                result["escalate"] = True
                result["priority"] = "URGENT"
                result["actions"].append("ESCALATE_DELAY_EXCEEDED")
                result["response_template"] = "delivery_delay_exceeded"
            elif days_elapsed > 8:
                result["priority"] = "HIGH"
                result["response_template"] = "delivery_delay_warning"
        
        # Gérer les problèmes d'adresse
        if delivery_issue == "ADDRESS_CHANGE":
            address_info = self._extract_address(ticket_message)
            if address_info:
                result["data"]["new_address"] = address_info
                result["actions"].append("UPDATE_DELIVERY_ADDRESS")
                result["priority"] = "HIGH"
                result["response_template"] = "delivery_address_change"
        
        # Colis perdu/non reçu
        elif delivery_issue == "PACKAGE_MISSING":
            result["escalate"] = True
            result["priority"] = "URGENT"
            result["actions"].extend([
                "OPEN_CARRIER_INVESTIGATION",
                "PREPARE_REPLACEMENT_SHIPMENT",
                "NOTIFY_LOGISTICS_MANAGER"
            ])
            result["response_template"] = "delivery_missing_package"
            
        # Demande d'estimation
        elif delivery_issue == "DELIVERY_ESTIMATE":
            result["actions"].append("PROVIDE_DELIVERY_TIMELINE")
            if days_elapsed and days_elapsed > 8:
                result["priority"] = "HIGH"
            result["response_template"] = "delivery_estimation"
            
        # Vérifier les mots-clés d'escalade
        if self._check_escalation_keywords(ticket_message):
            result["escalate"] = True
            result["priority"] = "URGENT"
            result["actions"].append("ESCALATE_KEYWORDS")
        
        # Calculer la confiance
        result["confidence"] = self._calculate_confidence(ticket_message, delivery_issue)
        
        return result
    
    def _identify_issue(self, message: str) -> str:
        """Identifie le type de problème de livraison avec patterns avancés"""
        message_lower = message.lower()
        
        # Vérifier les patterns par ordre de priorité
        for issue_type, pattern_list in self.delivery_patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, message_lower):
                    return issue_type
                    
        return "UNKNOWN"
    
    def _extract_tracking_info(self, message: str) -> Optional[Dict]:
        """Extrait les informations de tracking du message avec validation"""
        for carrier, pattern in self.carriers.items():
            match = re.search(pattern, message.upper())
            if match:
                return {
                    "carrier": carrier,
                    "tracking_number": match.group(0),
                    "validated": True
                }
        return None
    
    def _extract_address(self, message: str) -> Optional[str]:
        """Extrait une adresse du message avec patterns français/belges"""
        # Pattern pour détecter une adresse française/belge
        address_patterns = [
            r'(\d+\w*)\s+(\w+[\w\s]*),?\s*([A-Za-z\s-]+),?\s*(\d{4,5})',  # Standard
            r'(\d+)\s+([^,]+),\s*([^,]+),\s*(\d{5})',  # Avec virgules
            r'(\d+)\s+([^,]+)\s+(\d{5})'  # Format court
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, message)
            if match:
                if len(match.groups()) == 4:
                    return f"{match.group(1)} {match.group(2)}, {match.group(3)}, {match.group(4)}"
                elif len(match.groups()) == 3:
                    return f"{match.group(1)} {match.group(2)}, {match.group(3)}"
        
        return None
    
    def _calculate_business_days(self, order_date: datetime) -> int:
        """Calcule le nombre de jours ouvrés depuis la commande"""
        business_days = 0
        current = order_date
        today = datetime.now()
        
        while current < today:
            if current.weekday() < 5:  # Lundi-Vendredi
                business_days += 1
            current += timedelta(days=1)
            
        return business_days
    
    def _check_escalation_keywords(self, message: str) -> bool:
        """Vérifie la présence de mots-clés d'escalade"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.escalation_keywords)
    
    def _calculate_confidence(self, message: str, issue_type: str) -> float:
        """Calcule la confiance de détection"""
        confidence = 0.5  # Base
        
        # Bonus pour patterns spécifiques
        if issue_type != "UNKNOWN":
            confidence += 0.3
        
        # Bonus pour mots-clés de tracking
        tracking_keywords = ["tracking", "suivi", "numéro", "ups", "colissimo"]
        if any(keyword in message.lower() for keyword in tracking_keywords):
            confidence += 0.2
        
        # Bonus pour adresses
        if self._extract_address(message):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def generate_response(self, result: Dict, context: Dict) -> str:
        """Génère une réponse contextuelle basée sur le résultat"""
        template = result.get("response_template", "delivery_general")
        
        responses = {
            "delivery_general": self._format_general_delivery_response(),
            "delivery_tracking": self._format_tracking_response(result.get("data", {}).get("tracking")),
            "delivery_estimation": self._format_estimation_response(result.get("data", {}).get("days_elapsed")),
            "delivery_address_change": self._format_address_change_response(result.get("data", {}).get("new_address")),
            "delivery_missing_package": self._format_missing_package_response(),
            "delivery_delay_exceeded": self._format_delay_exceeded_response(result.get("data", {}).get("days_elapsed")),
            "delivery_delay_warning": self._format_delay_warning_response(result.get("data", {}).get("days_elapsed"))
        }
        
        return responses.get(template, responses["delivery_general"])
    
    def _format_general_delivery_response(self) -> str:
        """Format général pour questions de livraison"""
        return """Bonjour, je suis l'assistant automatique FlowUp.

Je vais vous aider avec votre question de livraison. Pour vous donner des informations précises, j'ai besoin de votre numéro de commande ou de suivi.

Que puis-je faire pour vous ?"""
    
    def _format_tracking_response(self, tracking_info: Dict) -> str:
        """Format pour informations de tracking"""
        if not tracking_info:
            return self._format_general_delivery_response()
        
        return f"""Bonjour, je suis l'assistant automatique FlowUp.

J'ai trouvé votre numéro de suivi {tracking_info['tracking_number']} pour {tracking_info['carrier']}.

Je vais vérifier le statut de votre colis et vous donner les informations les plus récentes."""
    
    def _format_estimation_response(self, days_elapsed: int) -> str:
        """Format pour estimation de livraison"""
        if days_elapsed and days_elapsed > 8:
            return f"""Bonjour, je suis l'assistant automatique FlowUp.

Je vois que votre commande a été passée il y a {days_elapsed} jours ouvrés. 

Je vais vérifier le statut de production et vous donner une estimation précise de livraison."""
        else:
            return """Bonjour, je suis l'assistant automatique FlowUp.

Je vais vérifier le statut de votre commande et vous donner une estimation précise de livraison."""
    
    def _format_address_change_response(self, new_address: str) -> str:
        """Format pour changement d'adresse"""
        return f"""Bonjour, je suis l'assistant automatique FlowUp.

Je comprends que vous souhaitez changer votre adresse de livraison pour : {new_address}

Je vais transmettre cette demande à notre service logistique pour mise à jour immédiate."""
    
    def _format_missing_package_response(self) -> str:
        """Format pour colis manquant"""
        return """Bonjour, je suis l'assistant automatique FlowUp.

Je comprends votre inquiétude concernant la non-réception de votre commande.

Je transfère immédiatement votre demande à notre équipe logistique qui va :
• Vérifier avec le transporteur
• Ouvrir une enquête
• Vous recontacter dans les 2 heures

Votre demande est traitée en priorité."""
    
    def _format_delay_exceeded_response(self, days_elapsed: int) -> str:
        """Format pour délai dépassé"""
        return f"""Bonjour, je suis l'assistant automatique FlowUp.

Je constate que votre commande a été passée il y a {days_elapsed} jours ouvrés, ce qui dépasse notre délai standard de 12 jours.

Je transfère IMMÉDIATEMENT votre demande à notre équipe prioritaire qui vous contactera dans les plus brefs délais.

Votre demande est traitée en urgence."""
    
    def _format_delay_warning_response(self, days_elapsed: int) -> str:
        """Format pour avertissement de délai"""
        return f"""Bonjour, je suis l'assistant automatique FlowUp.

Votre commande a été passée il y a {days_elapsed} jours ouvrés. 

Je vais vérifier le statut de production et vous donner une mise à jour précise sur les délais de livraison."""
    
    def get_escalation_priority(self, result: Dict) -> str:
        """Détermine la priorité d'escalade"""
        if result.get("escalate"):
            if result.get("priority") == "URGENT":
                return "IMMEDIATE"
            elif result.get("priority") == "HIGH":
                return "HIGH"
        return "NORMAL"
    
    def get_required_actions(self, result: Dict) -> List[str]:
        """Retourne les actions requises"""
        return result.get("actions", [])
    
    def should_escalate(self, result: Dict) -> bool:
        """Détermine si escalade nécessaire"""
        return result.get("escalate", False)
