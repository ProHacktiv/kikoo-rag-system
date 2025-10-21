"""
Delivery Handler Final - Version Optimisée
Basé sur le meilleur des deux handlers précédents
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class DeliveryInfo:
    """Informations de livraison"""
    order_id: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    days_elapsed: int = 0
    delivery_address: Optional[str] = None
    address_issues: List[str] = None

class DeliveryHandlerFinal:
    """Handler de livraison optimisé et final"""
    
    def __init__(self, odoo_client=None, ups_tracker=None):
        self.odoo_client = odoo_client
        self.ups_tracker = ups_tracker
        
        # Patterns de transporteurs
        self.carrier_patterns = {
            "UPS": r"1Z[A-Z0-9]{16}",
            "Colissimo": r"\d{2}[A-Z]{2}\d{9}[A-Z]{2}",
            "DHL": r"\d{10,}",
            "Chronopost": r"[A-Z]{2}\d{9}[A-Z]{2}"
        }
        
        # Patterns de problèmes de livraison
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
    
    def handle(self, message: str, context: Dict = None) -> Dict:
        """
        Traite un message de livraison
        
        Args:
            message: Message du client
            context: Contexte additionnel
        
        Returns:
            Dict: Résultat du traitement
        """
        context = context or {}
        message_lower = message.lower()
        
        result = {
            "issue_type": "UNKNOWN",
            "delivery_info": None,
            "actions": [],
            "escalate": False,
            "priority": "MEDIUM",
            "response_template": "delivery_general"
        }
        
        # 1. Identifier le type de problème
        issue_type = self._identify_issue(message_lower)
        result["issue_type"] = issue_type
        
        # 2. Extraire les informations de livraison
        delivery_info = self._extract_delivery_info(message, context)
        result["delivery_info"] = delivery_info
        
        # 3. Déterminer les actions
        actions = self._determine_actions(issue_type, delivery_info, context)
        result["actions"] = actions
        
        # 4. Vérifier l'escalade
        escalate, reason = self._check_escalation(message_lower, delivery_info, context)
        result["escalate"] = escalate
        result["escalation_reason"] = reason
        
        # 5. Déterminer la priorité
        priority = self._determine_priority(issue_type, delivery_info, escalate)
        result["priority"] = priority
        
        # 6. Sélectionner le template de réponse
        template = self._select_response_template(issue_type, escalate, priority)
        result["response_template"] = template
        
        return result
    
    def _identify_issue(self, message: str) -> str:
        """Identifie le type de problème de livraison"""
        for issue_type, patterns in self.delivery_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return issue_type
        return "UNKNOWN"
    
    def _extract_delivery_info(self, message: str, context: Dict) -> DeliveryInfo:
        """Extrait les informations de livraison"""
        info = DeliveryInfo()
        
        # Extraire le numéro de tracking
        tracking_info = self._extract_tracking_info(message)
        if tracking_info:
            info.tracking_number = tracking_info["tracking_number"]
            info.carrier = tracking_info["carrier"]
        
        # Extraire l'adresse
        address = self._extract_address(message)
        if address:
            info.delivery_address = address
        
        # Calculer les jours écoulés
        if context.get("order_date"):
            info.days_elapsed = self._calculate_business_days(context["order_date"])
        
        # ID de commande
        if context.get("order_id"):
            info.order_id = context["order_id"]
        
        return info
    
    def _extract_tracking_info(self, message: str) -> Optional[Dict]:
        """Extrait les informations de tracking"""
        for carrier, pattern in self.carrier_patterns.items():
            match = re.search(pattern, message.upper())
            if match:
                return {
                    "carrier": carrier,
                    "tracking_number": match.group(0)
                }
        return None
    
    def _extract_address(self, message: str) -> Optional[str]:
        """Extrait une adresse du message"""
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
    
    def _determine_actions(self, issue_type: str, delivery_info: DeliveryInfo, context: Dict) -> List[str]:
        """Détermine les actions à effectuer"""
        actions = []
        
        if issue_type == "PACKAGE_MISSING":
            actions.extend([
                "OPEN_CARRIER_INVESTIGATION",
                "PREPARE_REPLACEMENT_SHIPMENT",
                "NOTIFY_LOGISTICS_MANAGER"
            ])
        elif issue_type == "ADDRESS_CHANGE":
            actions.append("UPDATE_DELIVERY_ADDRESS")
        elif issue_type == "DELIVERY_ESTIMATE":
            actions.append("PROVIDE_DELIVERY_TIMELINE")
        elif issue_type == "TRACKING_ISSUE":
            actions.append("CHECK_TRACKING_STATUS")
        
        # Actions basées sur les délais
        if delivery_info.days_elapsed > 12:
            actions.append("ESCALATE_DELAY_EXCEEDED")
        elif delivery_info.days_elapsed > 8:
            actions.append("WARN_DELAY_APPROACHING")
        
        return actions
    
    def _check_escalation(self, message: str, delivery_info: DeliveryInfo, context: Dict) -> Tuple[bool, Optional[str]]:
        """Vérifie si escalade nécessaire"""
        # Vérifier les mots-clés d'escalade
        for keyword in self.escalation_keywords:
            if keyword in message:
                return True, f"Mot-clé d'escalade: {keyword}"
        
        # Vérifier les délais
        if delivery_info.days_elapsed > 12:
            return True, f"Délai dépassé: {delivery_info.days_elapsed} jours"
        
        # Vérifier les problèmes critiques
        if delivery_info.issue_type == "PACKAGE_MISSING":
            return True, "Colis manquant"
        
        return False, None
    
    def _determine_priority(self, issue_type: str, delivery_info: DeliveryInfo, escalate: bool) -> str:
        """Détermine la priorité"""
        if escalate:
            return "URGENT"
        elif delivery_info.days_elapsed > 8:
            return "HIGH"
        elif issue_type in ["PACKAGE_MISSING", "ADDRESS_CHANGE"]:
            return "HIGH"
        else:
            return "MEDIUM"
    
    def _select_response_template(self, issue_type: str, escalate: bool, priority: str) -> str:
        """Sélectionne le template de réponse"""
        if escalate:
            return "delivery_escalation"
        elif issue_type == "PACKAGE_MISSING":
            return "delivery_missing_package"
        elif issue_type == "ADDRESS_CHANGE":
            return "delivery_address_change"
        elif issue_type == "DELIVERY_ESTIMATE":
            return "delivery_estimation"
        elif issue_type == "TRACKING_ISSUE":
            return "delivery_tracking"
        else:
            return "delivery_general"
    
    def generate_response(self, result: Dict, context: Dict = None) -> str:
        """Génère une réponse basée sur le résultat"""
        template = result.get("response_template", "delivery_general")
        delivery_info = result.get("delivery_info")
        context = context or {}
        
        # Templates de réponse
        templates = {
            "delivery_general": self._format_general_response(),
            "delivery_estimation": self._format_estimation_response(delivery_info),
            "delivery_tracking": self._format_tracking_response(delivery_info),
            "delivery_address_change": self._format_address_change_response(delivery_info),
            "delivery_missing_package": self._format_missing_package_response(),
            "delivery_escalation": self._format_escalation_response(result.get("priority", "MEDIUM"))
        }
        
        return templates.get(template, templates["delivery_general"])
    
    def _format_general_response(self) -> str:
        """Format général pour questions de livraison"""
        return """Je vais vous aider avec votre question de livraison. Pour vous donner des informations précises, j'ai besoin de votre numéro de commande ou de suivi.

