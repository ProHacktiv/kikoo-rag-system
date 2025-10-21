"""
Context retriever for the flowup-support-bot.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from .knowledge_base import KnowledgeBase
from ..utils.logger import get_logger


class ContextRetriever:
    """
    Retrieve relevant context for queries using RAG system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the context retriever.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.embedding_generator = EmbeddingGenerator(config['rag'])
        self.vector_store = VectorStore(config['rag'])
        self.knowledge_base = KnowledgeBase(config)
        
        # Configuration
        self.similarity_threshold = config['rag'].get('similarity_threshold', 0.7)
        self.max_results = config['rag'].get('max_results', 5)
        self.chunk_size = config['rag'].get('chunk_size', 1000)
        self.chunk_overlap = config['rag'].get('chunk_overlap', 200)
    
    async def retrieve_context(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: Query text
            filters: Optional filters for retrieval
            
        Returns:
            Retrieved context information
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_single_embedding(query)
            
            # Search vector store
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=self.max_results,
                where=filters
            )
            
            # Filter by similarity threshold
            relevant_results = [
                result for result in search_results
                if result['similarity'] >= self.similarity_threshold
            ]
            
            # Format context
            context = {
                'query': query,
                'results': relevant_results,
                'total_results': len(search_results),
                'relevant_results': len(relevant_results),
                'sources': [result['metadata'].get('source', 'unknown') for result in relevant_results],
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Retrieved {len(relevant_results)} relevant results for query")
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            return {
                'query': query,
                'results': [],
                'total_results': 0,
                'relevant_results': 0,
                'sources': [],
                'error': str(e),
                'retrieved_at': datetime.utcnow().isoformat()
            }
    
    async def retrieve_similar_tickets(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar resolved tickets.
        
        Args:
            query: Query text
            limit: Maximum number of results
            
        Returns:
            List of similar tickets
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_single_embedding(query)
            
            # Search for similar tickets
            filters = {'type': 'resolved_ticket'}
            results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=limit,
                where=filters
            )
            
            # Format ticket results
            tickets = []
            for result in results:
                if result['similarity'] >= self.similarity_threshold:
                    tickets.append({
                        'ticket_id': result['metadata'].get('ticket_id'),
                        'subject': result['metadata'].get('subject'),
                        'solution': result['document'],
                        'similarity': result['similarity'],
                        'resolved_at': result['metadata'].get('resolved_at'),
                        'category': result['metadata'].get('category')
                    })
            
            return tickets
            
        except Exception as e:
            self.logger.error(f"Error retrieving similar tickets: {str(e)}")
            return []
    
    async def retrieve_knowledge_articles(self, query: str, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge articles.
        
        Args:
            query: Query text
            category: Optional category filter
            limit: Maximum number of results
            
        Returns:
            List of knowledge articles
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_single_embedding(query)
            
            # Set up filters
            filters = {'type': 'knowledge_article'}
            if category:
                filters['category'] = category
            
            # Search for articles
            results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=limit,
                where=filters
            )
            
            # Format article results
            articles = []
            for result in results:
                if result['similarity'] >= self.similarity_threshold:
                    articles.append({
                        'article_id': result['metadata'].get('article_id'),
                        'title': result['metadata'].get('title'),
                        'content': result['document'],
                        'similarity': result['similarity'],
                        'category': result['metadata'].get('category'),
                        'last_updated': result['metadata'].get('last_updated')
                    })
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error retrieving knowledge articles: {str(e)}")
            return []
    
    async def retrieve_procedures(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant procedures.
        
        Args:
            query: Query text
            limit: Maximum number of results
            
        Returns:
            List of procedures
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_single_embedding(query)
            
            # Search for procedures
            filters = {'type': 'procedure'}
            results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=limit,
                where=filters
            )
            
            # Format procedure results
            procedures = []
            for result in results:
                if result['similarity'] >= self.similarity_threshold:
                    procedures.append({
                        'procedure_id': result['metadata'].get('procedure_id'),
                        'title': result['metadata'].get('title'),
                        'steps': result['document'],
                        'similarity': result['similarity'],
                        'category': result['metadata'].get('category'),
                        'difficulty': result['metadata'].get('difficulty')
                    })
            
            return procedures
            
        except Exception as e:
            self.logger.error(f"Error retrieving procedures: {str(e)}")
            return []
    
    async def retrieve_faq(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant FAQ entries.
        
        Args:
            query: Query text
            limit: Maximum number of results
            
        Returns:
            List of FAQ entries
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_single_embedding(query)
            
            # Search for FAQ entries
            filters = {'type': 'faq'}
            results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=limit,
                where=filters
            )
            
            # Format FAQ results
            faq_entries = []
            for result in results:
                if result['similarity'] >= self.similarity_threshold:
                    faq_entries.append({
                        'faq_id': result['metadata'].get('faq_id'),
                        'question': result['metadata'].get('question'),
                        'answer': result['document'],
                        'similarity': result['similarity'],
                        'category': result['metadata'].get('category'),
                        'tags': result['metadata'].get('tags', [])
                    })
            
            return faq_entries
            
        except Exception as e:
            self.logger.error(f"Error retrieving FAQ: {str(e)}")
            return []
    
    async def retrieve_comprehensive_context(self, query: str, intent: str = None) -> Dict[str, Any]:
        """
        Retrieve comprehensive context from all sources.
        
        Args:
            query: Query text
            intent: Intent category for filtering
            
        Returns:
            Comprehensive context
        """
        try:
            # Set up filters based on intent
            filters = None
            if intent:
                filters = {'category': intent}
            
            # Retrieve from all sources
            context = await self.retrieve_context(query, filters)
            tickets = await self.retrieve_similar_tickets(query)
            articles = await self.retrieve_knowledge_articles(query, intent)
            procedures = await self.retrieve_procedures(query)
            faq = await self.retrieve_faq(query)
            
            # Combine all results
            comprehensive_context = {
                'query': query,
                'intent': intent,
                'general_context': context,
                'similar_tickets': tickets,
                'knowledge_articles': articles,
                'procedures': procedures,
                'faq': faq,
                'total_sources': len(context['sources']) + len(tickets) + len(articles) + len(procedures) + len(faq),
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
            return comprehensive_context
            
        except Exception as e:
            self.logger.error(f"Error retrieving comprehensive context: {str(e)}")
            return {
                'query': query,
                'intent': intent,
                'error': str(e),
                'retrieved_at': datetime.utcnow().isoformat()
            }
    
    def rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rank results by relevance.
        
        Args:
            results: List of results to rank
            query: Original query
            
        Returns:
            Ranked results
        """
        try:
            # Sort by similarity score
            ranked_results = sorted(
                results,
                key=lambda x: x.get('similarity', 0),
                reverse=True
            )
            
            return ranked_results
            
        except Exception as e:
            self.logger.error(f"Error ranking results: {str(e)}")
            return results
    
    def filter_by_relevance(self, results: List[Dict[str, Any]], min_similarity: float = None) -> List[Dict[str, Any]]:
        """
        Filter results by relevance threshold.
        
        Args:
            results: List of results to filter
            min_similarity: Minimum similarity threshold
            
        Returns:
            Filtered results
        """
        try:
            if min_similarity is None:
                min_similarity = self.similarity_threshold
            
            filtered_results = [
                result for result in results
                if result.get('similarity', 0) >= min_similarity
            ]
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error filtering results: {str(e)}")
            return results
    
    def get_context_summary(self, context: Dict[str, Any]) -> str:
        """
        Generate a summary of the retrieved context.
        
        Args:
            context: Retrieved context
            
        Returns:
            Context summary
        """
        try:
            summary_parts = []
            
            # Add general context
            if context.get('general_context', {}).get('relevant_results', 0) > 0:
                summary_parts.append(f"Found {context['general_context']['relevant_results']} relevant documents")
            
            # Add similar tickets
            if context.get('similar_tickets'):
                summary_parts.append(f"Found {len(context['similar_tickets'])} similar resolved tickets")
            
            # Add knowledge articles
            if context.get('knowledge_articles'):
                summary_parts.append(f"Found {len(context['knowledge_articles'])} knowledge articles")
            
            # Add procedures
            if context.get('procedures'):
                summary_parts.append(f"Found {len(context['procedures'])} procedures")
            
            # Add FAQ
            if context.get('faq'):
                summary_parts.append(f"Found {len(context['faq'])} FAQ entries")
            
            if summary_parts:
                return f"Context retrieved: {', '.join(summary_parts)}"
            else:
                return "No relevant context found"
                
        except Exception as e:
            self.logger.error(f"Error generating context summary: {str(e)}")
            return "Error generating context summary"
    
    def __str__(self) -> str:
        """
        String representation of ContextRetriever.
        
        Returns:
            String representation
        """
        return f"ContextRetriever(threshold={self.similarity_threshold}, max_results={self.max_results})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation of ContextRetriever.
        
        Returns:
            Detailed string representation
        """
        return f"ContextRetriever(similarity_threshold={self.similarity_threshold}, max_results={self.max_results}, chunk_size={self.chunk_size})"
