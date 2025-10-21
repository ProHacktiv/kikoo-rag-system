"""
Détecteur UC_263 CORRIGÉ - Problèmes carte graphique
Version améliorée basée sur l'analyse des problèmes actuels
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class UC263DetectorFixed:
    """
    Détecteur UC_263 CORRIGÉ avec logique améliorée
    
    PROBLÈMES RÉSOLUS:
    - Faux positifs sur simple mention "carte graphique"
    - Distinction entre question commerciale et problème technique
    - Vérification de possession du PC
    - Analyse des symptômes réels
    """
    
    def __init__(self):
        # SYMPTÔMES TECHNIQUES RÉELS (pas juste mention du composant)
        self.technical_symptoms = [
            # Problèmes d'affichage
            "ne s'allume plus", "ne démarre pas", "écran noir", "écran bleu",
            "pas d'image", "pas de signal", "écran vide",
            
            # Problèmes de performance
            "crash", "freeze", "se fige", "s'éteint", "redémarre",
            "lent", "lag", "saccadé", "instable",
            
            # Problèmes visuels
            "artefacts", "lignes", "pixels", "couleurs bizarres",
            "écran déformé", "résolution", "affichage bizarre",
            
            # Problèmes thermiques
            "surchauffe", "chauffe", "température", "ventilateur",
            "bruit", "ventilo", "hot", "brûlant",
            
            # Problèmes drivers
            "driver", "pilote", "installation", "reconnaissance",
            "détection", "non reconnu", "erreur driver",
            
            # Problèmes matériels
            "défaillant", "défectueux", "ne fonctionne plus",
            "cassé", "mort", "plus de vie"
        ]
        
        # MOTS-CLÉS COMMERCIAUX (ne pas détecter comme UC_263)
        self.commercial_keywords = [
            "prix", "coût", "tarif", "combien", "budget",
            "disponible", "stock", "livraison", "délai",
            "compatible", "recommandation", "conseil",
            "comparaison", "différence", "meilleur",
            "upgrade", "amélioration", "évolution"
        ]
        
        # VÉRIFICATEURS DE POSSESSION
        self.ownership_indicators = [
            "mon pc", "mon ordinateur", "j'ai", "j'ai acheté",
            "j'ai commandé", "depuis que j'ai", "depuis l'achat",
            "depuis la livraison", "depuis que je l'ai reçu"
        ]
        
        # SEUILS DE CONFIANCE
        self.confidence_thresholds = {
            "high": 0.8,      # Symptômes clairs + possession
            "medium": 0.6,    # Symptômes + contexte
            "low": 0.4,       # Mention vague
            "reject": 0.3     # Probablement commercial
        }
    
    def detect(self, message: str, context: Dict = None) -> Dict:
        """
        Détection UC_263 améliorée avec logique multi-critères
        
        Args:
            message: Message du client
            context: Contexte de la commande (status, produits, etc.)
            
        Returns:
            Dict avec is_uc_263, confidence, reasons, should_escalate
        """
        message_lower = message.lower()
        
        # ÉTAPE 1: Vérifier si c'est une question commerciale
        if self._is_commercial_inquiry(message_lower):
            return {
                "is_uc_263": False,
                "confidence": 0.0,
                "reason": "Question commerciale détectée",
                "should_escalate": False,
                "category": "COMMERCIAL"
            }
        
        # ÉTAPE 2: Détecter les symptômes techniques
        symptoms_found = self._detect_technical_symptoms(message_lower)
        
        # ÉTAPE 3: Vérifier la possession du PC
        has_pc = self._check_pc_ownership(message_lower, context)
        
        # ÉTAPE 4: Calculer le score de confiance
        confidence, reasons = self._calculate_confidence(
            symptoms_found, has_pc, message_lower, context
        )
        
        # ÉTAPE 5: Décision finale
        is_uc_263 = confidence >= self.confidence_thresholds["medium"]
        should_escalate = confidence >= self.confidence_thresholds["high"]
        
        return {
            "is_uc_263": is_uc_263,
            "confidence": confidence,
            "reason": " | ".join(reasons),
            "should_escalate": should_escalate,
            "symptoms_found": symptoms_found,
            "has_pc": has_pc,
            "category": "TECHNICAL" if is_uc_263 else "COMMERCIAL"
        }
    
    def _is_commercial_inquiry(self, message: str) -> bool:
        """Vérifie si c'est une question commerciale (pas technique)"""
        commercial_score = 0
        
        for keyword in self.commercial_keywords:
            if keyword in message:
                commercial_score += 1
        
        # Si plus de 2 mots commerciaux, probablement commercial
        return commercial_score >= 2
    
    def _detect_technical_symptoms(self, message: str) -> List[str]:
        """Détecte les symptômes techniques réels"""
        found_symptoms = []
        
        for symptom in self.technical_symptoms:
            if symptom in message:
                found_symptoms.append(symptom)
        
        return found_symptoms
    
    def _check_pc_ownership(self, message: str, context: Dict = None) -> bool:
        """Vérifie si le client possède déjà le PC"""
        
        # Vérification par mots-clés dans le message
        ownership_indicators = any(indicator in message for indicator in self.ownership_indicators)
        
        # Vérification par contexte Odoo
        context_ownership = False
        if context:
            order_status = context.get('status', '').lower()
            if order_status in ['delivered', 'in_use', 'shipped']:
                context_ownership = True
        
        return ownership_indicators or context_ownership
    
    def _calculate_confidence(self, symptoms: List[str], has_pc: bool, 
                            message: str, context: Dict = None) -> Tuple[float, List[str]]:
        """Calcule le score de confiance multi-critères"""
        score = 0.0
        reasons = []
        
        # Base score
        base_score = 0.1
        score += base_score
        reasons.append("Base score")
        
        # Symptômes techniques (poids fort)
        if symptoms:
            symptom_score = min(len(symptoms) * 0.3, 0.6)  # Max 0.6
            score += symptom_score
            reasons.append(f"Symptômes: {len(symptoms)}")
        
        # Possession du PC (poids fort)
        if has_pc:
            ownership_score = 0.3
            score += ownership_score
            reasons.append("Possession PC confirmée")
        
        # Contexte de commande récente
        if context and context.get('days_since_order', 0) < 30:
            recent_score = 0.1
            score += recent_score
            reasons.append("Commande récente")
        
        # Mots-clés techniques spécifiques
        technical_keywords = ['gpu', 'carte graphique', 'graphics', 'rtx', 'gtx']
        tech_mentions = sum(1 for kw in technical_keywords if kw in message)
        if tech_mentions > 0:
            tech_score = min(tech_mentions * 0.1, 0.2)  # Max 0.2
            score += tech_score
            reasons.append(f"Mentions techniques: {tech_mentions}")
        
        # Pénalité si trop de mots commerciaux
        commercial_penalty = 0
        for keyword in self.commercial_keywords:
            if keyword in message:
                commercial_penalty += 0.1
        
        score -= commercial_penalty
        if commercial_penalty > 0:
            reasons.append(f"Pénalité commerciale: -{commercial_penalty:.1f}")
        
        # Normaliser entre 0 et 1
        confidence = max(0.0, min(1.0, score))
        
        return confidence, reasons
    
    def get_detection_summary(self, message: str, context: Dict = None) -> str:
        """Retourne un résumé de la détection pour debug"""
        result = self.detect(message, context)
        
        summary = f"""
🔍 ANALYSE UC_263 DÉTECTEUR CORRIGÉ
====================================

Message: "{message[:100]}..."

RÉSULTAT:
- UC_263 détecté: {'✅ OUI' if result['is_uc_263'] else '❌ NON'}
- Confiance: {result['confidence']:.1%}
- Catégorie: {result['category']}
- Escalade: {'🚨 OUI' if result['should_escalate'] else '❌ NON'}

DÉTAILS:
- Symptômes trouvés: {len(result['symptoms_found'])} ({result['symptoms_found']})
- Possession PC: {'✅ OUI' if result['has_pc'] else '❌ NON'}
- Raisons: {result['reason']}

SEUILS:
- Seuil minimum: {self.confidence_thresholds['medium']:.1%}
- Seuil escalade: {self.confidence_thresholds['high']:.1%}
        """
        
        return summary.strip()

