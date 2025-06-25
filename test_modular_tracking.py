#!/usr/bin/env python3
"""
Test script per il nuovo sistema modulare di tracking SERP
"""

from rank_tracker import RankTracker
from database import Database
import asyncio
import json

async def test_modular_tracking():
    """Testa il nuovo sistema di tracking modulare"""
    
    # Inizializza componenti
    tracker = RankTracker()
    db = Database()
    
    print("🧪 Test Sistema Modulare SERP Tracking")
    print("="*60)
    
    # Test 1: Tracking ORGANIC_ONLY
    print("\n📋 Test 1: ORGANIC_ONLY Mode")
    tracking_config = {
        'tracking_mode': 'ORGANIC_ONLY',
        'track_ads': False,
        'track_snippets': False,
        'track_local': False,
        'track_shopping': False
    }
    
    localization_config = {
        'country_code': 'IT',
        'language_code': 'it',
        'city_code': None,
        'content_restriction': True
    }
    
    result = await tracker.search_keyword_complete(
        keyword="abbigliamento cucina",
        domain="isacco.it",
        localization_config=localization_config,
        tracking_config=tracking_config
    )
    
    print_result_summary("ORGANIC_ONLY", result)
    
    # Test 2: Tracking FULL_SERP
    print("\n📋 Test 2: FULL_SERP Mode")
    tracking_config_full = {
        'tracking_mode': 'FULL_SERP',
        'track_ads': True,
        'track_snippets': True,
        'track_local': True,
        'track_shopping': True
    }
    
    result_full = await tracker.search_keyword_complete(
        keyword="web agency brescia",
        domain="webheroes.it",
        localization_config=localization_config,
        tracking_config=tracking_config_full
    )
    
    print_result_summary("FULL_SERP", result_full)
    
    # Test 3: Tracking CUSTOM
    print("\n📋 Test 3: CUSTOM Mode (solo organici + ads)")
    tracking_config_custom = {
        'tracking_mode': 'CUSTOM',
        'track_ads': True,
        'track_snippets': False,
        'track_local': False,
        'track_shopping': False
    }
    
    result_custom = await tracker.search_keyword_complete(
        keyword="divise isacco",
        domain="isacco.it", 
        localization_config=localization_config,
        tracking_config=tracking_config_custom
    )
    
    print_result_summary("CUSTOM (organici + ads)", result_custom)
    
    # Test 4: Database integration
    print("\n📋 Test 4: Database Integration")
    test_database_integration(db)
    
    await tracker.close_crawler()
    print("\n✅ Tutti i test completati!")

def print_result_summary(mode: str, result: dict):
    """Stampa riassunto dei risultati"""
    print(f"Modalità: {mode}")
    
    if 'error' in result:
        print(f"❌ Errore: {result['error']}")
        return
    
    # Conta risultati per tipo
    counts = {}
    target_found = {}
    
    for result_type, results in result.items():
        if result_type in ['metadata', 'target_positions']:
            continue
        
        if isinstance(results, list):
            counts[result_type] = len(results)
            
            # Cerca il target domain nei risultati
            for res in results:
                if 'domain' in res:
                    domain = res['domain']
                    if any(target in domain for target in ['isacco.it', 'webheroes.it']):
                        target_found[result_type] = {
                            'position': res.get('position'),
                            'domain': domain,
                            'url': res.get('url', '')
                        }
    
    # Stampa conteggi
    print("  Risultati trovati:")
    for result_type, count in counts.items():
        print(f"    {result_type}: {count}")
    
    # Stampa posizioni target
    if target_found:
        print("  Target domain trovato in:")
        for result_type, info in target_found.items():
            pos = info['position']
            domain = info['domain']
            print(f"    {result_type}: posizione {pos} ({domain})")
    else:
        print("  ❌ Target domain non trovato")

def test_database_integration(db: Database):
    """Testa l'integrazione database"""
    print("Testando nuovo schema database...")
    
    # Test creazione progetto con tracking options
    try:
        project_id = db.create_project(
            name="Test Modular Tracking",
            domain="test.com",
            tracking_mode="FULL_SERP",
            track_ads=True,
            track_snippets=True,
            track_local=False,
            track_shopping=False
        )
        print(f"✅ Progetto creato con ID: {project_id}")
        
        # Test recupero configurazione tracking
        tracking_config = db.get_project_tracking_config(project_id)
        print(f"✅ Config tracking: {tracking_config}")
        
        # Test salvataggio SERP features
        test_features = [
            {
                'result_type': 'organic',
                'position': 1,
                'domain': 'test.com',
                'url': 'https://test.com',
                'title': 'Test Title',
                'snippet': 'Test snippet'
            },
            {
                'result_type': 'ads',
                'position': 1,
                'domain': 'advertiser.com',
                'url': 'https://advertiser.com',
                'title': 'Ad Title',
                'snippet': ''
            }
        ]
        
        db.save_serp_features_batch(project_id, "test keyword", test_features)
        print("✅ SERP features salvate")
        
        # Test recupero features
        features = db.get_serp_features(project_id, "test keyword")
        print(f"✅ Features recuperate: {len(features)} items")
        
        # Cleanup
        db.delete_project(project_id)
        print("✅ Test project eliminato")
        
    except Exception as e:
        print(f"❌ Errore database: {e}")

if __name__ == "__main__":
    asyncio.run(test_modular_tracking())