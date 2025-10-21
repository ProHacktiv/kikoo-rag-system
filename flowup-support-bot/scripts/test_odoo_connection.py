#!/usr/bin/env python3
"""
Test de connectivité Odoo
Vérifie la connexion avec les credentials du fichier config/odoo_config.json
"""

import sys
import os
import json
import requests
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_odoo_connection():
    """Test la connectivité avec Odoo"""
    print("🔗 Test de Connectivité Odoo")
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
        response = requests.get(config['url'], timeout=10)
        print(f"  ✅ URL accessible: {response.status_code}")
        print(f"  📄 Titre de la page: {response.text[:100]}...")
    except Exception as e:
        print(f"  ❌ URL non accessible: {e}")
        return False
    
    # Test 2: Vérifier l'API Odoo
    print(f"\n🔌 Test 2: API Odoo")
    api_url = f"{config['url']}/web/session/authenticate"
    
    auth_data = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "db": config['db'],
            "login": config['username'],
            "password": config['password']
        },
        "id": 1
    }
    
    try:
        response = requests.post(
            api_url,
            json=auth_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"  📡 Statut API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  📊 Réponse: {result}")
            
            if 'result' in result and result['result']:
                print(f"  ✅ Authentification réussie!")
                return True
            else:
                print(f"  ❌ Authentification échouée: {result}")
                return False
        else:
            print(f"  ❌ Erreur API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur connexion API: {e}")
        return False

def test_odoo_data_extraction():
    """Test l'extraction de données Odoo"""
    print(f"\n📊 Test 3: Extraction de données")
    
    config_path = "/Users/r4v3n/Workspce/Prod/kikoo_rag/config/odoo_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Test extraction des commandes
        api_url = f"{config['url']}/web/dataset/call_kw"
        
        # Requête pour récupérer les commandes
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "sale.order",
                "method": "search_read",
                "args": [],
                "kwargs": {
                    "fields": ["name", "partner_id", "state", "date_order"],
                    "limit": 5
                }
            },
            "id": 1
        }
        
        # Headers avec session
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'session_id=test'  # Session basique pour test
        }
        
        response = requests.post(api_url, json=data, headers=headers, timeout=10)
        
        print(f"  📡 Statut extraction: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  📊 Données extraites: {len(result.get('result', []))} enregistrements")
            
            if 'result' in result and result['result']:
                print(f"  ✅ Extraction réussie!")
                print(f"  📋 Exemple de commande: {result['result'][0] if result['result'] else 'Aucune'}")
                return True
            else:
                print(f"  ⚠️ Aucune donnée extraite: {result}")
                return False
        else:
            print(f"  ❌ Erreur extraction: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur extraction: {e}")
        return False

def test_odoo_integration():
    """Test l'intégration complète Odoo"""
    print(f"\n🔧 Test 4: Intégration complète")
    
    try:
        # Importer le client Odoo
        from src.integrations.odoo_client import OdooClient
        
        # Initialiser le client
        client = OdooClient()
        
        # Test de connexion
        if client.test_connection():
            print(f"  ✅ Client Odoo initialisé avec succès")
            
            # Test récupération d'une commande
            orders = client.get_orders(limit=1)
            if orders:
                print(f"  ✅ Commande récupérée: {orders[0].get('name', 'N/A')}")
                return True
            else:
                print(f"  ⚠️ Aucune commande trouvée")
                return False
        else:
            print(f"  ❌ Échec de connexion client")
            return False
            
    except ImportError as e:
        print(f"  ⚠️ Module OdooClient non disponible: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur intégration: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 FlowUp Support Bot - Test Connectivité Odoo")
    print("=" * 60)
    
    # Tests de connectivité
    tests = [
        ("Connectivité de base", test_odoo_connection),
        ("Extraction de données", test_odoo_data_extraction),
        ("Intégration complète", test_odoo_integration)
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
    else:
        print(f"\n⚠️ {total - successful} test(s) ont échoué")
        print(f"🔧 Des corrections sont nécessaires")
    
    return successful == total

if __name__ == "__main__":
    main()
