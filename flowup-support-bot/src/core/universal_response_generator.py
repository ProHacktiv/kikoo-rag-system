"""
Générateur de réponses unifié basé sur les UC et templates.
Optimisé pour les 50 tickets FlowUp analysés.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import yaml
import json

class UniversalResponseGenerator:
    """Générateur de réponses basé sur les UC et templates"""
    
    def __init__(self, odoo_client=None, config_path="config"):
        self.odoo = odoo_client
        self.config_path = config_path
        self.templates = self._load_templates()
        self.uc_solutions = self._load_uc_solutions()
    
    def _load_templates(self) -> Dict:
        """Charge tous les templates de réponse"""
        return {
            "greeting": "Bonjour, je suis l'assistant automatique FlowUp.",
            
            # DELIVERY Templates
            "delivery_estimation": """
J'ai trouvé votre commande {order_ref} du {order_date}.

✅ **Votre commande est dans les délais légaux**
• Commandée il y a : {days_elapsed} jours
• Délai maximum : 12 jours ouvrés
• Jours restants : {remaining_days} jours
• Statut actuel : {status}

{tracking_info}

Puis-je vous aider pour autre chose ?
""",
            
            "delivery_delayed": """
⚠️ **Je constate un dépassement du délai légal** ({days_elapsed} jours).

Je transfère immédiatement votre demande à un opérateur pour un traitement prioritaire.

Un membre de notre équipe vous contactera dans les plus brefs délais.
""",
            
            "incomplete_delivery": """
Je comprends que votre livraison est incomplète.

📦 **Éléments commandés :**
{order_items}

⚠️ **Éléments manquants détectés.**

Je transfère votre réclamation au service logistique avec priorité ÉLEVÉE.
Un opérateur vous contactera dans les 2 heures.

Je vous présente nos excuses pour cette erreur.
""",
            
            "tracking_provided": """
📦 **Votre commande est expédiée !**
• Transporteur : {carrier}
• Numéro de suivi : {tracking_number}
• [Suivre mon colis]({tracking_url})

Vous devriez recevoir votre colis sous 24-48h.
""",
            
            # HARDWARE Templates  
            "hardware_diagnostic": """
Je comprends que vous rencontrez un problème technique avec {component}.

🔧 **Solutions à essayer :**
{solutions}

Si le problème persiste après ces vérifications, je peux transférer votre demande à un technicien.

Ces solutions ont-elles résolu votre problème ?
""",
            
            "hardware_escalation": """
Je vois que le problème persiste malgré les solutions proposées.

Je transfère immédiatement votre demande à un technicien spécialisé qui pourra vous aider plus efficacement.

Un technicien vous contactera dans les plus brefs délais.
""",
            
            # SALES Templates
            "refund_request": """
Je comprends votre demande de {request_type}.

En tant qu'assistant automatique, je ne peux pas traiter directement les demandes de remboursement ou d'échange.

Je transfère immédiatement votre demande à un opérateur spécialisé avec priorité ÉLEVÉE.

Un membre de notre équipe vous contactera dans les plus brefs délais.
""",
            
            "pre_order_inquiry": """
Je comprends votre question concernant {inquiry_type}.

{response_content}

Un conseiller commercial vous contactera pour plus de détails.
""",
            
            # GENERIC
            "escalation": """
Je transfère votre demande à un opérateur qui pourra mieux vous aider.

Raison : {reason}
Priorité : {priority}

Vous serez contacté dans les plus brefs délais.
""",
            
            "unknown": """
Je vais vous aider au mieux.

Pourriez-vous me préciser votre demande concernant :
- Une livraison ou commande ?
- Un problème technique ?
- Une question commerciale ?

Cela me permettra de mieux vous orienter.
""",
            
            "closing": """
Puis-je vous aider pour autre chose ?
"""
        }
    
    def _load_uc_solutions(self) -> Dict:
        """Charge les solutions par UC"""
        return {
            # HARDWARE Solutions
            263: {
                "component": "votre carte graphique",
                "solutions": """1. Vérifier les câbles d'alimentation de la carte graphique
