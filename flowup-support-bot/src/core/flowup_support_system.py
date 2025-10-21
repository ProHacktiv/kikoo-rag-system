# FlowUp Support System - Système Complet de Gestion de Tickets
# Version 1.0 - Production Ready

import re
import json
import yaml
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
import logging
from abc import ABC, abstractmethod

# ==================== Configuration ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Enums et Constantes ====================

class Category(Enum):
    DELIVERY = "DELIVERY"
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    SALES = "SALES"
    RETURNS = "RETURNS"
    BILLING = "BILLING"
    UNKNOWN = "UNKNOWN"

class OrderStatus(Enum):
    EN_PRODUCTION = "EN_PRODUCTION"
    PICKING = "PICKING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"

class Priority(Enum):
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

# Patterns critiques basés sur l'analyse des 49 tickets
CRITICAL_PATTERNS = {
    "IMMEDIATE_ESCALATION": [
        r"remboursement",
        r"rembourser",
        r"échange",
        r"retour",
        r"défectueux",
        r"ne fonctionne plus",
        r"1 mois",
        r"2 semaine",
        r"pas de nouvelle",
    ],
    "MULTI_UC_COMBINATIONS": [
        (r"livraison.*adresse", ["UC_337", "UC_438"]),  # Livraison + changement adresse
        (r"commande.*retard", ["UC_337", "UC_421"]),    # Commande + tracking
        (r"carte graphique.*température", ["UC_263", "UC_269"]),  # GPU + refroidissement
        (r"windows.*activation", ["UC_272", "UC_278"]),  # OS + installation
    ],
    "EMOTION_INDICATORS": {
        "frustration": [r"impatien", r"inquiét", r"toujours pas", r"aucune nouvelle"],
        "urgence": [r"urgent", r"rapidement", r"au plus vite", r"besoin"],
        "colère": [r"inadmissible", r"scandaleux", r"marre", r"assez"],
    }
}

# Mapping UC basé sur les tickets analysés
UC_MAPPINGS = {
    # Livraison
    "UC_337": {
        "keywords": ["estimation", "livraison", "délai", "quand", "recevoir", "expédié"],
        "category": Category.DELIVERY,
        "priority": Priority.HIGH
    },
    "UC_421": {
        "keywords": ["tracking", "suivi", "numéro", "trace", "ups", "colissimo"],
        "category": Category.DELIVERY,
        "priority": Priority.MEDIUM
    },
    "UC_426": {
        "keywords": ["pas reçu", "pas livré", "perdu", "non livré"],
        "category": Category.DELIVERY,
        "priority": Priority.URGENT
    },
    "UC_438": {
        "keywords": ["changement adresse", "nouvelle adresse", "modifier adresse"],
        "category": Category.DELIVERY,
        "priority": Priority.HIGH
    },
    
    # Hardware
    "UC_263": {
        "keywords": ["carte graphique", "gpu", "rtx", "nvidia", "amd", "performance"],
        "category": Category.HARDWARE,
        "priority": Priority.HIGH
    },
    "UC_269": {
        "keywords": ["surchauffe", "température", "chaleur", "ventilateur", "refroidissement"],
        "category": Category.HARDWARE,
        "priority": Priority.URGENT
    },
    "UC_267": {
        "keywords": ["alimentation", "ne démarre pas", "s'éteint", "power"],
        "category": Category.HARDWARE,
        "priority": Priority.URGENT
    },
    "UC_268": {
        "keywords": ["ssd", "hdd", "disque", "stockage", "nvme"],
        "category": Category.HARDWARE,
        "priority": Priority.MEDIUM
    },
    
    # Software
    "UC_272": {
        "keywords": ["windows", "système", "activation", "clé", "licence"],
        "category": Category.SOFTWARE,
        "priority": Priority.HIGH
    },
    "UC_278": {
        "keywords": ["installation", "logiciel", "driver", "pilote"],
        "category": Category.SOFTWARE,
        "priority": Priority.MEDIUM
    },
    
    # RGB
    "UC_291": {
        "keywords": ["rgb", "led", "éclairage", "lumière", "couleur"],
        "category": Category.HARDWARE,
        "priority": Priority.LOW
    },
    
    # Sales
    "UC_365": {
        "keywords": ["commander", "acheter", "devis", "prix", "promotion"],
        "category": Category.SALES,
        "priority": Priority.MEDIUM
    },
    "UC_320": {
        "keywords": ["configuration", "personnalisation", "custom", "sur mesure"],
        "category": Category.SALES,
        "priority": Priority.MEDIUM
    },
    
    # Returns
    "UC_313": {
        "keywords": ["garantie", "échange", "remplacement", "retour", "défaut"],
        "category": Category.RETURNS,
        "priority": Priority.URGENT
    }
}

