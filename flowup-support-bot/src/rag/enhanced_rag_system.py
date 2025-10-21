"""
Système RAG avancé avec mémoire contextuelle et apprentissage
Implémentation du plan d'optimisation avec recherche hybride
"""

import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# Simulation des imports (à remplacer par les vrais)
try:
    from sentence_transformers import SentenceTransformer
    from chromadb import ChromaDB
except ImportError:
    # Fallback pour les tests
    class SentenceTransformer:
        def encode(self, texts): return np.random.rand(len(texts), 384)
    class ChromaDB:
        def __init__(self, **kwargs): pass
        def query(self, **kwargs): return {"documents": [], "distances": []}

@dataclass
class ConversationMemory:
    """Mémoire des conversations pour apprentissage"""
    interactions: List[Dict]
    max_memory: int = 1000
    
    def save_interaction(self, query: str, response: str, context: Dict):
        """Sauvegarde une interaction pour apprentissage"""
        interaction = {
            "timestamp": datetime.now(),
            "query": query,
            "response": response,
            "context": context,
            "success": self._evaluate_success(response)
        }
        
        self.interactions.append(interaction)
        
        # Garder seulement les N dernières interactions
        if len(self.interactions) > self.max_memory:
            self.interactions = self.interactions[-self.max_memory:]
    
    def _evaluate_success(self, response: str) -> bool:
        """Évalue le succès d'une réponse"""
        # Critères simples pour l'instant
        success_indicators = ["✅", "résolu", "solution", "aide"]
        failure_indicators = ["❌", "erreur", "impossible", "escalade"]
        
        success_score = sum(1 for indicator in success_indicators if indicator in response.lower())
        failure_score = sum(1 for indicator in failure_indicators if indicator in response.lower())
        
        return success_score > failure_score

