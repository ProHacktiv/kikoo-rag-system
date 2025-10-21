#!/usr/bin/env python3
"""
Test final de connectivité Odoo
Version corrigée avec extraction de données fonctionnelle
"""

import sys
import os
import json
import xmlrpc.client
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_odoo_complete():
    """Test complet de connectivité Odoo"""
    print("🔗 Test Connectivité Odoo - Version Finale")
    print("=" * 60)
    
    # Charger la configuration
    config_path = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"📋 Configuration chargée:")
        print(f"  • URL: {config['url']}")
        print(f"  • Database: {config['db']}")
        print(f"  • Username: {config['username']}")
        
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
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
    
    # Test extraction commandes
    print(f"\n📊 Test extraction commandes")
    try:
        # Recherche de commandes
        order_ids = models.execute_kw(
            config['db'], uid, config['password'],
            'sale.order', 'search',
            [[]],
            {'limit': 3}
        )
        
        print(f"  📋 {len(order_ids)} commandes trouvées")
        
        if order_ids:
            # Lecture des commandes (sans le paramètre fields problématique)
            orders = models.execute_kw(
                config['db'], uid, config['password'],
                'sale.order', 'read',
                order_ids
            )
            
            print(f"  📊 Détails des commandes:")
            for order in orders:
                print(f"    • {order.get('name', 'N/A')} - {order.get('state', 'N/A')} - {order.get('amount_total', 0)}€")
        
    except Exception as e:
        print(f"  ❌ Erreur extraction commandes: {e}")
        return False
    
    # Test extraction clients
    print(f"\n👥 Test extraction clients")
    try:
        # Recherche de clients
        partner_ids = models.execute_kw(
            config['db'], uid, config['password'],
            'res.partner', 'search',
            [[('customer_rank', '>', 0)]],
            {'limit': 3}
        )
        
        print(f"  👤 {len(partner_ids)} clients trouvés")
        
        if partner_ids:
            # Lecture des clients
            partners = models.execute_kw(
                config['db'], uid, config['password'],
                'res.partner', 'read',
                partner_ids
            )
            
            print(f"  📊 Détails des clients:")
            for partner in partners:
                print(f"    • {partner.get('name', 'N/A')} - {partner.get('email', 'N/A')}")
        
    except Exception as e:
        print(f"  ❌ Erreur extraction clients: {e}")
        return False
    
    # Test extraction produits
    print(f"\n🛍️ Test extraction produits")
    try:
        # Recherche de produits
        product_ids = models.execute_kw(
            config['db'], uid, config['password'],
            'product.product', 'search',
            [[]],
            {'limit': 3}
        )
        
        print(f"  📦 {len(product_ids)} produits trouvés")
        
        if product_ids:
            # Lecture des produits
            products = models.execute_kw(
                config['db'], uid, config['password'],
                'product.product', 'read',
                product_ids
            )
            
            print(f"  📊 Détails des produits:")
            for product in products:
                print(f"    • {product.get('name', 'N/A')} - {product.get('list_price', 0)}€")
        
    except Exception as e:
        print(f"  ❌ Erreur extraction produits: {e}")
        return False
    
    # Test extraction tickets de support
    print(f"\n🎫 Test extraction tickets de support")
    try:
        # Recherche de tickets
        ticket_ids = models.execute_kw(
            config['db'], uid, config['password'],
            'helpdesk.ticket', 'search',
            [[]],
            {'limit': 3}
        )
        
        print(f"  🎫 {len(ticket_ids)} tickets trouvés")
        
        if ticket_ids:
            # Lecture des tickets
            tickets = models.execute_kw(
                config['db'], uid, config['password'],
                'helpdesk.ticket', 'read',
                ticket_ids
            )
            
            print(f"  📊 Détails des tickets:")
            for ticket in tickets:
                print(f"    • {ticket.get('name', 'N/A')} - {ticket.get('state', 'N/A')}")
        
    except Exception as e:
        print(f"  ⚠️ Tickets de support non disponibles: {e}")
        # Ce n'est pas critique si les tickets ne sont pas disponibles
    
    return True

def test_odoo_client_integration():
    """Test l'intégration du client Odoo"""
    print(f"\n🔧 Test intégration client Odoo")
    
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
        
        print(f"  ✅ Client Odoo initialisé avec succès")
        print(f"  📊 Base de données: {client.database}")
        print(f"  👤 Utilisateur: {client.username}")
        print(f"  🔑 User ID: {client.uid}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur intégration client: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 FlowUp Support Bot - Test Connectivité Odoo Final")
    print("=" * 70)
    
    # Tests de connectivité
    tests = [
        ("Connectivité et extraction complète", test_odoo_complete),
        ("Intégration client Odoo", test_odoo_client_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 50)
        
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
        print(f"🔗 URL: https://www.flowup.shop")
        print(f"📊 Base: production")
        print(f"👤 Utilisateur: dev@flowup.shop")
    else:
        print(f"\n⚠️ {total - successful} test(s) ont échoué")
        print(f"🔧 Des corrections sont nécessaires")
    
    return successful == total

if __name__ == "__main__":
    main()
