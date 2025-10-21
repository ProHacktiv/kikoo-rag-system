"""
Système de réponses contextuelles personnalisées
Implémentation du plan d'optimisation avec génération de réponses intelligentes
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

class ContextualResponseEngine:
    """
    Générateur de réponses personnalisées par contexte
    
    FONCTIONNALITÉS:
    - Analyse du profil client
    - Sélection de templates appropriés
    - Personnalisation dynamique
    - Gestion des escalades
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Templates de réponse par UC et contexte
        self.response_templates = self._load_response_templates()
        
        # Configuration des personnalisations
        self.personalization_config = {
            "frustration_levels": ["low", "medium", "high", "critical"],
            "client_types": ["professional", "consumer", "vip"],
            "urgency_levels": ["normal", "high", "critical"]
        }
    
    def generate_response(self, uc: str, context: Dict, message: str = "") -> Dict[str, Any]:
        """
        Génère une réponse contextuelle personnalisée
        
        Args:
            uc: Use Case détecté
            context: Contexte Odoo enrichi
            message: Message original du client
            
        Returns:
            Dict avec réponse, métadonnées, actions
        """
        try:
            # 1. Analyser le profil client
            client_profile = self._analyze_client_profile(context, message)
            
            # 2. Sélectionner le template approprié
            template = self._select_template(uc, client_profile, context)
            
            # 3. Personnaliser la réponse
            personalized_response = self._personalize_response(
                template, client_profile, context, uc
            )
            
            # 4. Ajouter les actions nécessaires
            response_with_actions = self._add_actions(personalized_response, uc, context)
            
            # 5. Générer les métadonnées
            metadata = self._generate_metadata(uc, client_profile, context)
            
            return {
                "response": response_with_actions,
                "metadata": metadata,
                "client_profile": client_profile,
                "template_used": template.get("name", "default"),
                "personalization_applied": True
            }
            
        except Exception as e:
            self.logger.error(f"Erreur génération réponse: {str(e)}")
            return self._get_fallback_response(uc, context)
    
    def _analyze_client_profile(self, context: Dict, message: str) -> Dict[str, Any]:
        """Analyse le profil client pour personnalisation"""
        profile = {
            "frustration_level": "low",
            "client_type": "consumer",
            "urgency_level": "normal",
            "communication_style": "formal",
            "technical_level": "basic"
        }
        
        # Analyse du niveau de frustration
        frustration_indicators = {
            "low": ["merci", "s'il vous plaît", "pouvez-vous"],
            "medium": ["problème", "difficulté", "souci"],
            "high": ["urgent", "rapidement", "immédiatement", "frustré"],
            "critical": ["inacceptable", "scandale", "avocat", "plainte", "remboursement"]
        }
        
        message_lower = message.lower()
        for level, indicators in frustration_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                profile["frustration_level"] = level
                break
        
        # Analyse du type de client
        if context.get("total_orders", 0) > 5:
            profile["client_type"] = "vip"
        elif context.get("customer_name", "").endswith((".com", ".fr", ".org")):
            profile["client_type"] = "professional"
        
        # Analyse du niveau d'urgence
        if context.get("priority") == "IMMEDIATE":
            profile["urgency_level"] = "critical"
        elif context.get("is_delayed", False):
            profile["urgency_level"] = "high"
        
        # Analyse du style de communication
        if any(word in message_lower for word in ["bonjour", "bonsoir", "merci"]):
            profile["communication_style"] = "formal"
        else:
            profile["communication_style"] = "casual"
        
        # Analyse du niveau technique
        technical_terms = ["driver", "bios", "overclocking", "watercooling"]
        if any(term in message_lower for term in technical_terms):
            profile["technical_level"] = "advanced"
        
        return profile
    
    def _select_template(self, uc: str, client_profile: Dict, context: Dict) -> Dict[str, Any]:
        """Sélectionne le template approprié"""
        frustration_level = client_profile["frustration_level"]
        client_type = client_profile["client_type"]
        urgency_level = client_profile["urgency_level"]
        
        # Sélection basée sur l'UC et le contexte
        template_key = f"{uc}_{frustration_level}_{client_type}"
        
        if template_key in self.response_templates:
            return self.response_templates[template_key]
        
        # Fallback vers template générique
        fallback_key = f"{uc}_default"
        if fallback_key in self.response_templates:
            return self.response_templates[fallback_key]
        
        # Template par défaut
        return self.response_templates["default"]
    
    def _personalize_response(self, template: Dict, client_profile: Dict, 
                            context: Dict, uc: str) -> str:
        """Personnalise la réponse selon le contexte"""
        response = template.get("content", "")
        
        # Variables de personnalisation
        variables = {
            "customer_name": context.get("customer_name", "Client"),
            "order_reference": context.get("order_reference", "votre commande"),
            "days_elapsed": context.get("days_since_order", 0),
            "order_status": context.get("order_status", "en cours"),
            "gpu_model": self._extract_gpu_model(context),
            "delay_status": self._get_delay_status(context),
            "compensation": self._calculate_compensation(context),
            "next_steps": self._get_next_steps(uc, context)
        }
        
        # Remplacement des variables
        for key, value in variables.items():
            response = response.replace(f"{{{key}}}", str(value))
        
        # Personnalisation selon le profil
        if client_profile["frustration_level"] == "critical":
            response = self._add_apology(response)
        
        if client_profile["client_type"] == "vip":
            response = self._add_vip_treatment(response)
        
        return response
    
    def _add_actions(self, response: str, uc: str, context: Dict) -> str:
        """Ajoute les actions nécessaires à la réponse"""
        actions = []
        
        # Actions selon l'UC
        if uc == "UC_263":
            actions.extend([
                "🔧 Diagnostic technique programmé",
                "📞 Contact technicien sous 2h",
                "🛠️ RMA express si nécessaire"
            ])
        elif uc == "UC_336":
            actions.extend([
                "📊 Vérification statut en cours",
                "📧 Mise à jour par email",
                "🚨 Escalade si retard détecté"
            ])
        elif uc == "UC_337":
            actions.extend([
                "⏰ Calcul délai exact",
                "🚨 Escalade prioritaire",
                "💰 Compensation si applicable"
            ])
        
        # Actions selon le contexte
        if context.get("needs_escalation"):
            actions.append("🚨 ESCALADE PRIORITAIRE ACTIVÉE")
        
        if context.get("is_delayed"):
            actions.append("⚠️ RETARD DÉTECTÉ - TRAITEMENT URGENT")
        
        # Ajouter les actions à la réponse
        if actions:
            response += "\n\n" + "✅ **Actions immédiates :**\n"
            for action in actions:
                response += f"• {action}\n"
        
        return response
    
    def _generate_metadata(self, uc: str, client_profile: Dict, context: Dict) -> Dict[str, Any]:
        """Génère les métadonnées de la réponse"""
        return {
            "uc": uc,
            "timestamp": datetime.now().isoformat(),
            "client_profile": client_profile,
            "context_summary": {
                "has_order": context.get("has_order", False),
                "is_delayed": context.get("is_delayed", False),
                "needs_escalation": context.get("needs_escalation", False),
                "priority": context.get("priority", "NORMAL")
            },
            "response_quality": {
                "personalized": True,
                "contextual": True,
                "actionable": True
            }
        }
    
    def _extract_gpu_model(self, context: Dict) -> str:
        """Extrait le modèle GPU du contexte"""
        gpu_products = context.get("gpu_products", [])
        if gpu_products:
            return gpu_products[0].get("name", "votre carte graphique")
        return "votre carte graphique"
    
    def _get_delay_status(self, context: Dict) -> str:
        """Génère le statut de délai"""
        days = context.get("days_since_order", 0)
        if days > 12:
            return f"⚠️ Retard de {days - 12} jours"
        elif days > 7:
            return f"⏰ {12 - days} jours restants"
        else:
            return "✅ Dans les délais"
    
    def _calculate_compensation(self, context: Dict) -> str:
        """Calcule la compensation si applicable"""
        days = context.get("days_since_order", 0)
        if days > 15:
            return "💰 Compensation de 10% offerte"
        elif days > 12:
            return "🎁 Bon de réduction de 5%"
        else:
            return ""
    
    def _get_next_steps(self, uc: str, context: Dict) -> str:
        """Génère les prochaines étapes"""
        if uc == "UC_263":
            return "Un technicien vous contactera sous 2h pour diagnostic"
        elif uc == "UC_336":
            return "Mise à jour par email dans les 30 minutes"
        elif uc == "UC_337":
            return "Escalade prioritaire - réponse sous 1h"
        else:
            return "Suivi personnalisé assuré"
    
    def _add_apology(self, response: str) -> str:
        """Ajoute des excuses pour clients frustrés"""
        apology = "\n\nJe vous présente mes excuses sincères pour ce désagrément."
        return response + apology
    
    def _add_vip_treatment(self, response: str) -> str:
        """Ajoute un traitement VIP"""
        vip_note = "\n\nEn tant que client VIP, vous bénéficiez d'un traitement prioritaire."
        return response + vip_note
    
    def _get_fallback_response(self, uc: str, context: Dict) -> Dict[str, Any]:
        """Réponse de fallback en cas d'erreur"""
        return {
            "response": """
Bonjour, je suis l'assistant automatique FlowUp.

Je rencontre un problème technique momentané.

Je transfère votre demande à un opérateur qui pourra vous aider immédiatement.

Merci de votre patience.
            """.strip(),
            "metadata": {
                "uc": uc,
                "timestamp": datetime.now().isoformat(),
                "fallback": True
            },
            "client_profile": {},
            "template_used": "fallback",
            "personalization_applied": False
        }
    
    def _load_response_templates(self) -> Dict[str, Dict]:
        """Charge les templates de réponse"""
        return {
            # UC_263 - Problèmes GPU
            "UC_263_low_consumer": {
                "name": "GPU Problem - Low Frustration",
                "content": """
Bonjour {customer_name}, je suis l'assistant automatique FlowUp.

Je constate un problème technique avec {gpu_model}.

✅ **Actions immédiates effectuées :**
• Diagnostic enregistré dans votre dossier
• Équipe technique notifiée
• Procédure garantie activée

🔧 Un technicien vous contactera sous 2h pour :
• Diagnostic approfondi par TeamViewer
• Solution immédiate si possible
• RMA express si remplacement nécessaire

{next_steps}

Puis-je vous aider pour autre chose ?
                """.strip()
            },
            
            "UC_263_high_consumer": {
                "name": "GPU Problem - High Frustration",
                "content": """
Bonjour {customer_name}, je suis l'assistant automatique FlowUp.

Je comprends votre frustration concernant {gpu_model}.

🚨 **PRIORITÉ MAXIMALE ACCORDÉE À VOTRE CAS**

✅ **Actions immédiates effectuées :**
• Escalade prioritaire activée
• Technicien senior assigné
• RMA express préparé
• Compensation calculée

{compensation}

🔧 Un technicien senior vous contactera dans l'heure pour :
• Diagnostic immédiat
• Solution ou remplacement express
• Suivi personnalisé

Je vous présente mes excuses sincères pour ce désagrément.

{next_steps}
                """.strip()
            },
            
            # UC_336 - Statut commande
            "UC_336_default": {
                "name": "Order Status - Default",
                "content": """
Bonjour {customer_name}, je suis l'assistant automatique FlowUp.

Je vérifie immédiatement {order_reference} dans notre système.

📊 **État de votre commande :**
• Date de commande : {days_elapsed} jours écoulés
• Statut actuel : {order_status}
• {delay_status}

{next_steps}

Puis-je vous aider pour autre chose ?
                """.strip()
            },
            
            # UC_337 - Délai livraison
            "UC_337_high_consumer": {
                "name": "Delivery Delay - High Frustration",
                "content": """
Bonjour {customer_name}, je suis l'assistant automatique FlowUp.

Je constate que votre commande date de {days_elapsed} jours.

⚠️ **Nos délais standards sont de 12 jours maximum.**

{delay_status}

Je m'excuse sincèrement pour ce retard.

{compensation}

🚨 **ESCALADE PRIORITAIRE**
Votre demande a été transmise à notre équipe spécialisée.

{next_steps}

Merci de votre patience.
                """.strip()
            },
            
            # Template par défaut
            "default": {
                "name": "Default Template",
                "content": """
Bonjour {customer_name}, je suis l'assistant automatique FlowUp.

Je vais vous aider au mieux avec votre demande.

Un opérateur vous contactera dans les plus brefs délais.

Merci de votre compréhension.
                """.strip()
            }
        }