2. Mettre à jour les pilotes graphiques
3. Vérifier les températures avec HWMonitor
4. Tester avec une autre sortie vidéo
5. Vérifier que la carte est bien enfichée"""
            },
            267: {
                "component": "l'alimentation",
                "solutions": """1. Vérifier tous les câbles d'alimentation
2. Tester avec une autre prise électrique
3. Maintenir le bouton power 30 secondes (PC débranché)
4. Vérifier que l'interrupteur de l'alimentation est sur ON
5. Tester avec une autre alimentation si possible"""
            },
            269: {
                "component": "le système de refroidissement",
                "solutions": """1. Nettoyer les filtres à poussière
2. Vérifier que les ventilateurs tournent
3. Appliquer un profil de ventilation plus agressif
4. Vérifier la pâte thermique du processeur
5. Vérifier l'orientation des ventilateurs"""
            },
            270: {
                "component": "les périphériques",
                "solutions": """1. Vérifier les connexions USB
2. Tester sur un autre port USB
3. Redémarrer le PC
4. Vérifier les pilotes des périphériques
5. Tester avec un autre périphérique"""
            },
            284: {
                "component": "l'écran",
                "solutions": """1. Vérifier les câbles de connexion
2. Tester avec un autre câble
3. Vérifier la source d'alimentation de l'écran
4. Tester avec un autre écran
5. Vérifier les paramètres d'affichage"""
            },
            
            # SOFTWARE Solutions
            277: {
                "component": "la connexion réseau",
                "solutions": """1. Redémarrer le routeur/modem
2. Vérifier les câbles réseau
3. Tester la connexion WiFi
4. Vérifier les paramètres réseau
5. Contacter votre FAI si nécessaire"""
            },
            272: {
                "component": "le système d'exploitation",
                "solutions": """1. Redémarrer en mode sans échec
2. Vérifier les mises à jour Windows
3. Exécuter une vérification des fichiers système
4. Vérifier l'espace disque disponible
5. Restaurer le système à une date antérieure"""
            }
        }
    
    def generate(self, intent_result, ticket_data: Dict) -> str:
        """Génère la réponse complète basée sur l'analyse"""
        
        response_parts = []
        
        # 1. Toujours commencer par le greeting
        response_parts.append(self.templates["greeting"])
        
        # 2. Check Odoo si nécessaire
        order_data = None
        if self._needs_odoo_check(intent_result):
            order_data = self._get_order_data(ticket_data.get("user_id"))
        
        # 3. Générer le corps selon l'UC
        body = self._generate_body_for_uc(intent_result, ticket_data, order_data)
        response_parts.append(body)
        
        # 4. Ajouter escalade si nécessaire
        if intent_result.requires_escalation:
            escalation = self.templates["escalation"].format(
                reason=intent_result.escalation_reason,
                priority=intent_result.priority.value
            )
            response_parts.append(escalation)
        
        # 5. Toujours finir par la question de clôture
        response_parts.append(self.templates["closing"])
        
        return "\n\n".join(response_parts)
    
    def _needs_odoo_check(self, intent) -> bool:
        """Détermine si on doit checker Odoo"""
        odoo_categories = ["DELIVERY", "SALES"]
        odoo_ucs = [421, 337, 426, 336, 365]
        
        return (intent.category.value in odoo_categories or 
                intent.uc_id in odoo_ucs)
    
    def _get_order_data(self, user_id: str) -> Optional[Dict]:
        """Récupère les données de commande depuis Odoo"""
        if not self.odoo:
            # Mock data pour test
            return {
                "order_ref": "CMD-2024-001",
                "order_date": datetime.now() - timedelta(days=7),
                "status": "EN PRODUCTION",
                "items": ["PC Gamer RTX 4060", "Écran 27 pouces"],
                "tracking": None
            }
        
        return self.odoo.get_order(user_id)
    
    def _generate_body_for_uc(self, intent, ticket: Dict, order: Dict) -> str:
        """Génère le corps de message selon l'UC détecté"""
        
        # UC 337 - Estimation livraison
        if intent.uc_id == 337:
            if order:
                days = (datetime.now() - order["order_date"]).days
                remaining = 12 - days
                
                if remaining > 0:
                    return self.templates["delivery_estimation"].format(
                        order_ref=order["order_ref"],
                        order_date=order["order_date"].strftime("%d/%m/%Y"),
                        days_elapsed=days,
                        remaining_days=remaining,
                        status=order["status"],
                        tracking_info=self._format_tracking(order.get("tracking"))
                    )
                else:
                    return self.templates["delivery_delayed"].format(
                        days_elapsed=days
                    )
        
        # UC 306 - Remboursement
        elif intent.uc_id == 306:
            return self.templates["refund_request"].format(
                request_type="remboursement"
            )
        
        # UC 426 - Livraison incomplète
        elif intent.uc_id == 426:
            if order:
                items_list = "\n".join([f"• {item}" for item in order["items"]])
                return self.templates["incomplete_delivery"].format(
                    order_items=items_list
                )
        
        # UC Hardware (263, 267, 269, 270, 284)
        elif intent.category.value == "HARDWARE":
            solutions = self._get_hardware_solutions(intent.uc_id)
            return self.templates["hardware_diagnostic"].format(
                component=solutions["component"],
                solutions=solutions["solutions"]
            )
        
        # UC Software (277, 272)
        elif intent.category.value == "SOFTWARE":
            solutions = self._get_software_solutions(intent.uc_id)
            return self.templates["hardware_diagnostic"].format(
                component=solutions["component"],
                solutions=solutions["solutions"]
            )
        
        # UC 336 - Précommande
        elif intent.uc_id == 336:
            return self.templates["pre_order_inquiry"].format(
                inquiry_type="la disponibilité",
                response_content="Je vais vérifier la disponibilité de ce produit et vous recontacter."
            )
        
        # Fallback
        return self.templates["unknown"]
    
    def _format_tracking(self, tracking: Optional[Dict]) -> str:
        """Formate les infos de tracking"""
        if not tracking:
            return ""
        
        return self.templates["tracking_provided"].format(
            carrier=tracking.get('carrier', 'UPS'),
            tracking_number=tracking.get('number', ''),
            tracking_url=tracking.get('url', '')
        )
    
    def _get_hardware_solutions(self, uc_id: int) -> Dict:
        """Retourne les solutions pour problèmes hardware"""
        return self.uc_solutions.get(uc_id, {
            "component": "votre matériel",
            "solutions": "1. Redémarrer le PC\n2. Vérifier les connexions\n3. Contacter le support technique"
        })
    
    def _get_software_solutions(self, uc_id: int) -> Dict:
        """Retourne les solutions pour problèmes software"""
        return self.uc_solutions.get(uc_id, {
            "component": "le système",
            "solutions": "1. Redémarrer le PC\n2. Vérifier les mises à jour\n3. Contacter le support technique"
        })
    
    def generate_escalation_response(self, reason: str, priority: str) -> str:
        """Génère une réponse d'escalade standardisée"""
        return self.templates["escalation"].format(
            reason=reason,
            priority=priority
        )
    
    def get_response_stats(self, responses: List[Dict]) -> Dict:
        """Calcule les statistiques des réponses générées"""
        stats = {
            "total_responses": len(responses),
            "by_category": {},
            "escalation_rate": 0,
            "avg_length": 0
        }
        
        total_length = 0
        escalated = 0
        
        for response in responses:
            category = response.get("category", "UNKNOWN")
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += 1
            
            if response.get("escalated", False):
                escalated += 1
            
            total_length += len(response.get("content", ""))
        
        stats["escalation_rate"] = escalated / len(responses) if responses else 0
        stats["avg_length"] = total_length / len(responses) if responses else 0
        
        return stats
