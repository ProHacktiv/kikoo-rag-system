"""
External integrations for the flowup-support-bot.
"""

from .odoo_client import OdooClient
from .ups_tracker import UPSTracker
from .database import DatabaseConnection

__all__ = [
    "OdooClient",
    "UPSTracker",
    "DatabaseConnection"
]
