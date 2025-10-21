#!/usr/bin/env python3
"""
Script pour traiter tous les tickets UC avec le bot FlowUp
Génère les réponses dans les fichiers .md
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.flowup_chatbot import FlowUpChatbot

class UCTicketProcessor:
    """Processeur pour tous les tickets UC"""
    
    def __init__(self):
        self.chatbot = FlowUpChatbot()
        self.data_dir = Path("data/uc_validation_files_real")
        self.results_dir = Path("data/bot_responses")
        self.results_dir.mkdir(exist_ok=True)
        
        # Statistiques globales
        self.stats = {
            "total_tickets": 0,
            "successful_responses": 0,
            "escalations": 0,
            "uc_detections": {},
            "categories": {},
            "errors": []
        }
    
    def process_all_uc_files(self):
        """Traite tous les fichiers UC"""
        print("🤖 FlowUp Bot - Traitement de tous les tickets UC")
        print("=" * 60)
        
        # Lister tous les fichiers UC
        uc_files = list(self.data_dir.glob("UC_*_REAL_validation.md"))
        print(f"📁 {len(uc_files)} fichiers UC trouvés")
        
        for uc_file in uc_files:
            print(f"\n🔄 Traitement de {uc_file.name}")
            self.process_uc_file(uc_file)
        
        # Générer le rapport final
        self.generate_final_report()
    
    def process_uc_file(self, uc_file: Path):
        """Traite un fichier UC spécifique"""
        try:
            # Lire le fichier
            content = uc_file.read_text(encoding='utf-8')
            
            # Extraire les tickets
            tickets = self.extract_tickets_from_content(content)
            print(f"  📋 {len(tickets)} tickets trouvés")
            
            # Traiter chaque ticket
            responses = []
            for ticket in tickets:
                response = self.process_single_ticket(ticket)
                responses.append(response)
            
            # Générer le fichier de réponses
            self.generate_uc_response_file(uc_file, responses)
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            self.stats["errors"].append(f"{uc_file.name}: {e}")
    
    def extract_tickets_from_content(self, content: str) -> list:
        """Extrait les tickets du contenu markdown"""
        tickets = []
        
        # Pattern pour trouver les tickets
        ticket_pattern = r'## 🎫 TICKET #(\d+)\s*\n\n### 📋 Informations du Ticket\s*\n- \*\*ID\*\* : (\d+)\s*\n- \*\*Référence\*\* : ([^\n]+)\s*\n- \*\*Catégorie L1\*\* : ([^\n]+)\s*\n- \*\*Catégorie L2\*\* : ([^\n]+)\s*\n- \*\*Catégorie L3\*\* : ([^\n]+)\s*\n- \*\*UC ID\*\* : (\d+)\s*\n- \*\*Date création\*\* : ([^\n]+)\s*\n- \*\*Date résolution\*\* : ([^\n]+)\s*\n- \*\*Priorité\*\* : (\d+)\s*\n- \*\*Escalade\*\* : ([^\n]+)\s*\n\n### 💬 Message Original du Client\s*\n```\s*\n([^`]+)\s*\n```'
        
        matches = re.findall(ticket_pattern, content, re.DOTALL)
        
        for match in matches:
            ticket = {
                "ticket_number": match[0],
                "id": match[1],
                "reference": match[2],
                "category_l1": match[3],
                "category_l2": match[4],
                "category_l3": match[5],
                "uc_id": match[6],
                "creation_date": match[7],
                "resolution_date": match[8],
                "priority": match[9],
                "escalation": match[10],
                "message": match[11].strip()
            }
            tickets.append(ticket)
        
        return tickets
    
    def process_single_ticket(self, ticket: dict) -> dict:
        """Traite un ticket individuel"""
        try:
            # Créer le contexte
            context = {
                "ticket_id": ticket["id"],
                "uc_expected": ticket["uc_id"],
                "category_expected": ticket["category_l1"],
                "creation_date": ticket["creation_date"]
            }
            
            # Traiter avec le bot
            response = self.chatbot.process_message(
                message=ticket["message"],
                context=context
            )
            
            # Mettre à jour les statistiques
            self.stats["total_tickets"] += 1
            self.stats["successful_responses"] += 1
            
            if response.requires_escalation:
                self.stats["escalations"] += 1
            
            # Statistiques par UC
            uc_id = response.uc_detected.uc_id
            if uc_id not in self.stats["uc_detections"]:
                self.stats["uc_detections"][uc_id] = 0
            self.stats["uc_detections"][uc_id] += 1
            
            # Statistiques par catégorie
            category = response.uc_detected.category.value
            if category not in self.stats["categories"]:
                self.stats["categories"][category] = 0
            self.stats["categories"][category] += 1
            
            return {
                "ticket_info": ticket,
                "bot_response": {
                    "uc_detected": response.uc_detected.uc_id,
                    "confidence": response.uc_detected.confidence,
                    "category": response.uc_detected.category.value,
                    "priority": response.uc_detected.priority.value,
                    "escalation": response.requires_escalation,
                    "escalation_reason": response.escalation_reason,
                    "response_content": response.content
                },
                "evaluation": self.evaluate_response(ticket, response)
            }
            
        except Exception as e:
            print(f"    ❌ Erreur ticket {ticket['id']}: {e}")
            self.stats["errors"].append(f"Ticket {ticket['id']}: {e}")
            return {
                "ticket_info": ticket,
                "error": str(e)
            }
    
    def evaluate_response(self, ticket: dict, response) -> dict:
        """Évalue la qualité de la réponse"""
        evaluation = {
            "category_match": ticket["category_l1"] == response.uc_detected.category.value,
            "uc_match": ticket["uc_id"] == response.uc_detected.uc_id,
            "confidence_score": response.uc_detected.confidence,
            "escalation_correct": self.check_escalation_correctness(ticket, response),
            "response_quality": self.assess_response_quality(response),
            "overall_score": 0
        }
        
        # Calculer le score global
        score = 0
        if evaluation["category_match"]:
            score += 40
        if evaluation["uc_match"]:
            score += 40
        score += int(evaluation["confidence_score"] * 20)
        
        evaluation["overall_score"] = score
        return evaluation
    
    def check_escalation_correctness(self, ticket: dict, response) -> bool:
        """Vérifie si l'escalade est correcte"""
        # Si le ticket original était escaladé, le bot devrait aussi escalader
        original_escalation = ticket["escalation"] == "OUI"
        bot_escalation = response.requires_escalation
        
        return original_escalation == bot_escalation
    
    def assess_response_quality(self, response) -> str:
        """Évalue la qualité de la réponse"""
        content = response.content.lower()
        
        # Vérifier la présence d'éléments clés
        has_greeting = "bonjour" in content or "assistant" in content
        has_solution = any(word in content for word in ["solution", "étape", "vérifier", "tester"])
        has_escalation = response.requires_escalation and "escalade" in content
        
        if has_greeting and (has_solution or has_escalation):
            return "EXCELLENT"
        elif has_greeting:
            return "GOOD"
        else:
            return "POOR"
    
    def generate_uc_response_file(self, uc_file: Path, responses: list):
        """Génère le fichier de réponses pour un UC"""
        uc_name = uc_file.stem.replace("_REAL_validation", "")
        
        # Créer le contenu markdown
        content = f"""# 🤖 RÉPONSES BOT FLOWUP - {uc_name}
*Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*

## 📊 Statistiques du Traitement
- **Total tickets traités** : {len(responses)}
- **Réponses réussies** : {len([r for r in responses if 'error' not in r])}
- **Escalades détectées** : {len([r for r in responses if r.get('bot_response', {}).get('escalation', False)])}
- **Taux de succès** : {len([r for r in responses if 'error' not in r])/len(responses)*100:.1f}%

---

"""
        
        # Ajouter chaque réponse
        for i, response in enumerate(responses, 1):
            if 'error' in response:
                content += f"""## ❌ TICKET #{i} - ERREUR

**ID** : {response['ticket_info']['id']}
**Erreur** : {response['error']}

---

"""
            else:
                ticket_info = response['ticket_info']
                bot_response = response['bot_response']
                evaluation = response['evaluation']
                
                content += f"""## 🎫 TICKET #{i}

### 📋 Informations Originales
- **ID** : {ticket_info['id']}
- **Référence** : {ticket_info['reference']}
- **UC Attendu** : {ticket_info['uc_id']}
- **Catégorie Attendue** : {ticket_info['category_l1']}

### 💬 Message Original
```
{ticket_info['message']}
```

### 🤖 Réponse du Bot FlowUp
**UC Détecté** : {bot_response['uc_detected']} (Confiance: {bot_response['confidence']:.1%})
**Catégorie** : {bot_response['category']}
**Priorité** : {bot_response['priority']}
**Escalade** : {'OUI' if bot_response['escalation'] else 'NON'}

```
{bot_response['response_content']}
```

### 📊 Évaluation
- **Correspondance Catégorie** : {'✅' if evaluation['category_match'] else '❌'}
- **Correspondance UC** : {'✅' if evaluation['uc_match'] else '❌'}
- **Score Global** : {evaluation['overall_score']}/100
- **Qualité Réponse** : {evaluation['response_quality']}

---

"""
        
        # Sauvegarder le fichier
        output_file = self.results_dir / f"{uc_name}_BOT_RESPONSES.md"
        output_file.write_text(content, encoding='utf-8')
        print(f"  💾 Réponses sauvegardées: {output_file.name}")
    
    def generate_final_report(self):
        """Génère le rapport final"""
        report_content = f"""# 📊 RAPPORT FINAL - TRAITEMENT DE TOUS LES TICKETS UC
*Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*

## 🎯 Statistiques Globales
- **Total tickets traités** : {self.stats['total_tickets']}
- **Réponses réussies** : {self.stats['successful_responses']}
- **Taux de succès** : {self.stats['successful_responses']/self.stats['total_tickets']*100:.1f}%
- **Escalades détectées** : {self.stats['escalations']}
- **Taux d'escalade** : {self.stats['escalations']/self.stats['total_tickets']*100:.1f}%

## 📋 Distribution par UC
"""
        
        for uc_id, count in sorted(self.stats['uc_detections'].items()):
            report_content += f"- **{uc_id}** : {count} tickets\n"
        
        report_content += f"""
## 📊 Distribution par Catégorie
"""
        
        for category, count in sorted(self.stats['categories'].items()):
            report_content += f"- **{category}** : {count} tickets\n"
        
        if self.stats['errors']:
            report_content += f"""
## ❌ Erreurs Rencontrées
"""
            for error in self.stats['errors']:
                report_content += f"- {error}\n"
        
        report_content += f"""
## 🎉 Résumé
Le bot FlowUp a traité avec succès {self.stats['successful_responses']} tickets sur {self.stats['total_tickets']} au total.

Tous les fichiers de réponses ont été générés dans le dossier `data/bot_responses/`.
"""
        
        # Sauvegarder le rapport
        report_file = self.results_dir / "RAPPORT_FINAL_BOT_RESPONSES.md"
        report_file.write_text(report_content, encoding='utf-8')
        
        print(f"\n📊 RAPPORT FINAL GÉNÉRÉ")
        print(f"✅ Tickets traités: {self.stats['total_tickets']}")
        print(f"✅ Réponses réussies: {self.stats['successful_responses']}")
        print(f"✅ Taux de succès: {self.stats['successful_responses']/self.stats['total_tickets']*100:.1f}%")
        print(f"✅ Escalades: {self.stats['escalations']}")
        print(f"💾 Rapport sauvegardé: {report_file.name}")

def main():
    """Fonction principale"""
    processor = UCTicketProcessor()
    processor.process_all_uc_files()

if __name__ == "__main__":
    main()
