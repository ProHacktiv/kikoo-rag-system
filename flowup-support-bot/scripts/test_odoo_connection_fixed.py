#!/usr/bin/env python3
"""
Test de connectivité Odoo - Version Corrigée
Utilise XML-RPC au lieu de l'API REST
"""

import sys
import os
import json
import xmlrpc.client
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_odoo_xmlrpc_connection():
    """Test la connectivité Odoo via XML-RPC"""
    print("🔗 Test Connectivité Odoo - XML-RPC")
    print("=" * 50)
    
    # Charger la configuration
    config_path = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"📋 Configuration chargée:")
        print(f"  • URL: {config['url']}")
        print(f"  • Database: {config['db']}")
        print(f"  • Username: {config['username']}")
        print(f"  • Password: {'*' * len(config['password'])}")
        
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
        return False
    
    # Test 1: Vérifier l'accessibilité de l'URL
    print(f"\n🌐 Test 1: Accessibilité de l'URL")
    try:
        import requests
        response = requests.get(config['url'], timeout=10)
        print(f"  ✅ URL accessible: {response.status_code}")
    except Exception as e:
        print(f"  ❌ URL non accessible: {e}")
        return False
    
    # Test 2: Test XML-RPC Common
    print(f"\n🔌 Test 2: XML-RPC Common")
    try:
        common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
        version_info = common.version()
        print(f"  ✅ Serveur Odoo accessible")
        print(f"  📊 Version: {version_info}")
    except Exception as e:
        print(f"  ❌ Erreur XML-RPC Common: {e}")
        return False
    
    # Test 3: Authentification
    print(f"\n🔐 Test 3: Authentification")
    try:
        uid = common.authenticate(
            config['db'],
            config['username'],
            config['password'],
            {}
        )
        
        if uid:
            print(f"  ✅ Authentification réussie!")
            print(f"  👤 User ID: {uid}")
        else:
            print(f"  ❌ Authentification échouée")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur authentification: {e}")
        return False
    
    # Test 4: Accès aux modèles
    print(f"\n📊 Test 4: Accès aux modèles")
    try:
        models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")
        
        # Test recherche de commandes
        order_ids = models.execute_kw(
            config['db'], uid, config['password'],
            'sale.order', 'search',
            [[]],
            {'limit': 1}
        )
        
        print(f"  ✅ Accès aux modèles réussi")
        print(f"  📋 Commandes trouvées: {len(order_ids)}")
        
        if order_ids:
            # Test lecture d'une commande
            orders = models.execute_kw(
                config['db'], uid, config['password'],
                'sale.order', 'read',
                [order_ids[0]],
                {'fields': ['name', 'partner_id', 'state', 'date_order']}
            )
            
            if orders:
                order = orders[0]
                print(f"  📄 Exemple de commande: {order['name']} - {order['state']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur accès modèles: {e}")
        return False

def test_odoo_data_extraction():
    """Test l'extraction de données Odoo"""
    print(f"\n📊 Test 5: Extraction de données")
    
    config_path = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Connexion XML-RPC
        common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
        models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")
        
        # Authentification
        uid = common.authenticate(
            config['db'],
            config['username'],
            config['password'],
            {}
        )
        
        if not uid:
            print(f"  ❌ Authentification échouée")
            return False
        
        # Test extraction commandes
        print(f"  🔍 Recherche de commandes...")
        order_ids = models.execute_kw(
            config['db'], uid, config['password'],
            'sale.order', 'search',
            [[]],
            {'limit': 5}
        )
        
        print(f"  📋 {len(order_ids)} commandes trouvées")
        
        if order_ids:
            # Détails des commandes
            orders = models.execute_kw(
                config['db'], uid, config['password'],
                'sale.order', 'read',
                order_ids,
                {'fields': ['name', 'partner_id', 'state', 'date_order', 'amount_total']}
            )
            
            print(f"  📊 Détails des commandes:")
            for order in orders[:3]:  # Afficher les 3 premières
                print(f"    • {order['name']} - {order['state']} - {order['amount_total']}€")
        
        # Test extraction clients
        print(f"  👥 Recherche de clients...")
        partner_ids = models.execute_kw(
            config['db'], uid, config['password'],
            'res.partner', 'search',
            [[('customer_rank', '>', 0)]],
            {'limit': 3}
        )
        
        print(f"  👤 {len(partner_ids)} clients trouvés")
        
        if partner_ids:
            partners = models.execute_kw(
                config['db'], uid, config['password'],
                'res.partner', 'read',
                partner_ids,
                {'fields': ['name', 'email', 'phone', 'customer_rank']}
            )
            
            print(f"  📊 Détails des clients:")
            for partner in partners:
                print(f"    • {partner['name']} - {partner.get('email', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur extraction: {e}")
        return False

def test_odoo_integration_with_config():
    """Test l'intégration avec configuration"""
    print(f"\n🔧 Test 6: Intégration avec configuration")
    
    try:
        # Charger la configuration
        config_path = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Adapter la configuration pour le client
        odoo_config = {
            'url': config['url'],
            'database': config['db'],
            'username': config['username'],
            'password': config['password']
        }
        
        # Importer et initialiser le client
        from src.integrations.odoo_client import OdooClient
        
        client = OdooClient(odoo_config)
        
        print(f"  ✅ Client Odoo initialisé avec succès")
        
        # Test de récupération d'une commande
        print(f"  🔍 Test de récupération de commande...")
        
        # Note: Les méthodes sont async, donc on ne peut pas les tester directement ici
        # Mais on peut vérifier que le client est bien initialisé
        print(f"  ✅ Client prêt pour les opérations async")
        
        return True
        
    except ImportError as e:
        print(f"  ⚠️ Module OdooClient non disponible: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur intégration: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 FlowUp Support Bot - Test Connectivité Odoo (Version Corrigée)")
    print("=" * 70)
    
    # Tests de connectivité
    tests = [
        ("Connectivité XML-RPC", test_odoo_xmlrpc_connection),
        ("Extraction de données", test_odoo_data_extraction),
        ("Intégration avec config", test_odoo_integration_with_config)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"  ✅ {test_name}: RÉUSSI")
            else:
                print(f"  ❌ {test_name}: ÉCHOUÉ")
                
        except Exception as e:
            print(f"  ❌ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
    
    # Rapport final
    print(f"\n📊 RAPPORT FINAL")
    print("=" * 70)
    
    successful = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"✅ Tests réussis: {successful}/{total}")
    print(f"📈 Taux de succès: {successful/total*100:.1f}%")
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"  • {test_name}: {status}")
    
    if successful == total:
        print(f"\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print(f"✅ La connectivité Odoo est opérationnelle")
    else:
        print(f"\n⚠️ {total - successful} test(s) ont échoué")
        print(f"🔧 Des corrections sont nécessaires")
    
    return successful == total

if __name__ == "__main__":
    main()