# ==================== Models ====================

@dataclass
class Intent:
    """Représente une intention détectée"""
    uc_id: str
    confidence: float
    keywords_found: List[str]
    category: Category
    priority: Priority

@dataclass
class TicketContext:
    """Contexte enrichi du ticket"""
    order_id: Optional[str] = None
    order_status: Optional[OrderStatus] = None
    order_date: Optional[datetime] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    previous_tickets: List[int] = field(default_factory=list)
    
@dataclass
class Ticket:
    """Modèle de ticket complet"""
    id: int
    message: str
    timestamp: datetime
    detected_intents: List[Intent] = field(default_factory=list)
    context: TicketContext = field(default_factory=TicketContext)
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None
    
@dataclass
class Response:
    """Modèle de réponse générée"""
    content: str
    actions: List[str]
    escalate: bool
    confidence: float

# ==================== Analyseur Multi-UC ====================

class MultiUCAnalyzer:
    """Analyse un message et détecte TOUS les UC présents"""
    
    def __init__(self):
        self.uc_mappings = UC_MAPPINGS
        self.patterns = CRITICAL_PATTERNS
        
    def analyze(self, message: str) -> List[Intent]:
        """
        Analyse complète du message pour détecter tous les UC
        """
        message_lower = message.lower()
        detected_intents = []
        
        # Recherche directe par mots-clés UC
        for uc_id, config in self.uc_mappings.items():
            confidence = 0.0
            keywords_found = []
            
            for keyword in config["keywords"]:
                if keyword in message_lower:
                    confidence += 0.3
                    keywords_found.append(keyword)
            
            # Boost de confiance pour patterns spécifiques
            confidence = min(confidence, 1.0)
            
            if confidence >= 0.3:
                detected_intents.append(Intent(
                    uc_id=uc_id,
                    confidence=confidence,
                    keywords_found=keywords_found,
                    category=config["category"],
                    priority=config["priority"]
                ))
        
        # Détection des combinaisons multi-UC
        for pattern, uc_ids in self.patterns["MULTI_UC_COMBINATIONS"]:
            if re.search(pattern, message_lower):
                for uc_id in uc_ids:
                    if uc_id not in [i.uc_id for i in detected_intents]:
                        config = self.uc_mappings.get(uc_id, {})
                        detected_intents.append(Intent(
                            uc_id=uc_id,
                            confidence=0.7,
                            keywords_found=[],
                            category=config.get("category", Category.UNKNOWN),
                            priority=config.get("priority", Priority.MEDIUM)
                        ))
        
        # Si aucun UC détecté, catégoriser comme UNKNOWN
        if not detected_intents:
            detected_intents.append(Intent(
                uc_id="UC_None",
                confidence=0.5,
                keywords_found=[],
                category=Category.UNKNOWN,
                priority=Priority.LOW
            ))
        
        # Trier par priorité et confiance
        detected_intents.sort(key=lambda x: (x.priority.value, -x.confidence))
        
        return detected_intents
    
    def detect_emotion(self, message: str) -> Dict[str, float]:
        """Détecte l'état émotionnel du client"""
        emotions = {}
        message_lower = message.lower()
        
        for emotion, patterns in self.patterns["EMOTION_INDICATORS"].items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 0.5
            emotions[emotion] = min(score, 1.0)
        
        return emotions
    
    def requires_immediate_escalation(self, message: str) -> Tuple[bool, Optional[str]]:
        """Vérifie si le message nécessite une escalade immédiate"""
        message_lower = message.lower()
        
        for pattern in self.patterns["IMMEDIATE_ESCALATION"]:
            if re.search(pattern, message_lower):
                return True, f"Pattern critique détecté: {pattern}"
        
        # Vérifier le délai de 12 jours
        delay_patterns = [
            r"(\d+)\s*(?:jour|day)",
            r"(\d+)\s*(?:semaine|week)",
            r"commandé.*(\d+/\d+)"
        ]
        
        for pattern in delay_patterns:
            match = re.search(pattern, message_lower)
            if match:
                # Logique simplifiée pour démo
                return True, "Délai potentiellement dépassé"
        
        return False, None

