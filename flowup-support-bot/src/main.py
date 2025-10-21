"""
Point d'entrée principal de l'application FlowUp Support Bot.
API FastAPI avec endpoints pour le traitement des tickets.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import yaml
import os
from datetime import datetime

from .core.universal_ticket_processor import UniversalTicketProcessor
from .core.universal_intent_analyzer import UniversalIntentAnalyzer
from .integrations.odoo_client import OdooClient
from .integrations.ups_tracker import UPSTracker
from .utils.logger import setup_logging

# Configuration du logging
setup_logging("INFO")
logger = logging.getLogger(__name__)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="FlowUp Support Bot API",
    description="API pour le système de support client automatisé FlowUp",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic
class TicketRequest(BaseModel):
    id: str
    message: str
    user_id: str
    category_expected: Optional[str] = None
    uc_expected: Optional[int] = None
    context: Optional[Dict] = None
    date: Optional[str] = None

class TicketResponse(BaseModel):
    ticket_id: str
    detected_category: str
    detected_uc: int
    confidence: float
    response: str
    escalate: bool
    escalation_reason: Optional[str] = None
    priority: str
    actions_taken: List[str]
    performance: Dict
    processing_time: float

class BatchRequest(BaseModel):
    tickets: List[TicketRequest]

class StatsResponse(BaseModel):
    total_processed: int
    category_accuracy: float
    uc_accuracy: float
    escalation_rate: float
    by_category: Dict[str, int]
    by_priority: Dict[str, int]

# Variables globales
processor: Optional[UniversalTicketProcessor] = None
odoo_client: Optional[OdooClient] = None
ups_tracker: Optional[UPSTracker] = None

@app.on_event("startup")
async def startup_event():
    """Initialisation de l'application au démarrage"""
    global processor, odoo_client, ups_tracker
    
    logger.info("🚀 Démarrage de FlowUp Support Bot...")
    
    try:
        # Charger la configuration
        config_path = "config/chatbot_config.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            config = {}
        
        # Initialiser les clients d'intégration
        odoo_client = OdooClient(
            api_url=os.getenv("ODOO_URL", "http://localhost:8069/api"),
            api_key=os.getenv("ODOO_API_KEY", "mock_key")
        )
        
        ups_tracker = UPSTracker(
            api_key=os.getenv("UPS_API_KEY", "mock_key")
        )
        
        # Initialiser le processeur principal
        processor = UniversalTicketProcessor(config, odoo_client)
        
        logger.info("✅ Initialisation terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        raise

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "FlowUp Support Bot API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de santé de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "processor": processor is not None,
            "odoo": odoo_client is not None,
            "ups": ups_tracker is not None
        }
    }

@app.post("/process", response_model=TicketResponse)
async def process_ticket(ticket: TicketRequest):
    """
    Traite un ticket unique
    
    Args:
        ticket: Données du ticket à traiter
        
    Returns:
        Réponse générée par le bot
    """
    if not processor:
        raise HTTPException(status_code=500, detail="Processeur non initialisé")
    
    try:
        # Convertir le ticket en dictionnaire
        ticket_dict = ticket.dict()
        
        # Traiter le ticket
        result = processor.process(ticket_dict)
        
        # Convertir en réponse
        response = TicketResponse(**result)
        
        logger.info(f"Ticket {ticket.id} traité avec succès")
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du ticket {ticket.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/batch")
async def process_batch(request: BatchRequest):
    """
    Traite un batch de tickets
    
    Args:
        request: Liste des tickets à traiter
        
    Returns:
        Liste des réponses générées
    """
    if not processor:
        raise HTTPException(status_code=500, detail="Processeur non initialisé")
    
    try:
        # Convertir les tickets en dictionnaires
        tickets = [ticket.dict() for ticket in request.tickets]
        
        # Traiter le batch
        results = processor.process_batch(tickets)
        
        logger.info(f"Batch de {len(tickets)} tickets traité avec succès")
        return {
            "results": results,
            "total_processed": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """
    Récupère les statistiques de performance du bot
    
    Returns:
        Statistiques détaillées
    """
    if not processor:
        raise HTTPException(status_code=500, detail="Processeur non initialisé")
    
    try:
        stats = processor.get_stats()
        return StatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/detailed")
async def get_detailed_stats():
    """
    Récupère un rapport de performance détaillé
    
    Returns:
        Rapport complet avec recommandations
    """
    if not processor:
        raise HTTPException(status_code=500, detail="Processeur non initialisé")
    
    try:
        report = processor.get_performance_report()
        return report
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_message(message: str):
    """
    Analyse un message sans générer de réponse complète
    
    Args:
        message: Message à analyser
        
    Returns:
        Résultat de l'analyse d'intent
    """
    if not processor:
        raise HTTPException(status_code=500, detail="Processeur non initialisé")
    
    try:
        # Utiliser l'analyseur d'intent directement
        intent_result = processor.intent_analyzer.analyze(message)
        
        return {
            "category": intent_result.category.value,
            "uc_id": intent_result.uc_id,
            "confidence": intent_result.confidence,
            "priority": intent_result.priority.value,
            "keywords_matched": intent_result.keywords_matched,
            "requires_escalation": intent_result.requires_escalation,
            "escalation_reason": intent_result.escalation_reason
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset_statistics():
    """
    Remet à zéro les statistiques du bot
    
    Returns:
        Confirmation de la réinitialisation
    """
    if not processor:
        raise HTTPException(status_code=500, detail="Processeur non initialisé")
    
    try:
        processor.reset_stats()
        return {
            "message": "Statistiques réinitialisées avec succès",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_configuration():
    """
    Récupère la configuration actuelle du bot
    
    Returns:
        Configuration complète
    """
    try:
        config_path = "config/chatbot_config.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        else:
            return {"error": "Fichier de configuration non trouvé"}
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de test
@app.get("/test/50-tickets")
async def test_50_tickets():
    """
    Lance le test des 50 tickets (endpoint de test)
    
    Returns:
        Résultats du test
    """
    try:
        # Importer et exécuter le script de test
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        
        from test_50_tickets import test_all_tickets
        
        results, stats = test_all_tickets()
        
        return {
            "message": "Test des 50 tickets terminé",
            "results": results,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
