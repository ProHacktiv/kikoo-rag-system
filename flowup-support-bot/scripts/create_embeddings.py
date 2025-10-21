#!/usr/bin/env python3
"""
Script to create embeddings for the knowledge base.
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.rag.knowledge_base import KnowledgeBase
from src.utils.logger import get_logger


async def main():
    """Main function to create embeddings."""
    parser = argparse.ArgumentParser(description='Create embeddings for the knowledge base')
    parser.add_argument('--config', default='config/settings.yaml', help='Configuration file path')
    parser.add_argument('--force', action='store_true', help='Force recreation of embeddings')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger(__name__)
    if args.verbose:
        logger.info("Starting embedding creation process")
    
    try:
        # Load configuration
        import yaml
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Initialize knowledge base
        kb = KnowledgeBase(config)
        
        if args.force:
            logger.info("Force mode enabled - clearing existing embeddings")
            kb.vector_store.clear_collection()
        
        # Load knowledge base
        logger.info("Loading knowledge base...")
        success = await kb.load_knowledge_base()
        
        if success:
            logger.info("Knowledge base loaded successfully")
            
            # Get statistics
            stats = kb.get_knowledge_base_stats()
            logger.info(f"Knowledge base statistics: {stats}")
            
            # Backup if requested
            if args.force:
                backup_path = 'data/vectors/backup.json'
                logger.info(f"Creating backup at {backup_path}")
                kb.backup_knowledge_base(backup_path)
        else:
            logger.error("Failed to load knowledge base")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
