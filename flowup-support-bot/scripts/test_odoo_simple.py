#!/usr/bin/env python3
"""
Test simple de connectivité Odoo
Version qui fonctionne avec les permissions actuelles
"""

import sys
import os
import json
import xmlrpc.client
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_odoo_simple():
    """Test simple de connectivité Odoo"""
    print("🔗 Test Simple Connectivité Odoo")
    print("=" * 50)
    
    # Charger la configuration
    config_path = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"📋 Configuration:")
        print(f"  • URL: {config['url']}")
        print(f"  • Database: {config['db']}")
        print(f"  • Username: {config['username']}")
        
    except Exception as e:
        print(f"❌ Erreur config: {e}")
        return False
    
    # Connexion XML-RPC
    print(f"\n🔌 Connexion XML-RPC")
    try:
        common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
        models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")
        
        # Version du serveur
        version = common.version()
        print(f"  ✅ Serveur Odoo {version['server_version']} accessible")
        
    except Exception as e:
        print(f"  ❌ Erreur connexion: {e}")
        return False
    
    # Authentification
    print(f"\n🔐 Authentification")
    try:
        uid = common.authenticate(
            config['db'],
            config['username'],
            config['password'],
            {}
        )
        
        if uid:
            print(f"  ✅ Authentification réussie (User ID: {uid})")
        else:
            print(f"  ❌ Authentification échouée")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur authentification: {e}")
        return False
    
    # Test simple - compter les enregistrements
    print(f"\n📊 Test de comptage")
    try:
        # Compter les commandes
        order_count = models.execute_kw(
            config['db'], uid, config['password'],
            'sale.order', 'search_count',
            [[]]
        )
        print(f"  📋 Commandes: {order_count}")
        
        # Compter les clients
        partner_count = models.execute_kw(
            config['db'], uid, config['password'],
            'res.partner', 'search_count',
            [[]]
        )
        print(f"  👥 Clients: {partner_count}")
        
        # Compter les produits
        product_count = models.execute_kw(
            config['db'], uid, config['password'],
            'product.product', 'search_count',
            [[]]
        )
        print(f"  📦 Produits: {product_count}")
        
    except Exception as e:
        print(f"  ❌ Erreur comptage: {e}")
        return False
    
    # Test de lecture simple
    print(f"\n📖 Test de lecture simple")
    try:
        # Lire les informations de l'utilisateur connecté
        user_info = models.execute_kw(
            config['db'], uid, config['password'],
            'res.users', 'read',
            [uid]
        )
        
        if user_info:
            user = user_info[0]
            print(f"  👤 Utilisateur: {user.get('name', 'N/A')}")
            print(f"  📧 Email: {user.get('email', 'N/A')}")
            print(f"  🏢 Société: {user.get('company_id', [None, 'N/A'])[1]}")
        
    except Exception as e:
        print(f"  ❌ Erreur lecture utilisateur: {e}")
        return False
    
    # Test de recherche simple
    print(f"\n🔍 Test de recherche simple")
    try:
        # Rechercher les 5 dernières commandes
        order_ids = models.execute_kw(
            config['db'], uid, config['password'],
            'sale.order', 'search',
            [[]],
            {'limit': 5, 'order': 'id desc'}
        )
        
        print(f"  📋 {len(order_ids)} commandes trouvées")
        
        if order_ids:
            # Lire seulement les champs de base
            orders = models.execute_kw(
                config['db'], uid, config['password'],
                'sale.order', 'read',
                order_ids,
                {'fields': ['name', 'state']}
            )
            
            print(f"  📊 Dernières commandes:")
            for order in orders:
                print(f"    • {order.get('name', 'N/A')} - {order.get('state', 'N/A')}")
        
    except Exception as e:
        print(f"  ❌ Erreur recherche commandes: {e}")
        return False
    
    return True

def test_odoo_client_simple():
    """Test simple du client Odoo"""
    print(f"\n🔧 Test client Odoo simple")
    
    try:
        # Charger la configuration
        config_path = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Adapter la configuration
        odoo_config = {
            'url': config['url'],
            'database': config['db'],
            'username': config['username'],
            'password': config['password']
        }
        
        # Importer le client
        from src.integrations.odoo_client import OdooClient
        
        # Initialiser le client
        client = OdooClient(odoo_config)
        
        print(f"  ✅ Client Odoo initialisé")
        print(f"  📊 Base: {client.database}")
        print(f"  👤 User: {client.username}")
        print(f"  🔑 UID: {client.uid}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur client: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 FlowUp Support Bot - Test Odoo Simple")
    print("=" * 60)
    
    # Tests de connectivité
    tests = [
        ("Connectivité et opérations de base", test_odoo_simple),
        ("Client Odoo", test_odoo_client_simple)
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
    print("=" * 60)
    
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
        print(f"🔗 URL: https://www.flowup.shop")
        print(f"📊 Base: production")
        print(f"👤 Utilisateur: dev@flowup.shop")
        print(f"🔑 User ID: 226409")
    else:
        print(f"\n⚠️ {total - successful} test(s) ont échoué")
        print(f"🔧 Des corrections sont nécessaires")
    
    return successful == total

if __name__ == "__main__":
    main()