class EnhancedRAGSystem:
    """
    Système RAG avancé avec mémoire contextuelle et apprentissage
    
    FONCTIONNALITÉS:
    - Recherche hybride (sémantique + mots-clés)
    - Mémoire contextuelle
    - Ranking intelligent
    - Apprentissage continu
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialisation des composants
        self.embeddings = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.vector_store = ChromaDB(
            collection="flowup_tickets",
            embedding_function=self.embeddings
        )
        self.memory = ConversationMemory()
        
        # Configuration
        self.search_config = {
            "semantic_weight": 0.6,
            "keyword_weight": 0.4,
            "recency_weight": 0.3,
            "relevance_weight": 0.4,
            "resolution_weight": 0.3,
            "max_results": 10,
            "similarity_threshold": 0.7
        }
        
        # Base de connaissances
        self.knowledge_base = self._load_knowledge_base()
        
    def process_query(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """
        Traite une requête avec le système RAG avancé
        
        Args:
            query: Requête du client
            context: Contexte de la commande
            
        Returns:
            Dict avec réponse, sources, confiance
        """
        try:
            # 1. Enrichissement de la requête
            enriched_query = self._enrich_query(query, context)
            
            # 2. Recherche hybride
            similar_tickets = self._hybrid_search(enriched_query, context)
            
            # 3. Ranking intelligent
            ranked_results = self._rerank_results(similar_tickets, context)
            
            # 4. Génération de réponse
            response = self._generate_response(query, ranked_results, context)
            
            # 5. Sauvegarde pour apprentissage
            self.memory.save_interaction(query, response, context)
            
            return {
                "response": response,
                "sources": ranked_results[:5],
                "confidence": self._calculate_confidence(ranked_results),
                "query_enriched": enriched_query,
                "search_metadata": {
                    "total_results": len(similar_tickets),
                    "filtered_results": len(ranked_results),
                    "search_time": datetime.now()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erreur RAG: {str(e)}")
            return self._get_fallback_response(query, context)
    
    def _enrich_query(self, query: str, context: Dict = None) -> str:
        """Enrichit la requête avec le contexte"""
        enriched_parts = [query]
        
        if context:
            # Ajouter contexte client
            if context.get('customer_name'):
                enriched_parts.append(f"Client: {context['customer_name']}")
            
            # Ajouter contexte commande
            if context.get('order_status'):
                enriched_parts.append(f"Statut commande: {context['order_status']}")
            
            # Ajouter contexte produits
            if context.get('gpu_products'):
                gpu_names = [p.get('name', '') for p in context['gpu_products']]
                enriched_parts.append(f"Produits GPU: {', '.join(gpu_names)}")
            
            # Ajouter contexte problèmes
            if context.get('critical_issues'):
                issues = context['critical_issues']
                enriched_parts.append(f"Problèmes: {', '.join(issues)}")
        
        return " ".join(enriched_parts)
    
    def _hybrid_search(self, query: str, context: Dict = None) -> List[Dict]:
        """Recherche hybride sémantique + mots-clés"""
        results = []
        
        # 1. Recherche sémantique
        semantic_results = self._semantic_search(query)
        
        # 2. Recherche par mots-clés
        keyword_results = self._keyword_search(query)
        
        # 3. Fusion des résultats
        all_results = semantic_results + keyword_results
        
        # 4. Déduplication
        unique_results = self._deduplicate_results(all_results)
        
        # 5. Application des filtres
        filtered_results = self._apply_filters(unique_results, context)
        
        return filtered_results
    
    def _semantic_search(self, query: str) -> List[Dict]:
        """Recherche sémantique avec embeddings"""
        try:
            # Encoder la requête
            query_embedding = self.embeddings.encode([query])
            
            # Recherche dans la base vectorielle
            results = self.vector_store.query(
                query_embeddings=query_embedding,
                n_results=self.search_config["max_results"]
            )
            
            # Formater les résultats
            semantic_results = []
            for i, doc in enumerate(results.get("documents", [[]])[0]):
                semantic_results.append({
                    "content": doc,
                    "similarity": 1 - results.get("distances", [[]])[0][i],
                    "type": "semantic",
                    "source": "vector_store"
                })
            
            return semantic_results
            
        except Exception as e:
            self.logger.error(f"Erreur recherche sémantique: {str(e)}")
            return []
    
    def _keyword_search(self, query: str) -> List[Dict]:
        """Recherche par mots-clés"""
        try:
            # Extraire les mots-clés importants
            keywords = self._extract_keywords(query)
            
            # Recherche dans la base de connaissances
            keyword_results = []
            for kb_item in self.knowledge_base:
                score = self._calculate_keyword_score(kb_item, keywords)
                if score > 0.3:  # Seuil minimum
                    keyword_results.append({
                        "content": kb_item.get("content", ""),
                        "similarity": score,
                        "type": "keyword",
                        "source": "knowledge_base",
                        "metadata": kb_item.get("metadata", {})
                    })
            
            return keyword_results
            
        except Exception as e:
            self.logger.error(f"Erreur recherche mots-clés: {str(e)}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extrait les mots-clés importants de la requête"""
        # Mots-clés techniques
        technical_keywords = [
            "carte graphique", "gpu", "rtx", "gtx", "graphics",
            "processeur", "cpu", "intel", "amd",
            "ram", "mémoire", "stockage", "ssd", "hdd",
            "écran", "moniteur", "clavier", "souris"
        ]
        
        # Mots-clés problèmes
        problem_keywords = [
            "problème", "bug", "erreur", "crash", "freeze",
            "ne fonctionne pas", "défaillant", "cassé"
        ]
        
        # Mots-clés statut
        status_keywords = [
            "statut", "où en est", "avancement", "progression",
            "délai", "quand", "recevoir", "livraison"
        ]
        
        all_keywords = technical_keywords + problem_keywords + status_keywords
        found_keywords = []
        
        query_lower = query.lower()
        for keyword in all_keywords:
            if keyword in query_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _calculate_keyword_score(self, kb_item: Dict, keywords: List[str]) -> float:
        """Calcule le score de correspondance mots-clés"""
        content = kb_item.get("content", "").lower()
        matches = sum(1 for keyword in keywords if keyword in content)
        
        if not keywords:
            return 0.0
        
        return matches / len(keywords)
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Déduplique les résultats"""
        seen_contents = set()
        unique_results = []
        
        for result in results:
            content_hash = hash(result.get("content", ""))
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _apply_filters(self, results: List[Dict], context: Dict = None) -> List[Dict]:
        """Applique les filtres contextuels"""
        if not context:
            return results
        
        filtered_results = []
        
        for result in results:
            # Filtrer par UC si spécifié
            if context.get("uc_detected"):
                if self._matches_uc(result, context["uc_detected"]):
                    filtered_results.append(result)
            else:
                filtered_results.append(result)
        
        return filtered_results
    
    def _matches_uc(self, result: Dict, uc: str) -> bool:
        """Vérifie si le résultat correspond à l'UC"""
        content = result.get("content", "").lower()
        
        uc_keywords = {
            "UC_263": ["carte graphique", "gpu", "graphics", "rtx", "gtx"],
            "UC_336": ["statut", "où en est", "avancement"],
            "UC_337": ["délai", "quand", "recevoir", "livraison"],
            "UC_421": ["suivi", "tracking", "numéro"]
        }
        
        if uc in uc_keywords:
            return any(keyword in content for keyword in uc_keywords[uc])
        
        return True
    
    def _rerank_results(self, results: List[Dict], context: Dict = None) -> List[Dict]:
        """Re-classe les résultats avec ranking intelligent"""
        for result in results:
            # Score de pertinence
            relevance_score = result.get("similarity", 0.0)
            
            # Score de récence
            recency_score = self._calculate_recency_score(result)
            
            # Score de résolution
            resolution_score = self._calculate_resolution_score(result)
            
            # Score final pondéré
            final_score = (
                relevance_score * self.search_config["relevance_weight"] +
                recency_score * self.search_config["recency_weight"] +
                resolution_score * self.search_config["resolution_weight"]
            )
            
            result["final_score"] = final_score
        
        # Trier par score final
        return sorted(results, key=lambda x: x.get("final_score", 0), reverse=True)
    
    def _calculate_recency_score(self, result: Dict) -> float:
        """Calcule le score de récence"""
        # Pour l'instant, score basé sur le type de source
        source = result.get("source", "")
        if source == "vector_store":
            return 0.8  # Plus récent
        elif source == "knowledge_base":
            return 0.6  # Moyennement récent
        else:
            return 0.4  # Moins récent
    
    def _calculate_resolution_score(self, result: Dict) -> float:
        """Calcule le score de résolution"""
        content = result.get("content", "").lower()
        
        # Indicateurs de résolution
        resolution_indicators = ["résolu", "solution", "corrigé", "réparé", "fonctionne"]
        problem_indicators = ["problème", "erreur", "bug", "ne fonctionne pas"]
        
        resolution_count = sum(1 for indicator in resolution_indicators if indicator in content)
        problem_count = sum(1 for indicator in problem_indicators if indicator in content)
        
        if resolution_count > 0 and problem_count == 0:
            return 1.0  # Résolution claire
        elif resolution_count > problem_count:
            return 0.7  # Probablement résolu
        else:
            return 0.3  # Pas de résolution claire
    
    def _generate_response(self, query: str, ranked_results: List[Dict], context: Dict = None) -> str:
        """Génère la réponse basée sur les résultats"""
        if not ranked_results:
            return self._get_no_results_response(query, context)
        
        # Prendre les 3 meilleurs résultats
        top_results = ranked_results[:3]
        
        # Générer la réponse
        response_parts = []
        
        # Introduction
        response_parts.append("Bonjour, je suis l'assistant automatique FlowUp.")
        
        # Analyse des résultats
        if len(top_results) == 1:
            response_parts.append(self._format_single_result(top_results[0], context))
        else:
            response_parts.append(self._format_multiple_results(top_results, context))
        
        # Conclusion
        response_parts.append("Puis-je vous aider pour autre chose ?")
        
        return "\n\n".join(response_parts)
    
    def _format_single_result(self, result: Dict, context: Dict = None) -> str:
        """Formate un résultat unique"""
        content = result.get("content", "")
        confidence = result.get("final_score", 0.0)
        
        if confidence > 0.8:
            return f"✅ {content}"
        elif confidence > 0.6:
            return f"📋 {content}"
        else:
            return f"ℹ️ {content}"
    
    def _format_multiple_results(self, results: List[Dict], context: Dict = None) -> str:
        """Formate plusieurs résultats"""
        response_parts = []
        
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            confidence = result.get("final_score", 0.0)
            
            if confidence > 0.7:
                response_parts.append(f"✅ Solution {i}: {content}")
            else:
                response_parts.append(f"📋 Information {i}: {content}")
        
        return "\n".join(response_parts)
    
    def _calculate_confidence(self, ranked_results: List[Dict]) -> float:
        """Calcule la confiance globale"""
        if not ranked_results:
            return 0.0
        
        # Moyenne pondérée des scores
        total_score = sum(result.get("final_score", 0.0) for result in ranked_results)
        return min(total_score / len(ranked_results), 1.0)
    
    def _get_no_results_response(self, query: str, context: Dict = None) -> str:
        """Réponse quand aucun résultat trouvé"""
        return """
Je n'ai pas trouvé d'informations spécifiques pour votre demande.

Je vais transférer votre demande à un opérateur qui pourra mieux vous aider.

Un membre de notre équipe vous contactera dans les plus brefs délais.
        """.strip()
    
    def _get_fallback_response(self, query: str, context: Dict = None) -> str:
        """Réponse de fallback en cas d'erreur"""
        return """
Je rencontre un problème technique momentané.

Je transfère votre demande à un opérateur qui pourra vous aider immédiatement.

Merci de votre patience.
        """.strip()
    
    def _load_knowledge_base(self) -> List[Dict]:
        """Charge la base de connaissances"""
        # Base de connaissances simulée
        return [
            {
                "content": "Problème carte graphique RTX 4080: Vérifier les drivers, température, et connexions",
                "metadata": {"uc": "UC_263", "category": "technical"},
                "tags": ["gpu", "rtx", "problème", "technique"]
            },
            {
                "content": "Statut commande: Vérifier dans Odoo le statut actuel et les délais",
                "metadata": {"uc": "UC_336", "category": "delivery"},
                "tags": ["statut", "commande", "délai"]
            },
            {
                "content": "Délai livraison: 12 jours ouvrés maximum selon la loi",
                "metadata": {"uc": "UC_337", "category": "delivery"},
                "tags": ["délai", "livraison", "loi"]
            }
        ]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système"""
        return {
            "total_interactions": len(self.memory.interactions),
            "success_rate": self._calculate_success_rate(),
            "knowledge_base_size": len(self.knowledge_base),
            "search_config": self.search_config,
            "last_update": datetime.now()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calcule le taux de succès"""
        if not self.memory.interactions:
            return 0.0
        
        successful = sum(1 for interaction in self.memory.interactions 
                       if interaction.get("success", False))
        
        return successful / len(self.memory.interactions)

# Test du système RAG avancé
def test_enhanced_rag():
    """Test du système RAG avancé"""
    rag = EnhancedRAGSystem()
    
    test_queries = [
        {
            "query": "Ma carte graphique ne fonctionne plus",
            "context": {"uc_detected": "UC_263", "has_gpu": True}
        },
        {
            "query": "Où en est ma commande ?",
            "context": {"uc_detected": "UC_336", "has_order": True}
        }
    ]
    
    print("🧪 TEST SYSTÈME RAG AVANCÉ")
    print("=" * 35)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. Requête: {test['query']}")
        
        result = rag.process_query(test['query'], test['context'])
        
        print(f"   Réponse: {result['response'][:100]}...")
        print(f"   Confiance: {result['confidence']:.1%}")
        print(f"   Sources: {len(result['sources'])}")
        
        if result['sources']:
            print(f"   Meilleure source: {result['sources'][0]['content'][:50]}...")

if __name__ == "__main__":
    test_enhanced_rag()
