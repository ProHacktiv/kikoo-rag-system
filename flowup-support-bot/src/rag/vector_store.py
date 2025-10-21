"""
Vector store for the flowup-support-bot.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
import os
import json
from datetime import datetime

from ..utils.logger import get_logger


class VectorStore:
    """
    Vector store for storing and retrieving embeddings.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the vector store.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize ChromaDB
        self.persist_directory = config.get('persist_directory', 'data/vectors/chroma_db')
        self.collection_name = config.get('collection_name', 'flowup_knowledge')
        
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """
        Initialize ChromaDB client and collection.
        """
        try:
            # Create ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=None  # We'll handle embeddings externally
                )
                self.logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Flowup knowledge base embeddings"}
                )
                self.logger.info(f"Created new collection: {self.collection_name}")
            
        except Exception as e:
            self.logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def add_documents(self, documents: List[str], embeddings: np.ndarray, metadatas: List[Dict[str, Any]] = None, ids: List[str] = None) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            embeddings: Embeddings for the documents
            metadatas: List of metadata for each document
            ids: List of IDs for each document
            
        Returns:
            True if successful
        """
        try:
            if metadatas is None:
                metadatas = [{} for _ in documents]
            
            if ids is None:
                ids = [f"doc_{i}_{datetime.utcnow().timestamp()}" for i in range(len(documents))]
            
            # Add documents to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding documents: {str(e)}")
            return False
    
    def add_single_document(self, document: str, embedding: np.ndarray, metadata: Dict[str, Any] = None, doc_id: str = None) -> bool:
        """
        Add a single document to the vector store.
        
        Args:
            document: Document to add
            embedding: Embedding for the document
            metadata: Metadata for the document
            doc_id: ID for the document
            
        Returns:
            True if successful
        """
        try:
            if metadata is None:
                metadata = {}
            
            if doc_id is None:
                doc_id = f"doc_{datetime.utcnow().timestamp()}"
            
            self.collection.add(
                documents=[document],
                embeddings=[embedding.tolist()],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            self.logger.info(f"Added document {doc_id} to vector store")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding document: {str(e)}")
            return False
    
    def search(self, query_embedding: np.ndarray, n_results: int = 5, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding
            n_results: Number of results to return
            where: Filter conditions
            
        Returns:
            List of search results
        """
        try:
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            self.logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def search_by_text(self, query_text: str, query_embedding: np.ndarray, n_results: int = 5, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search by text query.
        
        Args:
            query_text: Text query
            query_embedding: Query embedding
            n_results: Number of results to return
            where: Filter conditions
            
        Returns:
            List of search results
        """
        try:
            # Perform search
            results = self.collection.query(
                query_texts=[query_text],
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching by text: {str(e)}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document information or None if not found
        """
        try:
            results = self.collection.get(
                ids=[doc_id]
            )
            
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'document': results['documents'][0],
                    'metadata': results['metadatas'][0],
                    'embedding': results['embeddings'][0] if results['embeddings'] else None
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting document {doc_id}: {str(e)}")
            return None
    
    def update_document(self, doc_id: str, document: str = None, embedding: np.ndarray = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Update a document.
        
        Args:
            doc_id: Document ID
            document: New document text
            embedding: New embedding
            metadata: New metadata
            
        Returns:
            True if successful
        """
        try:
            update_data = {}
            
            if document is not None:
                update_data['documents'] = [document]
            
            if embedding is not None:
                update_data['embeddings'] = [embedding.tolist()]
            
            if metadata is not None:
                update_data['metadatas'] = [metadata]
            
            if update_data:
                self.collection.update(
                    ids=[doc_id],
                    **update_data
                )
                
                self.logger.info(f"Updated document {doc_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating document {doc_id}: {str(e)}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[doc_id])
            self.logger.info(f"Deleted document {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {str(e)}")
            return False
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete multiple documents.
        
        Args:
            doc_ids: List of document IDs
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=doc_ids)
            self.logger.info(f"Deleted {len(doc_ids)} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection information.
        
        Returns:
            Collection information
        """
        try:
            count = self.collection.count()
            
            return {
                'name': self.collection_name,
                'document_count': count,
                'persist_directory': self.persist_directory,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection info: {str(e)}")
            return {}
    
    def get_all_documents(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all documents from the collection.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of all documents
        """
        try:
            results = self.collection.get(
                limit=limit
            )
            
            documents = []
            for i in range(len(results['ids'])):
                documents.append({
                    'id': results['ids'][i],
                    'document': results['documents'][i],
                    'metadata': results['metadatas'][i],
                    'embedding': results['embeddings'][i] if results['embeddings'] else None
                })
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting all documents: {str(e)}")
            return []
    
    def search_by_metadata(self, where: Dict[str, Any], n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents by metadata.
        
        Args:
            where: Metadata filter conditions
            n_results: Number of results to return
            
        Returns:
            List of matching documents
        """
        try:
            results = self.collection.get(
                where=where,
                limit=n_results
            )
            
            documents = []
            for i in range(len(results['ids'])):
                documents.append({
                    'id': results['ids'][i],
                    'document': results['documents'][i],
                    'metadata': results['metadatas'][i],
                    'embedding': results['embeddings'][i] if results['embeddings'] else None
                })
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error searching by metadata: {str(e)}")
            return []
    
    def get_document_count(self) -> int:
        """
        Get total number of documents in the collection.
        
        Returns:
            Number of documents
        """
        try:
            return self.collection.count()
        except Exception as e:
            self.logger.error(f"Error getting document count: {str(e)}")
            return 0
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        
        Returns:
            True if successful
        """
        try:
            # Get all document IDs
            all_docs = self.collection.get()
            if all_docs['ids']:
                self.collection.delete(ids=all_docs['ids'])
            
            self.logger.info("Cleared collection")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing collection: {str(e)}")
            return False
    
    def backup_collection(self, backup_path: str) -> bool:
        """
        Backup the collection to a file.
        
        Args:
            backup_path: Path to save backup
            
        Returns:
            True if successful
        """
        try:
            # Get all documents
            all_docs = self.get_all_documents()
            
            # Save to JSON file
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(all_docs, f, indent=2, default=str)
            
            self.logger.info(f"Backed up collection to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error backing up collection: {str(e)}")
            return False
    
    def restore_collection(self, backup_path: str) -> bool:
        """
        Restore the collection from a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful
        """
        try:
            # Load backup
            with open(backup_path, 'r', encoding='utf-8') as f:
                all_docs = json.load(f)
            
            # Clear existing collection
            self.clear_collection()
            
            # Restore documents
            documents = [doc['document'] for doc in all_docs]
            embeddings = [doc['embedding'] for doc in all_docs if doc['embedding']]
            metadatas = [doc['metadata'] for doc in all_docs]
            ids = [doc['id'] for doc in all_docs]
            
            if embeddings:
                self.add_documents(documents, np.array(embeddings), metadatas, ids)
            else:
                # If no embeddings, we need to regenerate them
                self.logger.warning("No embeddings in backup, documents added without embeddings")
            
            self.logger.info(f"Restored collection from {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring collection: {str(e)}")
            return False
    
    def __str__(self) -> str:
        """
        String representation of VectorStore.
        
        Returns:
            String representation
        """
        return f"VectorStore(collection={self.collection_name}, documents={self.get_document_count()})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation of VectorStore.
        
        Returns:
            Detailed string representation
        """
        return f"VectorStore(collection_name='{self.collection_name}', persist_directory='{self.persist_directory}', document_count={self.get_document_count()})"