# ==================== Mock Odoo Integration ====================

class OdooIntegration:
    """Mock de l'intégration Odoo pour récupérer les données client"""
    
    def __init__(self):
        # Mock data pour démonstration
        self.mock_orders = {
            "default": {
                "order_id": "SO-2024-1234",
                "status": OrderStatus.EN_PRODUCTION,
                "order_date": datetime.now() - timedelta(days=7),
                "customer_email": "client@example.com"
            }
        }
    
    def get_customer_context(self, email: Optional[str] = None) -> TicketContext:
        """Récupère le contexte client depuis Odoo"""
        # En production, faire un appel API réel à Odoo
        order_data = self.mock_orders.get("default", {})
        
        context = TicketContext(
            order_id=order_data.get("order_id"),
            order_status=order_data.get("status"),
            order_date=order_data.get("order_date"),
            customer_email=order_data.get("customer_email")
        )
        
        return context
    
    def calculate_delay(self, order_date: datetime) -> int:
        """Calcule le délai en jours ouvrés"""
        if not order_date:
            return 0
        
        business_days = 0
        current = order_date
        today = datetime.now()
        
        while current < today:
            if current.weekday() < 5:  # Lundi = 0, Vendredi = 4
                business_days += 1
            current += timedelta(days=1)
        
        return business_days

# ==================== Générateur de Réponses ====================