# Tests de validation
def test_uc263_detector():
    """Tests pour valider le détecteur UC_263 corrigé"""
    
    detector = UC263DetectorFixed()
    
    # Tests POSITIFS (vrais problèmes techniques)
    positive_cases = [
        "Mon PC ne s'allume plus depuis hier, la carte graphique fait du bruit",
        "J'ai des artefacts sur l'écran, ma RTX 3080 crash",
        "Depuis que j'ai reçu mon PC, la carte graphique surchauffe",
        "Ma carte graphique ne fonctionne plus, écran noir au démarrage"
    ]
    
    # Tests NÉGATIFS (questions commerciales)
    negative_cases = [
        "Quel est le prix de la carte graphique RTX 4080 ?",
        "Quelle carte graphique recommandez-vous pour du gaming ?",
        "La RTX 4070 est-elle disponible en stock ?",
        "Quelle est la différence entre RTX 4060 et RTX 4070 ?"
    ]
    
    print("🧪 TESTS DÉTECTEUR UC_263 CORRIGÉ")
    print("=" * 50)
    
    print("\n✅ CAS POSITIFS (problèmes techniques):")
    for i, case in enumerate(positive_cases, 1):
        result = detector.detect(case)
        status = "✅ DÉTECTÉ" if result['is_uc_263'] else "❌ MANQUÉ"
        print(f"{i}. {status} - {case[:50]}...")
        print(f"   Confiance: {result['confidence']:.1%}")
    
    print("\n❌ CAS NÉGATIFS (questions commerciales):")
    for i, case in enumerate(negative_cases, 1):
        result = detector.detect(case)
        status = "✅ REJETÉ" if not result['is_uc_263'] else "❌ FAUX POSITIF"
        print(f"{i}. {status} - {case[:50]}...")
        print(f"   Confiance: {result['confidence']:.1%}")
    
    # Test avec contexte
    print("\n🔍 TEST AVEC CONTEXTE:")
    context = {
        'status': 'delivered',
        'days_since_order': 5,
        'products': ['RTX 4080']
    }
    
    test_message = "Ma carte graphique ne s'allume plus"
    result = detector.detect(test_message, context)
    print(f"Message: {test_message}")
    print(f"Résultat: {'✅ DÉTECTÉ' if result['is_uc_263'] else '❌ MANQUÉ'}")
    print(f"Confiance: {result['confidence']:.1%}")
    print(f"Escalade: {'🚨 OUI' if result['should_escalate'] else '❌ NON'}")

if __name__ == "__main__":
    test_uc263_detector()
