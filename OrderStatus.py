import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class OrderStatus(Enum):
    """Statuts possibles d'une commande"""
    PENDING = "en attente"
    PRODUCTION = "en production"
    TESTING = "en test qualité"
    PICKING = "prêt pour expédition"
    SHIPPED = "expédié"
    DELIVERED = "livré"

@dataclass
class Order:
    """Structure d'une commande"""
    order_id: str
    user_id: str
    product: str
    order_date: datetime.datetime
    payment_date: datetime.datetime
    status: OrderStatus
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    
    @property
    def days_since_payment(self) -> int:
        """Calcule le nombre de jours depuis le paiement"""
        return (datetime.datetime.now() - self.payment_date).days
    
    @property
    def is_within_legal_delay(self) -> bool:
        """Vérifie si on est dans les 12 jours légaux"""
        return self.days_since_payment <= 12
    
    @property
    def remaining_days(self) -> int:
        """Jours restants avant dépassement du délai"""
        return max(0, 12 - self.days_since_payment)

class OdooIntegration:
    """Interface avec Odoo pour récupérer les commandes"""
    
    def __init__(self):
        # Simuler une base de données Odoo
        self.mock_orders = {
            "user_123": [
                Order(
                    order_id="S167549",
                    user_id="user_123",
                    product="PC Savannah RTX 4060",
                    order_date=datetime.datetime(2024, 9, 1),
                    payment_date=datetime.datetime(2024, 9, 1),
                    status=OrderStatus.PRODUCTION,
                    tracking_number=None,
                    tracking_url=None
                )
            ]
        }
    
    def get_user_orders(self, user_id: str) -> List[Order]:
        """Récupère toutes les commandes d'un utilisateur"""
        return self.mock_orders.get(user_id, [])
    
    def get_recent_orders(self, user_id: str, days: int = 30) -> List[Order]:
        """Récupère les commandes récentes"""
        orders = self.get_user_orders(user_id)
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        return [o for o in orders if o.order_date >= cutoff]