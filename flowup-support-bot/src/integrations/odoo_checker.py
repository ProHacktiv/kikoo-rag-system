"""
Check Odoo automatique avant génération de réponse
Implémentation du check Odoo obligatoire selon les nouvelles instructions
"""

import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging

class OdooChecker:
    """
    Vérificateur Odoo automatique pour enrichir le contexte
    
    FONCTIONNALITÉS:
    - Check automatique avant chaque réponse
    - Enrichissement du contexte client
    - Détection des statuts critiques
    - Calcul des délais et retards
    """
    
    def __init__(self, odoo_client=None):
        self.odoo = odoo_client
        self.logger = logging.getLogger(__name__)
        
        # Configuration des checks
        self.check_config = {
            "always_check": True,  # Toujours checker Odoo
            "timeout": 5,         # Timeout en secondes
            "retry_attempts": 2,  # Tentatives en cas d'échec
            "cache_duration": 300  # Cache 5 minutes
        }
        
        # Cache pour éviter les appels répétés
        self.cache = {}
    
    def check_order_context(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Check Odoo complet pour enrichir le contexte
        
        Args:
            user_id: ID du client
            message: Message du client
            
        Returns:
            Dict avec toutes les informations Odoo
        """
        try:
            # Vérifier le cache d'abord
            cache_key = f"odoo_check_{user_id}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if self._is_cache_valid(cached_data):
                    self.logger.info(f"Utilisation cache Odoo pour {user_id}")
                    return cached_data['data']
            
            # Check Odoo si pas de client Odoo disponible
            if not self.odoo:
                return self._get_fallback_context(user_id, message)
            
            # 1. Récupérer les commandes du client
            orders = self._get_customer_orders(user_id)
            
            # 2. Analyser la commande la plus récente
            latest_order = self._get_latest_order(orders)
            
            # 3. Calculer les métriques importantes
            context = self._build_context(latest_order, orders, message)
            
            # 4. Mettre en cache
            self.cache[cache_key] = {
                'data': context,
                'timestamp': datetime.now()
            }
            
            self.logger.info(f"Check Odoo réussi pour {user_id}: {context.get('order_status', 'UNKNOWN')}")
            return context
            
        except Exception as e:
            self.logger.error(f"Erreur check Odoo pour {user_id}: {str(e)}")
            return self._get_fallback_context(user_id, message)
    
    def _get_customer_orders(self, user_id: str) -> List[Dict]:
        """Récupère les commandes du client"""
        try:
            if not self.odoo:
                return []
            
            # Recherche par email ou ID client
            orders = self.odoo.search_orders_by_customer(user_id)
            return orders or []
            
        except Exception as e:
            self.logger.error(f"Erreur récupération commandes {user_id}: {str(e)}")
            return []
    
    def _get_latest_order(self, orders: List[Dict]) -> Optional[Dict]:
        """Récupère la commande la plus récente"""
        if not orders:
            return None
        
        # Trier par date de commande
        sorted_orders = sorted(
            orders, 
            key=lambda x: x.get('date_order', '1900-01-01'),
            reverse=True
        )
        
        return sorted_orders[0]
    
    def _build_context(self, order: Optional[Dict], all_orders: List[Dict], message: str) -> Dict[str, Any]:
        """Construit le contexte enrichi"""
        if not order:
            return {
                "has_order": False,
                "order_status": "NO_ORDER",
                "needs_escalation": True,
                "escalation_reason": "Aucune commande trouvée",
                "priority": "HIGH"
            }
        
        # Informations de base
        order_date = order.get('date_order', '')
        status = order.get('state', 'UNKNOWN')
        products = order.get('product_lines', [])
        
        # Calcul des délais
        days_since_order = self._calculate_days_since_order(order_date)
        is_delayed = days_since_order > 12
        
        # Analyse des produits
        gpu_products = self._extract_gpu_products(products)
        has_gpu = len(gpu_products) > 0
        
        # Détection de problèmes critiques
        critical_issues = self._detect_critical_issues(order, days_since_order, status)
        
        # Priorité et escalade
        priority = self._calculate_priority(order, days_since_order, critical_issues)
        needs_escalation = self._needs_escalation(order, days_since_order, critical_issues)
        
        return {
            # Informations commande
            "has_order": True,
            "order_id": order.get('id'),
            "order_reference": order.get('name'),
            "order_date": order_date,
            "order_status": status,
            "days_since_order": days_since_order,
            "is_delayed": is_delayed,
            
            # Produits
            "products": products,
            "gpu_products": gpu_products,
            "has_gpu": has_gpu,
            
            # Contexte client
            "customer_name": order.get('partner_id', [{}])[0].get('name', 'Client'),
            "customer_email": order.get('partner_id', [{}])[0].get('email', ''),
            
            # Statut livraison
            "delivery_status": order.get('delivery_status', 'UNKNOWN'),
            "tracking_number": order.get('tracking_number', ''),
            "delivery_date": order.get('delivery_date', ''),
            
            # Problèmes détectés
            "critical_issues": critical_issues,
            "needs_escalation": needs_escalation,
            "escalation_reason": self._get_escalation_reason(critical_issues, days_since_order),
            "priority": priority,
            
            # Historique
            "total_orders": len(all_orders),
            "previous_issues": self._analyze_previous_issues(all_orders),
            
            # Métriques
            "satisfaction_risk": self._calculate_satisfaction_risk(order, days_since_order),
            "urgency_level": self._calculate_urgency_level(critical_issues, days_since_order)
        }
    
    def _calculate_days_since_order(self, order_date: str) -> int:
        """Calcule le nombre de jours depuis la commande"""
        try:
            if not order_date:
                return 0
            
            order_dt = datetime.strptime(order_date.split(' ')[0], '%Y-%m-%d')
            today = datetime.now()
            delta = today - order_dt
            return delta.days
            
        except Exception:
            return 0
    
    def _extract_gpu_products(self, products: List[Dict]) -> List[Dict]:
        """Extrait les produits GPU de la commande"""
        gpu_keywords = ['rtx', 'gtx', 'gpu', 'carte graphique', 'graphics']
        gpu_products = []
        
        for product in products:
            product_name = product.get('product_name', '').lower()
            if any(keyword in product_name for keyword in gpu_keywords):
                gpu_products.append(product)
        
        return gpu_products
    
    def _detect_critical_issues(self, order: Dict, days_since_order: int, status: str) -> List[str]:
        """Détecte les problèmes critiques"""
        issues = []
        
        # Délai dépassé
        if days_since_order > 12:
            issues.append("DELAY_EXCEEDED")
        
        # Statut problématique
        if status in ['cancelled', 'refunded']:
            issues.append("ORDER_CANCELLED")
        
        # Problèmes de livraison
        delivery_status = order.get('delivery_status', '')
        if delivery_status in ['lost', 'damaged', 'returned']:
            issues.append("DELIVERY_PROBLEM")
        
        # Produits critiques
        if self._extract_gpu_products(order.get('product_lines', [])):
            issues.append("HAS_GPU_PRODUCTS")
        
        return issues
    
    def _calculate_priority(self, order: Dict, days_since_order: int, critical_issues: List[str]) -> str:
        """Calcule la priorité basée sur le contexte"""
        if "DELAY_EXCEEDED" in critical_issues:
            return "IMMEDIATE"
        elif "ORDER_CANCELLED" in critical_issues:
            return "HIGH"
        elif "DELIVERY_PROBLEM" in critical_issues:
            return "HIGH"
        elif days_since_order > 7:
            return "MEDIUM"
        else:
            return "NORMAL"
    
    def _needs_escalation(self, order: Dict, days_since_order: int, critical_issues: List[str]) -> bool:
        """Détermine si escalade nécessaire"""
        return (
            len(critical_issues) > 0 or
            days_since_order > 10 or
            order.get('state') in ['cancelled', 'refunded']
        )
    
    def _get_escalation_reason(self, critical_issues: List[str], days_since_order: int) -> str:
        """Génère la raison d'escalade"""
        if "DELAY_EXCEEDED" in critical_issues:
            return f"Délai légal dépassé ({days_since_order} jours)"
        elif "ORDER_CANCELLED" in critical_issues:
            return "Commande annulée"
        elif "DELIVERY_PROBLEM" in critical_issues:
            return "Problème de livraison"
        elif days_since_order > 10:
            return f"Retard important ({days_since_order} jours)"
        else:
            return "Problème détecté"
    
    def _analyze_previous_issues(self, all_orders: List[Dict]) -> Dict[str, Any]:
        """Analyse les problèmes précédents"""
        return {
            "total_orders": len(all_orders),
            "cancelled_orders": len([o for o in all_orders if o.get('state') == 'cancelled']),
            "refunded_orders": len([o for o in all_orders if o.get('state') == 'refunded']),
            "average_delay": self._calculate_average_delay(all_orders)
        }
    
    def _calculate_average_delay(self, orders: List[Dict]) -> float:
        """Calcule le délai moyen des commandes"""
        if not orders:
            return 0.0
        
        delays = []
        for order in orders:
            days = self._calculate_days_since_order(order.get('date_order', ''))
            if days > 0:
                delays.append(days)
        
        return sum(delays) / len(delays) if delays else 0.0
    
    def _calculate_satisfaction_risk(self, order: Dict, days_since_order: int) -> str:
        """Calcule le risque de satisfaction"""
        if days_since_order > 15:
            return "HIGH"
        elif days_since_order > 10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_urgency_level(self, critical_issues: List[str], days_since_order: int) -> str:
        """Calcule le niveau d'urgence"""
        if len(critical_issues) > 2 or days_since_order > 15:
            return "CRITICAL"
        elif len(critical_issues) > 0 or days_since_order > 10:
            return "HIGH"
        else:
            return "NORMAL"
    
    def _get_fallback_context(self, user_id: str, message: str) -> Dict[str, Any]:
        """Contexte de fallback si Odoo indisponible"""
        return {
            "has_order": False,
            "order_status": "UNKNOWN",
            "needs_escalation": True,
            "escalation_reason": "Impossible de vérifier la commande",
            "priority": "MEDIUM",
            "odoo_available": False
        }
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Vérifie si le cache est encore valide"""
        if 'timestamp' not in cached_data:
            return False
        
        cache_age = datetime.now() - cached_data['timestamp']
        return cache_age.total_seconds() < self.check_config['cache_duration']
    
    def get_check_summary(self, user_id: str, message: str) -> str:
        """Retourne un résumé du check Odoo pour debug"""
        context = self.check_order_context(user_id, message)
        
        summary = f"""
🔍 CHECK ODOO AUTOMATIQUE
=========================

Client: {user_id}
Message: "{message[:50]}..."

RÉSULTAT:
- Commande trouvée: {'✅ OUI' if context.get('has_order') else '❌ NON'}
- Statut: {context.get('order_status', 'UNKNOWN')}
- Jours écoulés: {context.get('days_since_order', 0)}
- Retard: {'⚠️ OUI' if context.get('is_delayed') else '✅ NON'}
- Escalade: {'🚨 OUI' if context.get('needs_escalation') else '❌ NON'}

CONTEXTE:
- Produits GPU: {len(context.get('gpu_products', []))}
- Problèmes critiques: {len(context.get('critical_issues', []))}
- Priorité: {context.get('priority', 'NORMAL')}
- Urgence: {context.get('urgency_level', 'NORMAL')}

RAISON ESCALADE: {context.get('escalation_reason', 'Aucune')}
        """
        
        return summary.strip()

# Test du checker Odoo
def test_odoo_checker():
    """Test du vérificateur Odoo"""
    checker = OdooChecker()
    
    # Test avec différents contextes
    test_cases = [
        {
            "user_id": "client_test_1",
            "message": "Ma carte graphique ne fonctionne plus",
            "expected": "Check Odoo effectué"
        },
        {
            "user_id": "client_test_2", 
            "message": "Où en est ma commande ?",
            "expected": "Check Odoo effectué"
        }
    ]
    
    print("🧪 TEST CHECKER ODOO")
    print("=" * 30)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Test: {case['user_id']}")
        print(f"   Message: {case['message']}")
        
        try:
            context = checker.check_order_context(case['user_id'], case['message'])
            print(f"   Résultat: ✅ {case['expected']}")
            print(f"   Commande: {'✅ Trouvée' if context.get('has_order') else '❌ Non trouvée'}")
            print(f"   Escalade: {'🚨 OUI' if context.get('needs_escalation') else '❌ NON'}")
            
        except Exception as e:
            print(f"   Erreur: ❌ {str(e)}")

if __name__ == "__main__":
    test_odoo_checker()