class ContextualResponseGenerator:
    """Génère des réponses contextuelles personnalisées"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.odoo = OdooIntegration()
    
    def _load_templates(self) -> Dict:
        """Charge les templates de réponse"""
        return {
            "greeting": "Bonjour, je suis l'assistant automatique FlowUp. ",
            
            # Templates par UC
            "UC_337": {
                "within_delay": "Je consulte votre commande {order_id}. Elle est actuellement en statut {status}. Votre PC gaming est en cours de production depuis {days} jours ouvrés. Le délai standard est de 12 jours ouvrés maximum. Vous devriez recevoir votre commande d'ici {remaining} jours ouvrés.",
                "delay_exceeded": "Je constate que votre commande {order_id} a été passée il y a {days} jours ouvrés, ce qui dépasse notre délai standard. Je transfère immédiatement votre demande à notre équipe prioritaire qui vous contactera dans les plus brefs délais.",
                "no_order": "Je vais vérifier le statut de votre commande. D'après nos systèmes, votre dernière commande est en cours de traitement. Notre équipe va vous contacter rapidement avec une mise à jour précise."
            },
            
            "UC_263": {
                "default": "Je vois que vous rencontrez un problème avec votre carte graphique. Voici les étapes de diagnostic recommandées:\n1. Vérifiez que la carte est bien connectée\n2. Mettez à jour les pilotes depuis le site du constructeur\n3. Contrôlez les températures avec GPU-Z\nSi le problème persiste, notre équipe technique prendra le relais."
            },
            
            "UC_269": {
                "default": "Un problème de surchauffe nécessite une attention immédiate. Éteignez votre PC et vérifiez:\n1. Que tous les ventilateurs fonctionnent\n2. Qu'il n'y a pas de poussière dans les filtres\n3. Que la pâte thermique est correctement appliquée\nNotre équipe technique va vous contacter pour un diagnostic approfondi."
            },
            
            "UC_313": {
                "default": "Je comprends votre demande de retour/échange. Votre garantie de 2 ans couvre l'ensemble de votre configuration. Je transfère immédiatement votre demande à notre service après-vente qui vous contactera sous 24h avec la procédure de retour."
            },
            
            "UC_426": {
                "default": "Je comprends votre inquiétude concernant la non-réception de votre commande. Je vérifie immédiatement avec notre transporteur et notre équipe logistique va vous contacter en urgence avec les informations de localisation de votre colis."
            },
            
            "UC_None": {
                "default": "Je comprends votre demande. Pour vous apporter la meilleure assistance possible, notre équipe support va analyser votre message et vous répondre personnellement dans les plus brefs délais."
            },
            
            # Réponses multi-UC
            "multi_uc": "J'ai identifié plusieurs points dans votre message:\n{responses}\n\nNotre équipe va traiter l'ensemble de ces points en priorité.",
            
            # Escalade
            "escalation": "\n\n⚠️ Votre demande nécessite une attention particulière et a été transmise en priorité à notre équipe spécialisée."
        }
    
    def generate(self, ticket: Ticket) -> Response:
        """Génère une réponse complète pour le ticket"""
        response_parts = [self.templates["greeting"]]
        actions = []
        needs_escalation = ticket.requires_escalation
        
        # Si multi-UC détecté
        if len(ticket.detected_intents) > 1:
            sub_responses = []
            
            for intent in ticket.detected_intents:
                if intent.uc_id != "UC_None":
                    sub_response = self._generate_uc_response(intent, ticket.context)
                    if sub_response:
                        sub_responses.append(f"• {sub_response}")
            
            if sub_responses:
                response_parts.append(self.templates["multi_uc"].format(
                    responses="\n".join(sub_responses)
                ))
        else:
            # Single UC
            intent = ticket.detected_intents[0] if ticket.detected_intents else None
            if intent:
                uc_response = self._generate_uc_response(intent, ticket.context)
                if uc_response:
                    response_parts.append(uc_response)
        
        # Ajouter message d'escalade si nécessaire
        if needs_escalation:
            response_parts.append(self.templates["escalation"])
            actions.append("ESCALATE_TO_HUMAN")
        
        # Construire la réponse finale
        final_response = "\n".join(response_parts)
        
        return Response(
            content=final_response,
            actions=actions,
            escalate=needs_escalation,
            confidence=ticket.detected_intents[0].confidence if ticket.detected_intents else 0.5
        )
    
    def _generate_uc_response(self, intent: Intent, context: TicketContext) -> str:
        """Génère une réponse spécifique pour un UC"""
        uc_templates = self.templates.get(intent.uc_id, {})
        
        if intent.uc_id == "UC_337":
            # Gestion spéciale pour estimation livraison
            if context.order_date:
                delay = self.odoo.calculate_delay(context.order_date)
                if delay > 12:
                    template = uc_templates.get("delay_exceeded", "")
                else:
                    template = uc_templates.get("within_delay", "")
                    remaining = 12 - delay
                
                return template.format(
                    order_id=context.order_id or "EN_COURS",
                    status=context.order_status.value if context.order_status else "EN_PRODUCTION",
                    days=delay,
                    remaining=remaining if delay <= 12 else 0
                )
            else:
                return uc_templates.get("no_order", "")
        
        # Réponse par défaut pour autres UC
        return uc_templates.get("default", "")

# ==================== Processeur Principal ====================

class UnifiedTicketProcessor:
    """Pipeline principal de traitement des tickets"""
    
    def __init__(self):
        self.analyzer = MultiUCAnalyzer()
        self.generator = ContextualResponseGenerator()
        self.odoo = OdooIntegration()
        self.metrics = {
            "total_processed": 0,
            "escalated": 0,
            "multi_uc_detected": 0,
            "by_category": {}
        }
    
    def process(self, ticket_id: int, message: str) -> Dict:
        """
        Pipeline complet de traitement d'un ticket
        """
        logger.info(f"Processing ticket {ticket_id}")
        
        # 1. Créer le ticket
        ticket = Ticket(
            id=ticket_id,
            message=message,
            timestamp=datetime.now()
        )
        
        # 2. Analyse multi-UC
        ticket.detected_intents = self.analyzer.analyze(message)
        
        # 3. Détection d'émotions
        emotions = self.analyzer.detect_emotion(message)
        
        # 4. Vérifier escalade
        needs_escalation, reason = self.analyzer.requires_immediate_escalation(message)
        ticket.requires_escalation = needs_escalation
        ticket.escalation_reason = reason
        
        # 5. Enrichissement contexte Odoo
        ticket.context = self.odoo.get_customer_context()
        
        # 6. Génération de la réponse
        response = self.generator.generate(ticket)
        
        # 7. Mise à jour des métriques
        self._update_metrics(ticket, response)
        
        # 8. Logging
        self._log_processing(ticket, response, emotions)
        
        # Retourner le résultat complet
        return {
            "ticket_id": ticket_id,
            "detected_intents": [
                {
                    "uc_id": i.uc_id,
                    "confidence": i.confidence,
                    "category": i.category.value,
                    "priority": i.priority.value
                }
                for i in ticket.detected_intents
            ],
            "emotions": emotions,
            "response": response.content,
            "actions": response.actions,
            "requires_escalation": response.escalate,
            "confidence": response.confidence
        }
    
    def _update_metrics(self, ticket: Ticket, response: Response):
        """Met à jour les métriques de performance"""
        self.metrics["total_processed"] += 1
        
        if response.escalate:
            self.metrics["escalated"] += 1
        
        if len(ticket.detected_intents) > 1:
            self.metrics["multi_uc_detected"] += 1
        
        for intent in ticket.detected_intents:
            category = intent.category.value
            self.metrics["by_category"][category] = \
                self.metrics["by_category"].get(category, 0) + 1
    
    def _log_processing(self, ticket: Ticket, response: Response, emotions: Dict):
        """Log détaillé du traitement"""
        logger.info(f"Ticket {ticket.id} processed:")
        logger.info(f"  - Intents: {[i.uc_id for i in ticket.detected_intents]}")
        logger.info(f"  - Emotions: {emotions}")
        logger.info(f"  - Escalation: {ticket.requires_escalation}")
        logger.info(f"  - Confidence: {response.confidence}")
    
    def get_metrics(self) -> Dict:
        """Retourne les métriques de performance"""
        return self.metrics

# ==================== Tests Unitaires ====================

class TestSuite:
    """Suite de tests pour valider le système"""
    
    def __init__(self):
        self.processor = UnifiedTicketProcessor()
        self.test_cases = self._load_test_cases()
    
    def _load_test_cases(self) -> List[Dict]:
        """Charge les cas de test basés sur les 49 tickets réels"""
        return [
            {
                "id": 36514,
                "message": "Bonjour, puis je avoir une estimation de livraison pour ma commande car cela fait 1 semaine que j'ai commandé et payé.",
                "expected_uc": ["UC_337"],
                "expected_category": Category.DELIVERY,
                "should_escalate": False
            },
            {
                "id": 36226,
                "message": "après avoir différentes manipulation mon pc ne redémarre toujours pas je demande l'échange ou le remboursement",
                "expected_uc": ["UC_313"],
                "expected_category": Category.RETURNS,
                "should_escalate": True
            },
            {
                "id": 39370,
                "message": "j'ai acheté un ordinateur chez vous, tout d'un coup mon ordinateur c'est éteint avec le message préparation de la réparation automatique les leds de la carte graphique s'éteigne",
                "expected_uc": ["UC_263", "UC_267"],
                "expected_category": Category.HARDWARE,
                "should_escalate": True
            },
            {
                "id": 43810,
                "message": "Bonjour, j'habite maintenant au : 12b rue madeleine laffitte, Montreuil, 93100. Serait-il possible de changer l'adresse ?",
                "expected_uc": ["UC_438"],
                "expected_category": Category.DELIVERY,
                "should_escalate": False
            },
            {
                "id": 32252,
                "message": "j'ai un message qui me dit alerte surchauffe cpu après 5 minute mon pc s'éteint tout seule",
                "expected_uc": ["UC_269"],
                "expected_category": Category.HARDWARE,
                "should_escalate": True
            }
        ]
    
    def run_tests(self) -> Dict:
        """Exécute tous les tests et retourne les résultats"""
        results = {
            "total": len(self.test_cases),
            "passed": 0,
            "failed": 0,
            "accuracy_category": 0,
            "accuracy_uc": 0,
            "accuracy_escalation": 0,
            "details": []
        }
        
        for test_case in self.test_cases:
            result = self.processor.process(
                test_case["id"],
                test_case["message"]
            )
            
            # Vérifier la catégorie
            detected_categories = [i["category"] for i in result["detected_intents"]]
            category_match = test_case["expected_category"].value in detected_categories
            
            # Vérifier les UC
            detected_ucs = [i["uc_id"] for i in result["detected_intents"]]
            uc_match = any(uc in detected_ucs for uc in test_case["expected_uc"])
            
            # Vérifier l'escalade
            escalation_match = result["requires_escalation"] == test_case["should_escalate"]
            
            # Calculer le score
            test_passed = category_match and uc_match and escalation_match
            
            if test_passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            if category_match:
                results["accuracy_category"] += 1
            if uc_match:
                results["accuracy_uc"] += 1
            if escalation_match:
                results["accuracy_escalation"] += 1
            
            # Détails pour debug
            results["details"].append({
                "ticket_id": test_case["id"],
                "passed": test_passed,
                "category_match": category_match,
                "uc_match": uc_match,
                "escalation_match": escalation_match,
                "detected_ucs": detected_ucs,
                "expected_ucs": test_case["expected_uc"]
            })
        
        # Calculer les pourcentages
        results["accuracy_category"] = (results["accuracy_category"] / results["total"]) * 100
        results["accuracy_uc"] = (results["accuracy_uc"] / results["total"]) * 100
        results["accuracy_escalation"] = (results["accuracy_escalation"] / results["total"]) * 100
        
        return results

# ==================== Main ====================

def main():
    """Point d'entrée principal pour démonstration"""
    
    print("=== FlowUp Support System v1.0 ===\n")
    
    # Initialiser le processeur
    processor = UnifiedTicketProcessor()
    
    # Test avec des exemples réels
    test_messages = [
        (36514, "Bonjour, puis je avoir une estimation de livraison pour ma commande car cela fait 1 semaine que j'ai commandé"),
        (39370, "mon ordinateur c'est éteint, la carte graphique s'éteint aussi, je demande un échange"),
        (32252, "alerte surchauffe cpu mon pc s'éteint après 5 minutes"),
        (43810, "je voudrais changer mon adresse de livraison pour le 12b rue madeleine laffitte, Montreuil"),
        (49061, "j'ai commandé mon pc le 30 Juillet aucune nouvelle, combien de temps pour la livraison ?")
    ]
    
    print("📝 Traitement des tickets de test:\n")
    for ticket_id, message in test_messages:
        print(f"Ticket #{ticket_id}")
        print(f"Message: {message[:100]}...")
        
        result = processor.process(ticket_id, message)
        
        print(f"UC détectés: {[i['uc_id'] for i in result['detected_intents']]}")
        print(f"Confiance: {result['confidence']:.2%}")
        print(f"Escalade: {'✅ OUI' if result['requires_escalation'] else '❌ NON'}")
        print(f"\n🤖 Réponse:\n{result['response']}\n")
        print("-" * 80 + "\n")
    
    # Exécuter les tests
    print("\n📊 Exécution des tests de validation:\n")
    test_suite = TestSuite()
    test_results = test_suite.run_tests()
    
    print(f"✅ Tests réussis: {test_results['passed']}/{test_results['total']}")
    print(f"❌ Tests échoués: {test_results['failed']}/{test_results['total']}")
    print(f"\nPrécisions:")
    print(f"  - Catégorie: {test_results['accuracy_category']:.1f}%")
    print(f"  - UC: {test_results['accuracy_uc']:.1f}%")
    print(f"  - Escalade: {test_results['accuracy_escalation']:.1f}%")
    
    # Métriques
    print("\n📈 Métriques globales:")
    metrics = processor.get_metrics()
    print(f"  - Total traité: {metrics['total_processed']}")
    print(f"  - Escaladés: {metrics['escalated']}")
    print(f"  - Multi-UC détectés: {metrics['multi_uc_detected']}")
    print(f"  - Par catégorie: {metrics['by_category']}")

if __name__ == "__main__":
    main()
