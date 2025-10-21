import re
from typing import Tuple, Dict, Any

class DeliveryIntentAnalyzer:
    """Analyse l'intention des messages liés à la livraison"""
    
    PATTERNS = {
        'DELIVERY_ESTIMATION': [
            r'quand.*(?:recevoir|livr|expédi)',
            r'estimation.*livraison',
            r'délai.*(?:livraison|commande)',
            r'combien.*temps.*(?:recevoir|livr)',
            r'date.*(?:livraison|réception)'
        ],
        'ORDER_STATUS': [
            r'où en est.*commande',
            r'état.*commande',
            r'statut.*commande',
            r'nouvelles?.*commande',
            r'suivi.*commande',
            r'commande.*en cours'
        ],
        'DELIVERY_PROBLEM': [
            r'pas.*reçu',
            r'toujours pas.*(?:nouvelles|reçu|livr)',
            r'problème.*livraison',
            r'colis.*(?:perdu|pas arrivé)',
            r'retard.*livraison',
            r'manque.*(?:article|produit|écran)'
        ],
        'ADDRESS_CHANGE': [
            r'chang.*adresse',
            r'nouvelle adresse',
            r'mauvaise adresse',
            r'modifier.*adresse'
        ]
    }
    
    TIME_INDICATORS = {
        'days': r'(\d+)\s*(?:jour|j)',
        'weeks': r'(\d+)\s*semaine',
        'date': r'(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)'
    }
    
    def analyze(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analyse le message et retourne l'intention + contexte
        Returns: (intent_type, context_dict)
        """
        message_lower = message.lower()
        
        # Chercher l'intention principale
        intent = 'UNKNOWN_DELIVERY'
        for intent_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    intent = intent_type
                    break
            if intent != 'UNKNOWN_DELIVERY':
                break
        
        # Extraire le contexte temporel
        context = {}
        
        # Chercher les indicateurs de temps
        for time_type, pattern in self.TIME_INDICATORS.items():
            match = re.search(pattern, message_lower)
            if match:
                context[f'mentioned_{time_type}'] = match.group(1)
        
        # Détecter l'urgence
        urgent_words = ['urgent', 'vite', 'rapidement', 'impati', 'besoin']
        context['is_urgent'] = any(word in message_lower for word in urgent_words)
        
        # Détecter la frustration
        frustration_words = ['toujours pas', 'encore', 'ça fait', 'impatient', 'inquiet']
        context['is_frustrated'] = any(word in message_lower for word in frustration_words)
        
        return intent, context