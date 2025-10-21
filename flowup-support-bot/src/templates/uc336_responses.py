"""
Templates de réponse UC_336 - Statut précommande
SANS PROMESSES - Constatations uniquement
"""

import re
from typing import Dict

UC_336_RESPONSE_TEMPLATES = {
    "within_delay": """
Bonjour, je suis l'assistant automatique FlowUp.

Je vérifie immédiatement votre commande dans notre système.

📊 **État de votre commande :**
• Date de commande : {order_date}
• Jours écoulés : {days_elapsed} jours
• Délai légal : 12 jours ouvrés
• Statut actuel : {current_status}

✅ **Votre commande est dans les délais normaux.**

{status_explanation}

Votre commande sera traitée selon nos délais standards.
Je ne peux pas vous donner de date exacte, mais vous recevrez 
une notification dès qu'elle sera expédiée.

Puis-je vous aider pour autre chose ?
""",

    "delay_exceeded": """
Bonjour, je suis l'assistant automatique FlowUp.

Je constate que votre commande date de {days_elapsed} jours.

⚠️ **Nos délais standards sont de 12 jours maximum.**

Je m'excuse sincèrement pour ce retard.

Je ne peux malheureusement pas vous garantir de délai précis,
mais j'escalade immédiatement votre dossier vers notre équipe 
prioritaire qui traitera votre demande.

🚨 **ESCALADE PRIORITAIRE**
Votre demande a été transmise à notre équipe spécialisée.

Merci de votre patience.
""",

    "no_order_data": """
Bonjour, je suis l'assistant automatique FlowUp.

Je vérifie votre commande dans notre système.

Malheureusement, je ne peux pas accéder aux détails complets 
de votre commande pour le moment.

J'escalade votre demande vers notre équipe qui pourra vous 
fournir des informations précises sur l'avancement.

⚠️ **ESCALADE VERS ÉQUIPE SUPPORT**

Merci de votre compréhension.
""",

    "status_update": """
Bonjour, je suis l'assistant automatique FlowUp.

Je vérifie l'état de votre commande dans notre système.

📊 **Informations actuelles :**
• Statut : {current_status}
• Dernière mise à jour : {last_update}
• Jours écoulés : {days_elapsed} jours

{status_explanation}

Votre commande progresse normalement dans notre processus.
Vous serez informé automatiquement de tout changement d'état.

Puis-je vous aider pour autre chose ?
"""
}

STATUS_EXPLANATIONS = {
    "EN COURS": "Votre PC est actuellement en phase de production dans nos ateliers.",
    "Fabrication": "Votre PC est en cours d'assemblage par nos techniciens.",
    "Préparation": "Votre PC est assemblé et en cours de tests finaux avant expédition.",
    "Test": "Votre PC passe nos contrôles qualité avant expédition.",
    "EN PRODUCTION": "Votre PC est en cours de fabrication dans nos ateliers.",
    "ASSEMBLAGE": "Votre PC est en cours d'assemblage par nos techniciens.",
    "CONTROLE": "Votre PC passe nos contrôles qualité finaux.",
    "EN ATTENTE": "Votre commande est en attente de traitement.",
    "VALIDEE": "Votre commande a été validée et est en cours de traitement.",
}

def generate_uc336_response(detection_result: Dict, order_data: Dict = None) -> str:
    """
    Génère la réponse UC_336 SANS INVENTION
    
    Args:
        detection_result: Résultat de la détection UC_336
        order_data: Données de commande depuis Odoo
        
    Returns:
        str: Réponse personnalisée
    """
    
    days = detection_result.get("days_since_order")
    should_escalate = detection_result.get("should_escalate")
    
    # CAS 1 : Retard > 12 jours → Escalade
    if should_escalate:
        return UC_336_RESPONSE_TEMPLATES["delay_exceeded"].format(
            days_elapsed=days
        )
    
    # CAS 2 : Pas de données Odoo → Escalade
    if not order_data:
        return UC_336_RESPONSE_TEMPLATES["no_order_data"]
    
    # CAS 3 : Dans les délais
    order_date = order_data.get("date", "N/A")
    current_status = order_data.get("status", "EN COURS")
    status_explanation = STATUS_EXPLANATIONS.get(
        current_status,
        "Votre commande est en cours de traitement."
    )
    
    return UC_336_RESPONSE_TEMPLATES["within_delay"].format(
        order_date=order_date,
        days_elapsed=days or "N/A",
        current_status=current_status,
        status_explanation=status_explanation
    )

def get_status_explanation(status: str) -> str:
    """Retourne l'explication d'un statut"""
    return STATUS_EXPLANATIONS.get(
        status.upper(),
        "Votre commande est en cours de traitement."
    )

def validate_response_safety(response: str) -> bool:
    """
    Valide qu'une réponse ne contient pas de promesses dangereuses
    
    Returns:
        bool: True si la réponse est sûre
    """
    dangerous_patterns = [
        r"dans \d+ heures?",
        r"sous \d+ heures?",
        r"dans \d+ jours?",
        r"nous allons vous envoyer",
        r"je vais vous envoyer",
        r"garantie",
        r"promis",
        r"assuré",
        r"certain",
    ]
    
    response_lower = response.lower()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, response_lower):
            return False
    
    return True
