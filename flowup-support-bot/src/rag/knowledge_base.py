"""
Knowledge base management for the flowup-support-bot.
"""

import os
import json
import yaml
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import glob

from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from ..utils.logger import get_logger


class KnowledgeBase:
    """
    Manage the knowledge base for the RAG system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the knowledge base.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.embedding_generator = EmbeddingGenerator(config['rag'])
        self.vector_store = VectorStore(config['rag'])
        
        # Configuration
        self.knowledge_base_path = config.get('knowledge_base_path', 'data/knowledge_base')
        self.chunk_size = config['rag'].get('chunk_size', 1000)
        self.chunk_overlap = config['rag'].get('chunk_overlap', 200)
    
    async def load_knowledge_base(self) -> bool:
        """
        Load the entire knowledge base into the vector store.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info("Loading knowledge base...")
            
            # Load different types of knowledge
            await self._load_resolved_tickets()
            await self._load_procedures()
            await self._load_faq()
            await self._load_knowledge_articles()
            
            self.logger.info("Knowledge base loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {str(e)}")
            return False
    
    async def _load_resolved_tickets(self) -> None:
        """
        Load resolved tickets into the vector store.
        """
        try:
            tickets_path = os.path.join(self.knowledge_base_path, 'tickets_resolved')
            if not os.path.exists(tickets_path):
                self.logger.warning(f"Resolved tickets directory not found: {tickets_path}")
                return
            
            # Find all ticket files
            ticket_files = glob.glob(os.path.join(tickets_path, '*.json'))
            
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for ticket_file in ticket_files:
                with open(ticket_file, 'r', encoding='utf-8') as f:
                    ticket_data = json.load(f)
                
                # Extract ticket information
                ticket_id = ticket_data.get('id', 'unknown')
                subject = ticket_data.get('subject', '')
                solution = ticket_data.get('solution', '')
                category = ticket_data.get('category', 'unknown')
                resolved_at = ticket_data.get('resolved_at', '')
                
                # Create document content
                document = f"Subject: {subject}\n\nSolution: {solution}"
                
                # Generate embedding
                embedding = self.embedding_generator.generate_single_embedding(document)
                
                # Create metadata
                metadata = {
                    'type': 'resolved_ticket',
                    'ticket_id': ticket_id,
                    'subject': subject,
                    'category': category,
                    'resolved_at': resolved_at,
                    'source': 'resolved_tickets'
                }
                
                documents.append(document)
                embeddings.append(embedding)
                metadatas.append(metadata)
                ids.append(f"ticket_{ticket_id}")
            
            if documents:
                self.vector_store.add_documents(documents, np.array(embeddings), metadatas, ids)
                self.logger.info(f"Loaded {len(documents)} resolved tickets")
            
        except Exception as e:
            self.logger.error(f"Error loading resolved tickets: {str(e)}")
    
    async def _load_procedures(self) -> None:
        """
        Load procedures into the vector store.
        """
        try:
            procedures_path = os.path.join(self.knowledge_base_path, 'procedures')
            if not os.path.exists(procedures_path):
                self.logger.warning(f"Procedures directory not found: {procedures_path}")
                return
            
            # Find all procedure files
            procedure_files = glob.glob(os.path.join(procedures_path, '*.md'))
            
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for procedure_file in procedure_files:
                with open(procedure_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract procedure information
                procedure_id = os.path.splitext(os.path.basename(procedure_file))[0]
                
                # Split content into chunks if too long
                chunks = self._split_text_into_chunks(content)
                
                for i, chunk in enumerate(chunks):
                    # Generate embedding
                    embedding = self.embedding_generator.generate_single_embedding(chunk)
                    
                    # Create metadata
                    metadata = {
                        'type': 'procedure',
                        'procedure_id': procedure_id,
                        'chunk_index': i,
                        'source': 'procedures',
                        'file_path': procedure_file
                    }
                    
                    documents.append(chunk)
                    embeddings.append(embedding)
                    metadatas.append(metadata)
                    ids.append(f"procedure_{procedure_id}_{i}")
            
            if documents:
                self.vector_store.add_documents(documents, np.array(embeddings), metadatas, ids)
                self.logger.info(f"Loaded {len(documents)} procedure chunks")
            
        except Exception as e:
            self.logger.error(f"Error loading procedures: {str(e)}")
    
    async def _load_faq(self) -> None:
        """
        Load FAQ entries into the vector store.
        """
        try:
            faq_path = os.path.join(self.knowledge_base_path, 'faq')
            if not os.path.exists(faq_path):
                self.logger.warning(f"FAQ directory not found: {faq_path}")
                return
            
            # Find all FAQ files
            faq_files = glob.glob(os.path.join(faq_path, '*.json'))
            
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for faq_file in faq_files:
                with open(faq_file, 'r', encoding='utf-8') as f:
                    faq_data = json.load(f)
                
                # Process FAQ entries
                for entry in faq_data.get('entries', []):
                    question = entry.get('question', '')
                    answer = entry.get('answer', '')
                    category = entry.get('category', 'general')
                    tags = entry.get('tags', [])
                    
                    # Create document content
                    document = f"Question: {question}\n\nAnswer: {answer}"
                    
                    # Generate embedding
                    embedding = self.embedding_generator.generate_single_embedding(document)
                    
                    # Create metadata
                    metadata = {
                        'type': 'faq',
                        'faq_id': entry.get('id', 'unknown'),
                        'question': question,
                        'category': category,
                        'tags': tags,
                        'source': 'faq'
                    }
                    
                    documents.append(document)
                    embeddings.append(embedding)
                    metadatas.append(metadata)
                    ids.append(f"faq_{entry.get('id', 'unknown')}")
            
            if documents:
                self.vector_store.add_documents(documents, np.array(embeddings), metadatas, ids)
                self.logger.info(f"Loaded {len(documents)} FAQ entries")
            
        except Exception as e:
            self.logger.error(f"Error loading FAQ: {str(e)}")
    
    async def _load_knowledge_articles(self) -> None:
        """
        Load knowledge articles into the vector store.
        """
        try:
            articles_path = os.path.join(self.knowledge_base_path, 'articles')
            if not os.path.exists(articles_path):
                self.logger.warning(f"Articles directory not found: {articles_path}")
                return
            
            # Find all article files
            article_files = glob.glob(os.path.join(articles_path, '*.md'))
            
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for article_file in article_files:
                with open(article_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract article information
                article_id = os.path.splitext(os.path.basename(article_file))[0]
                
                # Split content into chunks if too long
                chunks = self._split_text_into_chunks(content)
                
                for i, chunk in enumerate(chunks):
                    # Generate embedding
                    embedding = self.embedding_generator.generate_single_embedding(chunk)
                    
                    # Create metadata
                    metadata = {
                        'type': 'knowledge_article',
                        'article_id': article_id,
                        'chunk_index': i,
                        'source': 'articles',
                        'file_path': article_file
                    }
                    
                    documents.append(chunk)
                    embeddings.append(embedding)
                    metadatas.append(metadata)
                    ids.append(f"article_{article_id}_{i}")
            
            if documents:
                self.vector_store.add_documents(documents, np.array(embeddings), metadatas, ids)
                self.logger.info(f"Loaded {len(documents)} article chunks")
            
        except Exception as e:
            self.logger.error(f"Error loading knowledge articles: {str(e)}")
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to break at sentence boundary
            last_period = text.rfind('.', start, end)
            last_newline = text.rfind('\n', start, end)
            
            if last_period > start:
                end = last_period + 1
            elif last_newline > start:
                end = last_newline + 1
            
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        
        return chunks
    
    async def add_resolved_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Add a resolved ticket to the knowledge base.
        
        Args:
            ticket_data: Ticket data
            
        Returns:
            True if successful
        """
        try:
            # Create document content
            subject = ticket_data.get('subject', '')
            solution = ticket_data.get('solution', '')
            document = f"Subject: {subject}\n\nSolution: {solution}"
            
            # Generate embedding
            embedding = self.embedding_generator.generate_single_embedding(document)
            
            # Create metadata
            metadata = {
                'type': 'resolved_ticket',
                'ticket_id': ticket_data.get('id'),
                'subject': subject,
                'category': ticket_data.get('category', 'unknown'),
                'resolved_at': ticket_data.get('resolved_at', ''),
                'source': 'resolved_tickets'
            }
            
            # Add to vector store
            doc_id = f"ticket_{ticket_data.get('id')}"
            success = self.vector_store.add_single_document(
                document=document,
                embedding=embedding,
                metadata=metadata,
                doc_id=doc_id
            )
            
            if success:
                self.logger.info(f"Added resolved ticket {ticket_data.get('id')} to knowledge base")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding resolved ticket: {str(e)}")
            return False
    
    async def add_faq_entry(self, faq_data: Dict[str, Any]) -> bool:
        """
        Add a FAQ entry to the knowledge base.
        
        Args:
            faq_data: FAQ data
            
        Returns:
            True if successful
        """
        try:
            # Create document content
            question = faq_data.get('question', '')
            answer = faq_data.get('answer', '')
            document = f"Question: {question}\n\nAnswer: {answer}"
            
            # Generate embedding
            embedding = self.embedding_generator.generate_single_embedding(document)
            
            # Create metadata
            metadata = {
                'type': 'faq',
                'faq_id': faq_data.get('id'),
                'question': question,
                'category': faq_data.get('category', 'general'),
                'tags': faq_data.get('tags', []),
                'source': 'faq'
            }
            
            # Add to vector store
            doc_id = f"faq_{faq_data.get('id')}"
            success = self.vector_store.add_single_document(
                document=document,
                embedding=embedding,
                metadata=metadata,
                doc_id=doc_id
            )
            
            if success:
                self.logger.info(f"Added FAQ entry {faq_data.get('id')} to knowledge base")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding FAQ entry: {str(e)}")
            return False
    
    async def update_knowledge_base(self) -> bool:
        """
        Update the knowledge base with new content.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info("Updating knowledge base...")
            
            # Clear existing content
            self.vector_store.clear_collection()
            
            # Reload all content
            success = await self.load_knowledge_base()
            
            if success:
                self.logger.info("Knowledge base updated successfully")
            else:
                self.logger.error("Failed to update knowledge base")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating knowledge base: {str(e)}")
            return False
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics.
        
        Returns:
            Knowledge base statistics
        """
        try:
            collection_info = self.vector_store.get_collection_info()
            
            # Get counts by type
            all_docs = self.vector_store.get_all_documents()
            
            type_counts = {}
            for doc in all_docs:
                doc_type = doc['metadata'].get('type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            return {
                'total_documents': collection_info.get('document_count', 0),
                'type_counts': type_counts,
                'collection_name': collection_info.get('name'),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting knowledge base stats: {str(e)}")
            return {}
    
    def backup_knowledge_base(self, backup_path: str) -> bool:
        """
        Backup the knowledge base.
        
        Args:
            backup_path: Path to save backup
            
        Returns:
            True if successful
        """
        try:
            return self.vector_store.backup_collection(backup_path)
        except Exception as e:
            self.logger.error(f"Error backing up knowledge base: {str(e)}")
            return False
    
    def restore_knowledge_base(self, backup_path: str) -> bool:
        """
        Restore the knowledge base from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful
        """
        try:
            return self.vector_store.restore_collection(backup_path)
        except Exception as e:
            self.logger.error(f"Error restoring knowledge base: {str(e)}")
            return False
    
    def __str__(self) -> str:
        """
        String representation of KnowledgeBase.
        
        Returns:
            String representation
        """
        stats = self.get_knowledge_base_stats()
        return f"KnowledgeBase(documents={stats.get('total_documents', 0)})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation of KnowledgeBase.
        
        Returns:
            Detailed string representation
        """
        stats = self.get_knowledge_base_stats()
        return f"KnowledgeBase(total_documents={stats.get('total_documents', 0)}, type_counts={stats.get('type_counts', {})})"