# Test du moteur de réponses contextuelles
def test_contextual_engine():
    """Test du moteur de réponses contextuelles"""
    engine = ContextualResponseEngine()
    
    test_cases = [
        {
            "uc": "UC_263",
            "context": {
                "customer_name": "Jean Dupont",
                "has_order": True,
                "gpu_products": [{"name": "RTX 4080"}],
                "days_since_order": 5,
                "priority": "HIGH"
            },
            "message": "Ma carte graphique ne fonctionne plus"
        },
        {
            "uc": "UC_336",
            "context": {
                "customer_name": "Marie Martin",
                "has_order": True,
                "order_reference": "CMD-2024-001",
                "days_since_order": 8,
                "order_status": "en cours"
            },
            "message": "Où en est ma commande ?"
        }
    ]
    
    print("🧪 TEST MOTEUR RÉPONSES CONTEXTUELLES")
    print("=" * 45)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. UC: {case['uc']}")
        print(f"   Client: {case['context']['customer_name']}")
        
        result = engine.generate_response(
            case['uc'], 
            case['context'], 
            case['message']
        )
        
        print(f"   Réponse: {result['response'][:100]}...")
        print(f"   Template: {result['template_used']}")
        print(f"   Personnalisé: {'✅ OUI' if result['personalization_applied'] else '❌ NON'}")
        
        if result['client_profile']:
            profile = result['client_profile']
            print(f"   Profil: {profile['frustration_level']} | {profile['client_type']} | {profile['urgency_level']}")

if __name__ == "__main__":
    test_contextual_engine()
