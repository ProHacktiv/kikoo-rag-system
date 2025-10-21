"""
Embeddings generation for the flowup-support-bot.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Union
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import pickle
import os
from datetime import datetime

from ..utils.logger import get_logger


class EmbeddingGenerator:
    """
    Generate embeddings for text using various models.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the embedding generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Load model configuration
        self.model_name = config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Initialize model
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self) -> None:
        """
        Load the embedding model.
        """
        try:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            
            if 'sentence-transformers' in self.model_name:
                self.model = SentenceTransformer(self.model_name, device=self.device)
            else:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name)
                self.model.to(self.device)
            
            self.logger.info(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            self.logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def generate_embeddings(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        Args:
            texts: Text or list of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Embeddings array
        """
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            if 'sentence-transformers' in self.model_name:
                embeddings = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=len(texts) > 100,
                    convert_to_numpy=True
                )
            else:
                embeddings = self._generate_embeddings_with_transformers(texts, batch_size)
            
            self.logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def _generate_embeddings_with_transformers(self, texts: List[str], batch_size: int) -> np.ndarray:
        """
        Generate embeddings using transformers model.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Embeddings array
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden states
                batch_embeddings = outputs.last_hidden_state.mean(dim=1)
                embeddings.append(batch_embeddings.cpu().numpy())
        
        return np.vstack(embeddings)
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0]
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.generate_embeddings(texts, batch_size)
        return [embeddings[i] for i in range(len(embeddings))]
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score
        """
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error computing similarity: {str(e)}")
            return 0.0
    
    def compute_similarities(self, query_embedding: np.ndarray, candidate_embeddings: np.ndarray) -> np.ndarray:
        """
        Compute similarities between query and candidate embeddings.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: Candidate embeddings array
            
        Returns:
            Array of similarity scores
        """
        try:
            # Normalize query embedding
            query_norm = np.linalg.norm(query_embedding)
            if query_norm == 0:
                return np.zeros(len(candidate_embeddings))
            
            # Normalize candidate embeddings
            candidate_norms = np.linalg.norm(candidate_embeddings, axis=1)
            candidate_norms[candidate_norms == 0] = 1  # Avoid division by zero
            
            # Compute cosine similarities
            similarities = np.dot(candidate_embeddings, query_embedding) / (candidate_norms * query_norm)
            return similarities
            
        except Exception as e:
            self.logger.error(f"Error computing similarities: {str(e)}")
            return np.zeros(len(candidate_embeddings))
    
    def find_most_similar(self, query_embedding: np.ndarray, candidate_embeddings: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: Candidate embeddings array
            top_k: Number of top results to return
            
        Returns:
            List of similarity results
        """
        try:
            similarities = self.compute_similarities(query_embedding, candidate_embeddings)
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                results.append({
                    'index': int(idx),
                    'similarity': float(similarities[idx]),
                    'embedding': candidate_embeddings[idx]
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error finding most similar: {str(e)}")
            return []
    
    def save_embeddings(self, embeddings: np.ndarray, filepath: str) -> None:
        """
        Save embeddings to file.
        
        Args:
            embeddings: Embeddings to save
            filepath: File path to save to
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                pickle.dump(embeddings, f)
            
            self.logger.info(f"Saved embeddings to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving embeddings: {str(e)}")
            raise
    
    def load_embeddings(self, filepath: str) -> np.ndarray:
        """
        Load embeddings from file.
        
        Args:
            filepath: File path to load from
            
        Returns:
            Loaded embeddings
        """
        try:
            with open(filepath, 'rb') as f:
                embeddings = pickle.load(f)
            
            self.logger.info(f"Loaded embeddings from {filepath}")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Error loading embeddings: {str(e)}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings.
        
        Returns:
            Embedding dimension
        """
        try:
            if 'sentence-transformers' in self.model_name:
                return self.model.get_sentence_embedding_dimension()
            else:
                return self.model.config.hidden_size
        except Exception as e:
            self.logger.error(f"Error getting embedding dimension: {str(e)}")
            return 384  # Default for all-MiniLM-L6-v2
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Model information
        """
        return {
            'model_name': self.model_name,
            'device': self.device,
            'embedding_dimension': self.get_embedding_dimension(),
            'model_type': 'sentence-transformers' if 'sentence-transformers' in self.model_name else 'transformers'
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text before embedding.
        
        Args:
            text: Text to preprocess
            
        Returns:
            Preprocessed text
        """
        # Basic text preprocessing
        text = text.strip()
        text = ' '.join(text.split())  # Remove extra whitespace
        
        # Add any custom preprocessing here
        return text
    
    def generate_embeddings_with_metadata(self, texts: List[str], metadata: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate embeddings with metadata.
        
        Args:
            texts: List of texts to embed
            metadata: List of metadata for each text
            
        Returns:
            List of embedding results with metadata
        """
        try:
            if metadata is None:
                metadata = [{} for _ in texts]
            
            embeddings = self.generate_embeddings(texts)
            
            results = []
            for i, (text, embedding, meta) in enumerate(zip(texts, embeddings, metadata)):
                results.append({
                    'index': i,
                    'text': text,
                    'embedding': embedding,
                    'metadata': meta,
                    'generated_at': datetime.utcnow().isoformat()
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings with metadata: {str(e)}")
            return []
    
    def __str__(self) -> str:
        """
        String representation of EmbeddingGenerator.
        
        Returns:
            String representation
        """
        return f"EmbeddingGenerator(model={self.model_name}, device={self.device})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation of EmbeddingGenerator.
        
        Returns:
            Detailed string representation
        """
        return f"EmbeddingGenerator(model_name='{self.model_name}', device='{self.device}', embedding_dimension={self.get_embedding_dimension()})"
