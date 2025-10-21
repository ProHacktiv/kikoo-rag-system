"""
UC_336 Detector - Statut précommande
Détecteur spécialisé pour UC_336 avec algorithme de scoring précis
"""

import re
from datetime import datetime
from typing import Dict, Optional

class UC336Detector:
    """
    Détecteur spécialisé UC_336 - Statut précommande
    Score de 0-100 basé sur présence/absence keywords
    """
    
    def __init__(self):
        # Patterns primaires (+30 points)
        self.primary_patterns = [
            r"où en est",
            r"statut",
            r"avancement", 
            r"progression",
            r"état.*commande",
            r"information.*commande",
            r"des nouvelles",
            r"des infos",
            r"suivi.*commande",
            r"idée.*envoi",
            r"concernant.*envoi",
            r"réception.*colis",
        ]
        
        # Patterns statut visible (+20 points)
        self.status_patterns = [
            r"toujours en",
            r"n'a pas bougé",
            r"n'a pas changé",
            r"en cours",
            r"fabrication",
            r"préparation",
            r"noté",
        ]
        
        # Patterns négatifs (pénalité -30 chacun)
        self.negative_patterns = [
            r"retard",
            r"toujours pas reçu",
            r"toujours pas livré",
            r"quand vais-je recevoir",
            r"date de livraison",
            r"sera livré quand",
            r"numéro.*suivi",
            r"tracking.*numéro",
            r"urgent",
            r"anniversaire",
            r"impérativement",
            r"vacances",
        ]
    
    def detect(self, message: str, order_data: Dict = None) -> Dict:
        """
        Détecte UC_336 avec scoring précis
        
        Args:
            message: Message du client
            order_data: Données de commande depuis Odoo
            
        Returns:
            {
                "is_uc_336": bool,
                "confidence": float (0-100),
                "reason": str,
                "should_escalate": bool,
                "days_since_order": int
            }
        """
        score = 0
        reasons = []
        message_lower = message.lower()
        
        # ÉTAPE 1 : Keywords primaires (+30 points)
        primary_found = False
        for pattern in self.primary_patterns:
            if re.search(pattern, message_lower):
                score += 30
                primary_found = True
                reasons.append(f"✓ Keyword primaire: '{pattern}'")
                break
        
        # ÉTAPE 2 : Statut visible mentionné (+20 points)
        for pattern in self.status_patterns:
            if re.search(pattern, message_lower):
                score += 20
                reasons.append(f"✓ Statut visible: '{pattern}'")
                break
        
        # ÉTAPE 3 : Vérifier délai commande
        days_since_order = self._extract_days(message, order_data)
        
        if days_since_order:
            if days_since_order < 12:
                score += 20
                reasons.append(f"✓ Commande récente: {days_since_order}j < 12j")
            else:
                score -= 30
                reasons.append(f"⚠️ Retard: {days_since_order}j >= 12j → UC_337")
        
        # ÉTAPE 4 : Keywords négatifs (pénalité -30 chacun)
        has_negative = False
        for pattern in self.negative_patterns:
            if re.search(pattern, message_lower):
                score -= 30
                has_negative = True
                reasons.append(f"✗ Keyword négatif: '{pattern}'")
        
        if not has_negative:
            score += 10
            reasons.append("✓ Pas de plainte/urgence")
        
        # NORMALISER
        confidence = max(0, min(100, score))
        is_uc_336 = confidence >= 40 and primary_found
        
        # ESCALADE si > 12 jours
        should_escalate = days_since_order and days_since_order > 12
        
        return {
            "is_uc_336": is_uc_336,
            "confidence": confidence,
            "reason": " | ".join(reasons),
            "should_escalate": should_escalate,
            "days_since_order": days_since_order
        }
    
    def _extract_days(self, message: str, order_data: Dict = None) -> Optional[int]:
        """Extrait nombre de jours depuis commande"""
        
        # Si données Odoo disponibles
        if order_data and "order_date" in order_data:
            try:
                if isinstance(order_data["order_date"], str):
                    order_date = datetime.fromisoformat(order_data["order_date"])
                else:
                    order_date = order_data["order_date"]
                return (datetime.now() - order_date).days
            except:
                pass
        
        # Sinon, parser le message
        message_lower = message.lower()
        
        # "il y a X jours"
        match = re.search(r"il y a (\d+) jours?", message_lower)
        if match:
            return int(match.group(1))
        
        # "ça fait X jours"
        match = re.search(r"ça fait (\d+) jours?", message_lower)
        if match:
            return int(match.group(1))
        
        # "une semaine"
        if "une semaine" in message_lower:
            return 7
        
        # "X semaines"
        match = re.search(r"(\d+) semaines?", message_lower)
        if match:
            return int(match.group(1)) * 7
        
        # Date "commandé le DD/MM"
        match = re.search(r"command[ée].*le (\d{1,2})/(\d{1,2})", message)
        if match:
            day, month = int(match.group(1)), int(match.group(2))
            try:
                order_date = datetime(datetime.now().year, month, day)
                return (datetime.now() - order_date).days
            except:
                pass
        
        return None
    
    def get_detection_summary(self, message: str, order_data: Dict = None) -> str:
        """Retourne un résumé de la détection pour debug"""
        result = self.detect(message, order_data)
        
        summary = f"""
🔍 DÉTECTION UC_336
==================
Message: {message[:100]}...

Résultat: {'✅ UC_336' if result['is_uc_336'] else '❌ Pas UC_336'}
Confiance: {result['confidence']:.1f}%
Escalade: {'OUI' if result['should_escalate'] else 'NON'}
Jours: {result['days_since_order'] or 'N/A'}

Raisons:
{result['reason']}
"""
        return summary
