"""
Tests unitaires pour UC_336 Detector
Validation de la détection et des réponses
"""

import sys
import os
import unittest
from datetime import datetime, timedelta

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.detectors.uc336_detector import UC336Detector
from src.templates.uc336_responses import generate_uc336_response, validate_response_safety

class TestUC336Detector(unittest.TestCase):
    """Tests pour le détecteur UC_336"""
    
    def setUp(self):
        """Initialisation des tests"""
        self.detector = UC336Detector()
    
    def test_positive_cases(self):
        """Test des cas positifs - doivent détecter UC_336"""
        
        # TEST 1 : Message typique UC_336
        message1 = "Commande effectuée le 24/03 : ordre de fabrication toujours noté EN COURS, des infos ?"
        result1 = self.detector.detect(message1)
        
        self.assertTrue(result1["is_uc_336"], f"Devrait détecter UC_336: {result1}")
        self.assertGreaterEqual(result1["confidence"], 60, f"Confiance trop faible: {result1['confidence']}")
        
        # TEST 2 : Demande de statut
        message2 = "j'ai passé commande il y a une semaine j'aimerai savoir où en est la commande"
        result2 = self.detector.detect(message2)
        
        self.assertTrue(result2["is_uc_336"], f"Devrait détecter UC_336: {result2}")
        self.assertGreaterEqual(result2["confidence"], 50, f"Confiance trop faible: {result2['confidence']}")
        
        # TEST 3 : Demande d'avancement
        message3 = "Bonjour, j'aimerais connaître l'avancement de ma commande"
        result3 = self.detector.detect(message3)
        
        self.assertTrue(result3["is_uc_336"], f"Devrait détecter UC_336: {result3}")
        self.assertGreaterEqual(result3["confidence"], 50, f"Confiance trop faible: {result3['confidence']}")
        
        print("✅ Tests positifs passés")
    
    def test_negative_cases(self):
        """Test des cas négatifs - ne doivent PAS détecter UC_336"""
        
        # TEST 1 : Retard explicite
        message1 = "ma commande n'est pas livrée. 16 jours ouvrés depuis la commande"
        result1 = self.detector.detect(message1)
        
        self.assertFalse(result1["is_uc_336"], f"Ne devrait PAS détecter UC_336: {result1}")
        self.assertTrue(result1["should_escalate"], "Devrait escalader pour retard")
        
        # TEST 2 : Focus livraison
        message2 = "Quand vais-je recevoir ma commande ? C'est urgent"
        result2 = self.detector.detect(message2)
        
        self.assertFalse(result2["is_uc_336"], f"Ne devrait PAS détecter UC_336: {result2}")
        
        # TEST 3 : Tracking
        message3 = "J'ai besoin du numéro de suivi de ma commande"
        result3 = self.detector.detect(message3)
        
        self.assertFalse(result3["is_uc_336"], f"Ne devrait PAS détecter UC_336: {result3}")
        
        print("✅ Tests négatifs passés")
    
    def test_days_extraction(self):
        """Test de l'extraction des jours"""
        
        # TEST 1 : "il y a X jours"
        message1 = "commande il y a 5 jours"
        result1 = self.detector.detect(message1)
        self.assertEqual(result1["days_since_order"], 5)
        
        # TEST 2 : "ça fait X jours"
        message2 = "ça fait 3 jours que j'ai commandé"
        result2 = self.detector.detect(message2)
        self.assertEqual(result2["days_since_order"], 3)
        
        # TEST 3 : "une semaine"
        message3 = "commande il y a une semaine"
        result3 = self.detector.detect(message3)
        self.assertEqual(result3["days_since_order"], 7)
        
        # TEST 4 : Données Odoo
        order_data = {
            "order_date": datetime.now() - timedelta(days=8)
        }
        message4 = "où en est ma commande"
        result4 = self.detector.detect(message4, order_data)
        self.assertEqual(result4["days_since_order"], 8)
        
        print("✅ Tests extraction jours passés")
    
    def test_escalation_logic(self):
        """Test de la logique d'escalade"""
        
        # TEST 1 : Pas d'escalade si < 12 jours
        message1 = "commande il y a 5 jours, où en est-elle ?"
        result1 = self.detector.detect(message1)
        self.assertFalse(result1["should_escalate"])
        
        # TEST 2 : Escalade si > 12 jours
        message2 = "commande il y a 15 jours, toujours pas de nouvelles"
        result2 = self.detector.detect(message2)
        self.assertTrue(result2["should_escalate"])
        
        print("✅ Tests escalade passés")

class TestUC336Responses(unittest.TestCase):
    """Tests pour les réponses UC_336"""
    
    def test_response_generation(self):
        """Test de génération des réponses"""
        
        # TEST 1 : Dans les délais
        detection_result = {
            "days_since_order": 5,
            "should_escalate": False
        }
        order_data = {
            "date": "2024-01-15",
            "status": "EN COURS"
        }
        
        response = generate_uc336_response(detection_result, order_data)
        
        self.assertIn("dans les délais normaux", response)
        self.assertIn("5 jours", response)
        self.assertNotIn("dans 2 heures", response)  # Pas de promesse
        
        # TEST 2 : Retard
        detection_result = {
            "days_since_order": 15,
            "should_escalate": True
        }
        
        response = generate_uc336_response(detection_result, order_data)
        
        self.assertIn("ESCALADE PRIORITAIRE", response)
        self.assertIn("15 jours", response)
        
        # TEST 3 : Pas de données
        detection_result = {
            "days_since_order": None,
            "should_escalate": False
        }
        
        response = generate_uc336_response(detection_result, None)
        
        self.assertIn("ESCALADE VERS ÉQUIPE SUPPORT", response)
        
        print("✅ Tests génération réponses passés")
    
    def test_response_safety(self):
        """Test de sécurité des réponses"""
        
        # TEST 1 : Réponse sûre
        safe_response = """
        Bonjour, je suis l'assistant automatique FlowUp.
        Votre commande est dans les délais normaux.
        """
        self.assertTrue(validate_response_safety(safe_response))
        
        # TEST 2 : Réponse dangereuse
        dangerous_response = """
        Je vais vous envoyer une mise à jour dans 2 heures.
        """
        self.assertFalse(validate_response_safety(dangerous_response))
        
        print("✅ Tests sécurité réponses passés")

def run_all_tests():
    """Lance tous les tests"""
    print("🧪 Tests UC_336 Detector")
    print("=" * 50)
    
    # Tests du détecteur
    detector_tests = TestUC336Detector()
    detector_tests.setUp()
    
    try:
        detector_tests.test_positive_cases()
        detector_tests.test_negative_cases()
        detector_tests.test_days_extraction()
        detector_tests.test_escalation_logic()
        print("✅ Tous les tests du détecteur passent !")
    except Exception as e:
        print(f"❌ Erreur tests détecteur: {e}")
        return False
    
    # Tests des réponses
    response_tests = TestUC336Responses()
    
    try:
        response_tests.test_response_generation()
        response_tests.test_response_safety()
        print("✅ Tous les tests des réponses passent !")
    except Exception as e:
        print(f"❌ Erreur tests réponses: {e}")
        return False
    
    print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
    return True

if __name__ == "__main__":
    run_all_tests()
