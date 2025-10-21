"""
Détecteur UC amélioré multi-étapes
Implémentation du plan d'optimisation avec détection en 3 étapes
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging

class ImprovedUCDetector:
    """
    Détecteur UC amélioré avec analyse en 3 étapes
    
    ÉTAPES:
    1. Analyse syntaxique (tokenisation, entités)
    2. Analyse sémantique (intent, symptômes)
    3. Scoring multi-critères (keywords, intent, symptômes, contexte)
    """
    
    def __init__(self, odoo_checker=None):
        self.odoo_checker = odoo_checker
        self.logger = logging.getLogger(__name__)
        
        # Configuration des UC avec seuils de confiance
        self.uc_config = {
            "UC_263": {
                "keywords": ["carte graphique", "gpu", "rtx", "gtx", "graphics"],
                "symptoms": ["crash", "freeze", "écran noir", "artefacts", "surchauffe"],
                "intents": ["problem", "issue", "broken", "not_working"],
                "context_required": True,
                "confidence_threshold": 0.6
            },
            "UC_336": {
                "keywords": ["où en est", "statut", "avancement", "progression"],
                "symptoms": ["toujours en", "n'a pas bougé", "en cours"],
                "intents": ["status_inquiry", "progress_check"],
                "context_required": True,
                "confidence_threshold": 0.4
            },
            "UC_337": {
                "keywords": ["délai", "quand", "recevoir", "estimation", "livraison"],
                "symptoms": ["retard", "toujours pas reçu", "urgent"],
                "intents": ["delivery_inquiry", "timing_question"],
                "context_required": True,
                "confidence_threshold": 0.5
            },
            "UC_421": {
                "keywords": ["suivi", "tracking", "numéro", "suivre"],
                "symptoms": ["pas de suivi", "numéro perdu"],
                "intents": ["tracking_request"],
                "context_required": True,
                "confidence_threshold": 0.5
            }
        }
        
        # Patterns d'intent
        self.intent_patterns = {
            "problem": [r"ne fonctionne pas", r"problème", r"bug", r"erreur", r"défaillant"],
            "status_inquiry": [r"où en est", r"statut", r"avancement", r"progression"],
            "delivery_inquiry": [r"quand", r"délai", r"recevoir", r"livraison"],
            "tracking_request": [r"suivi", r"tracking", r"numéro", r"suivre"],
            "commercial": [r"prix", r"coût", r"disponible", r"stock", r"recommandation"]
        }
        
        # Patterns de symptômes
        self.symptom_patterns = {
            "display": [r"écran noir", r"pas d'image", r"écran bleu", r"artefacts"],
            "performance": [r"crash", r"freeze", r"se fige", r"lent", r"saccadé"],
            "thermal": [r"surchauffe", r"chauffe", r"température", r"ventilateur"],
            "hardware": [r"ne s'allume plus", r"ne démarre pas", r"défaillant", r"cassé"]
        }
    
    def detect(self, message: str, user_id: str = None) -> Dict[str, Any]:
        """
        Détection UC améliorée en 3 étapes
        
        Args:
            message: Message du client
            user_id: ID du client pour contexte Odoo
            
        Returns:
            Dict avec UC détecté, confiance, détails
        """
        try:
            # ÉTAPE 1: Analyse syntaxique
            tokens = self._tokenize(message)
            entities = self._extract_entities(tokens)
            
            # ÉTAPE 2: Analyse sémantique
            intent = self._analyze_intent(message)
            symptoms = self._detect_symptoms(message)
            
            # ÉTAPE 3: Contexte Odoo si disponible
            context = None
            if user_id and self.odoo_checker:
                context = self.odoo_checker.check_order_context(user_id, message)
            
            # ÉTAPE 4: Scoring multi-critères
            scores = self._calculate_uc_scores(
                tokens, entities, intent, symptoms, context
            )
            
            # ÉTAPE 5: Sélection du meilleur UC
            best_uc, confidence = self._select_best_uc(scores)
            
            # ÉTAPE 6: Vérification seuil de confiance
            if confidence < 0.3:
                return self._handle_low_confidence(message, intent, context)
            
            # ÉTAPE 7: Génération du résultat
            result = self._build_result(best_uc, confidence, scores, context)
            
            self.logger.info(f"UC détecté: {best_uc} (confiance: {confidence:.1%})")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur détection UC: {str(e)}")
            return self._get_error_result()
    
    def _tokenize(self, message: str) -> List[str]:
        """Tokenisation du message"""
        # Nettoyage et tokenisation simple
        cleaned = re.sub(r'[^\w\s]', ' ', message.lower())
        tokens = cleaned.split()
        return tokens
    
    def _extract_entities(self, tokens: List[str]) -> Dict[str, List[str]]:
        """Extraction d'entités nommées"""
        entities = {
            "products": [],
            "components": [],
            "brands": [],
            "models": []
        }
        
        # Détection produits
        product_keywords = ["pc", "ordinateur", "carte graphique", "processeur", "ram"]
        for token in tokens:
            if any(keyword in token for keyword in product_keywords):
                entities["products"].append(token)
        
        # Détection composants
        component_keywords = ["rtx", "gtx", "intel", "amd", "nvidia"]
        for token in tokens:
            if any(keyword in token for keyword in component_keywords):
                entities["components"].append(token)
        
        return entities
    
    def _analyze_intent(self, message: str) -> str:
        """Analyse de l'intention du message"""
        message_lower = message.lower()
        
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            intent_scores[intent] = score
        
        # Retourner l'intent avec le score le plus élevé
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            return best_intent if intent_scores[best_intent] > 0 else "unknown"
        
        return "unknown"
    
    def _detect_symptoms(self, message: str) -> List[str]:
        """Détection des symptômes techniques"""
        message_lower = message.lower()
        found_symptoms = []
        
        for category, patterns in self.symptom_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    found_symptoms.append(f"{category}:{pattern}")
        
        return found_symptoms
    
    def _calculate_uc_scores(self, tokens: List[str], entities: Dict, 
                           intent: str, symptoms: List[str], context: Dict) -> Dict[str, float]:
        """Calcul des scores pour chaque UC"""
        scores = {}
        
        for uc_id, config in self.uc_config.items():
            score = 0.0
            
            # Score basé sur les mots-clés
            keyword_score = self._calculate_keyword_score(tokens, config["keywords"])
            score += keyword_score * 0.3
            
            # Score basé sur l'intent
            intent_score = self._calculate_intent_score(intent, config["intents"])
            score += intent_score * 0.3
            
            # Score basé sur les symptômes
            symptom_score = self._calculate_symptom_score(symptoms, config["symptoms"])
            score += symptom_score * 0.2
            
            # Score basé sur le contexte
            context_score = self._calculate_context_score(context, uc_id)
            score += context_score * 0.2
            
            scores[uc_id] = min(score, 1.0)
        
        return scores
    
    def _calculate_keyword_score(self, tokens: List[str], keywords: List[str]) -> float:
        """Calcule le score basé sur les mots-clés"""
        matches = 0
        for token in tokens:
            for keyword in keywords:
                if keyword in token or token in keyword:
                    matches += 1
                    break
        
        return min(matches / len(keywords), 1.0) if keywords else 0.0
    
    def _calculate_intent_score(self, intent: str, intents: List[str]) -> float:
        """Calcule le score basé sur l'intent"""
        if intent in intents:
            return 1.0
        return 0.0
    
    def _calculate_symptom_score(self, symptoms: List[str], expected_symptoms: List[str]) -> float:
        """Calcule le score basé sur les symptômes"""
        if not symptoms:
            return 0.0
        
        matches = 0
        for symptom in symptoms:
            for expected in expected_symptoms:
                if expected in symptom:
                    matches += 1
                    break
        
        return min(matches / len(expected_symptoms), 1.0) if expected_symptoms else 0.0
    
    def _calculate_context_score(self, context: Dict, uc_id: str) -> float:
        """Calcule le score basé sur le contexte Odoo"""
        if not context:
            return 0.0
        
        score = 0.0
        
        # UC_263: Vérifier présence GPU
        if uc_id == "UC_263" and context.get("has_gpu", False):
            score += 0.5
        
        # UC_336/337: Vérifier statut commande
        if uc_id in ["UC_336", "UC_337"] and context.get("has_order", False):
            score += 0.3
            
            # Bonus si retard
            if context.get("is_delayed", False):
                score += 0.2
        
        # UC_421: Vérifier statut livraison
        if uc_id == "UC_421" and context.get("delivery_status") in ["shipped", "in_transit"]:
            score += 0.5
        
        return min(score, 1.0)
    
    def _select_best_uc(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """Sélectionne le meilleur UC basé sur les scores"""
        if not scores:
            return "UC_UNKNOWN", 0.0
        
        best_uc = max(scores, key=scores.get)
        confidence = scores[best_uc]
        
        return best_uc, confidence
    
    def _handle_low_confidence(self, message: str, intent: str, context: Dict) -> Dict[str, Any]:
        """Gère les cas de faible confiance"""
        return {
            "uc_detected": "UC_UNKNOWN",
            "confidence": 0.0,
            "reason": "Confiance insuffisante",
            "suggestion": self._get_clarification_suggestion(intent, context),
            "needs_escalation": True,
            "escalation_reason": "Détection incertaine"
        }
    
    def _get_clarification_suggestion(self, intent: str, context: Dict) -> str:
        """Génère une suggestion de clarification"""
        if intent == "commercial":
            return "Pourriez-vous préciser votre question commerciale ?"
        elif intent == "problem":
            return "Pouvez-vous décrire plus précisément le problème rencontré ?"
        else:
            return "Pouvez-vous préciser votre demande ?"
    
    def _build_result(self, uc: str, confidence: float, scores: Dict, context: Dict) -> Dict[str, Any]:
        """Construit le résultat final"""
        return {
            "uc_detected": uc,
            "confidence": confidence,
            "all_scores": scores,
            "context": context,
            "needs_escalation": self._needs_escalation(uc, confidence, context),
            "escalation_reason": self._get_escalation_reason(uc, context),
            "priority": self._calculate_priority(uc, context),
            "suggested_actions": self._get_suggested_actions(uc, context)
        }
    
    def _needs_escalation(self, uc: str, confidence: float, context: Dict) -> bool:
        """Détermine si escalade nécessaire"""
        # Escalade si confiance faible
        if confidence < 0.5:
            return True
        
        # Escalade si contexte critique
        if context and context.get("needs_escalation", False):
            return True
        
        # Escalade pour certains UC critiques
        critical_ucs = ["UC_263", "UC_337"]
        if uc in critical_ucs and confidence < 0.7:
            return True
        
        return False
    
    def _get_escalation_reason(self, uc: str, context: Dict) -> str:
        """Génère la raison d'escalade"""
        if context and context.get("needs_escalation"):
            return context.get("escalation_reason", "Contexte critique")
        
        if uc == "UC_263":
            return "Problème technique GPU"
        elif uc == "UC_337":
            return "Retard de livraison"
        else:
            return "Détection incertaine"
    
    def _calculate_priority(self, uc: str, context: Dict) -> str:
        """Calcule la priorité"""
        if context and context.get("priority") == "IMMEDIATE":
            return "IMMEDIATE"
        elif uc in ["UC_263", "UC_337"]:
            return "HIGH"
        else:
            return "NORMAL"
    
    def _get_suggested_actions(self, uc: str, context: Dict) -> List[str]:
        """Génère les actions suggérées"""
        actions = []
        
        if uc == "UC_263":
            actions.extend([
                "Diagnostic technique",
                "Vérification garantie",
                "Escalade équipe technique"
            ])
        elif uc == "UC_336":
            actions.extend([
                "Vérification statut commande",
                "Mise à jour client",
                "Escalade si retard"
            ])
        elif uc == "UC_337":
            actions.extend([
                "Calcul délai exact",
                "Escalade prioritaire",
                "Compensation si applicable"
            ])
        
        return actions
    
    def _get_error_result(self) -> Dict[str, Any]:
        """Résultat en cas d'erreur"""
        return {
            "uc_detected": "UC_ERROR",
            "confidence": 0.0,
            "reason": "Erreur de détection",
            "needs_escalation": True,
            "escalation_reason": "Erreur système"
        }
    
    def get_detection_summary(self, message: str, user_id: str = None) -> str:
        """Retourne un résumé de la détection pour debug"""
        result = self.detect(message, user_id)
        
        summary = f"""
🔍 DÉTECTION UC AMÉLIORÉE
========================

Message: "{message[:50]}..."
Client: {user_id or 'Non spécifié'}

RÉSULTAT:
- UC détecté: {result.get('uc_detected', 'UNKNOWN')}
- Confiance: {result.get('confidence', 0):.1%}
- Escalade: {'🚨 OUI' if result.get('needs_escalation') else '❌ NON'}
- Priorité: {result.get('priority', 'NORMAL')}

DÉTAILS:
- Raison: {result.get('reason', 'N/A')}
- Actions suggérées: {', '.join(result.get('suggested_actions', []))}

SCORES DÉTAILLÉS:
{json.dumps(result.get('all_scores', {}), indent=2)}
        """
        
        return summary.strip()

# Test du détecteur amélioré
def test_improved_detector():
    """Test du détecteur UC amélioré"""
    detector = ImprovedUCDetector()
    
    test_cases = [
        {
            "message": "Ma carte graphique RTX 4080 ne s'allume plus",
            "expected_uc": "UC_263",
            "description": "Problème technique GPU"
        },
        {
            "message": "Où en est ma commande ?",
            "expected_uc": "UC_336", 
            "description": "Demande de statut"
        },
        {
            "message": "Quand vais-je recevoir mon PC ?",
            "expected_uc": "UC_337",
            "description": "Demande de délai"
        },
        {
            "message": "J'ai besoin du numéro de suivi",
            "expected_uc": "UC_421",
            "description": "Demande de tracking"
        }
    ]
    
    print("🧪 TEST DÉTECTEUR UC AMÉLIORÉ")
    print("=" * 40)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['description']}")
        print(f"   Message: {case['message']}")
        
        result = detector.detect(case['message'])
        detected_uc = result.get('uc_detected', 'UNKNOWN')
        confidence = result.get('confidence', 0)
        
        status = "✅ CORRECT" if detected_uc == case['expected_uc'] else "❌ INCORRECT"
        print(f"   Résultat: {status}")
        print(f"   UC: {detected_uc} (attendu: {case['expected_uc']})")
        print(f"   Confiance: {confidence:.1%}")
        print(f"   Escalade: {'🚨 OUI' if result.get('needs_escalation') else '❌ NON'}")

if __name__ == "__main__":
    test_improved_detector()