Que puis-je faire pour vous ?"""
    
    def _format_estimation_response(self, delivery_info: DeliveryInfo) -> str:
        """Format pour estimation de livraison"""
        if delivery_info and delivery_info.days_elapsed > 12:
            return f"""Je constate que votre commande a été passée il y a {delivery_info.days_elapsed} jours ouvrés.

Ce délai dépasse notre engagement de 12 jours ouvrés maximum.

🚨 ESCALADE PRIORITAIRE ACTIVÉE
Notre équipe de direction va vous contacter dans l'heure pour vous donner une date d'expédition ferme."""
        else:
            return """Je vais vérifier le statut de votre commande et vous donner une estimation précise de livraison."""
    
    def _format_tracking_response(self, delivery_info: DeliveryInfo) -> str:
        """Format pour informations de tracking"""
        if delivery_info and delivery_info.tracking_number:
            return f"""J'ai trouvé votre numéro de suivi {delivery_info.tracking_number} pour {delivery_info.carrier}.

Je vais vérifier le statut de votre colis et vous donner les informations les plus récentes."""
        else:
            return """Je vais vous aider avec le suivi de votre colis. Avez-vous un numéro de suivi ?"""
    
    def _format_address_change_response(self, delivery_info: DeliveryInfo) -> str:
        """Format pour changement d'adresse"""
        if delivery_info and delivery_info.delivery_address:
            return f"""Je comprends que vous souhaitez changer votre adresse de livraison pour : {delivery_info.delivery_address}

Je vais transmettre cette demande à notre service logistique pour mise à jour immédiate."""
        else:
            return """Je vais vous aider avec le changement d'adresse. Pouvez-vous me donner votre nouvelle adresse ?"""
    
    def _format_missing_package_response(self) -> str:
        """Format pour colis manquant"""
        return """Je comprends votre inquiétude concernant la non-réception de votre commande.

Je lance immédiatement les actions suivantes :

1️⃣ **Enquête transporteur** : Localisation exacte du colis
2️⃣ **Vérification adresse** : Confirmation des coordonnées de livraison
3️⃣ **Escalade prioritaire** : Votre dossier passe en urgence absolue

📞 Notre responsable logistique va vous appeler dans l'heure avec la localisation précise de votre colis."""
    
    def _format_escalation_response(self, priority: str) -> str:
        """Format pour escalade"""
        if priority == "URGENT":
            return """
🚨 **ESCALADE URGENTE - PRIORITÉ ABSOLUE**
Votre situation a été classée comme critique.
Un responsable va vous contacter dans l'heure."""
        else:
            return """
⚠️ **ESCALADE PRIORITAIRE**
Votre demande nécessite une attention particulière et a été transmise 
à notre équipe spécialisée qui vous contactera dans les plus brefs délais."""
