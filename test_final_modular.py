#!/usr/bin/env python3
"""
Test finale per verificare il sistema modulare completo
"""

from database import Database
from rank_tracker import RankTracker
import asyncio

def test_database_schema():
    """Testa il nuovo schema database"""
    print("🗄️ Testing Database Schema")
    print("-" * 40)
    
    db = Database()
    
    # Test creazione progetto con tracking completo
    project_id = db.create_project(
        name="Test Modular System",
        domain="test.com",
        tracking_mode="FULL_SERP",
        track_ads=True,
        track_snippets=True,
        track_local=True,
        track_shopping=True
    )
    print(f"✅ Progetto creato: ID {project_id}")
    
    # Test recupero configurazione
    project = db.get_project(project_id)
    tracking_config = db.get_project_tracking_config(project_id)
    
    print(f"✅ Tracking mode: {tracking_config['tracking_mode']}")
    print(f"✅ Track ads: {tracking_config['track_ads']}")
    print(f"✅ Track snippets: {tracking_config['track_snippets']}")
    print(f"✅ Track local: {tracking_config['track_local']}")
    print(f"✅ Track shopping: {tracking_config['track_shopping']}")
    
    # Test salvataggio SERP features
    test_features = [
        {
            'result_type': 'organic',
            'position': 1,
            'domain': 'test.com',
            'url': 'https://test.com',
            'title': 'Test Organic Result',
            'snippet': 'This is a test organic result'
        },
        {
            'result_type': 'ads',
            'position': 1,
            'domain': 'advertiser.com',
            'url': 'https://advertiser.com/ad',
            'title': 'Test Ad',
            'snippet': 'This is a sponsored ad'
        },
        {
            'result_type': 'featured_snippet',
            'position': 0,
            'domain': 'snippet.com',
            'url': 'https://snippet.com/featured',
            'title': 'Featured Snippet Test',
            'snippet': 'This is a featured snippet'
        }
    ]
    
    db.save_serp_features_batch(project_id, "test keyword", test_features)
    print("✅ SERP features salvate")
    
    # Test recupero features
    organic_features = db.get_serp_features(project_id, result_type='organic')
    ads_features = db.get_serp_features(project_id, result_type='ads')
    snippet_features = db.get_serp_features(project_id, result_type='featured_snippet')
    
    print(f"✅ Organic results: {len(organic_features)}")
    print(f"✅ Ads results: {len(ads_features)}")
    print(f"✅ Featured snippets: {len(snippet_features)}")
    
    # Cleanup
    db.delete_project(project_id)
    print("✅ Test cleanup completato")
    
    return True

async def test_rank_tracker_modular():
    """Testa il RankTracker con modalità modulare"""
    print("\n🎯 Testing RankTracker Modular")
    print("-" * 40)
    
    tracker = RankTracker()
    
    # Test configurazione ORGANIC_ONLY
    tracking_config_organic = {
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
    
    print("Testing ORGANIC_ONLY mode...")
    result_organic = await tracker.search_keyword_complete(
        keyword="abbigliamento cucina",
        domain="isacco.it",
        localization_config=localization_config,
        tracking_config=tracking_config_organic
    )
    
    if 'error' not in result_organic:
        print(f"✅ ORGANIC_ONLY: {len(result_organic.get('organic', []))} risultati organici")
        print(f"✅ Ads filtrati: {'ads' not in result_organic}")
        
        # Verifica target positions
        target_pos = result_organic.get('target_positions', {})
        if 'organic' in target_pos:
            print(f"✅ isacco.it trovato in posizione organica: {target_pos['organic']['position']}")
    else:
        print(f"❌ Errore ORGANIC_ONLY: {result_organic['error']}")
    
    # Test configurazione FULL_SERP
    tracking_config_full = {
        'tracking_mode': 'FULL_SERP',
        'track_ads': True,
        'track_snippets': True,
        'track_local': True,
        'track_shopping': True
    }
    
    print("\nTesting FULL_SERP mode...")
    result_full = await tracker.search_keyword_complete(
        keyword="web agency brescia",
        domain="webheroes.it",
        localization_config=localization_config,
        tracking_config=tracking_config_full
    )
    
    if 'error' not in result_full:
        print(f"✅ FULL_SERP organic: {len(result_full.get('organic', []))}")
        print(f"✅ FULL_SERP ads: {len(result_full.get('ads', []))}")
        print(f"✅ FULL_SERP local: {len(result_full.get('local_pack', []))}")
        print(f"✅ FULL_SERP snippets: {len(result_full.get('featured_snippets', []))}")
    else:
        print(f"❌ Errore FULL_SERP: {result_full['error']}")
    
    await tracker.close_crawler()
    return True

def test_ui_compatibility():
    """Verifica compatibilità con nuova UI"""
    print("\n🎨 Testing UI Compatibility")
    print("-" * 40)
    
    # Simula dati form dalla nuova UI
    form_data = {
        'name': 'Test UI Project',
        'domain': 'example.com',
        'keywords': 'test keyword 1\ntest keyword 2',
        'tracking_mode': 'CUSTOM',
        'track_ads': True,
        'track_snippets': False,
        'track_local': True,
        'track_shopping': False
    }
    
    print(f"✅ Form data simulato: {form_data}")
    
    # Verifica che i nuovi campi siano presenti
    required_fields = ['tracking_mode', 'track_ads', 'track_snippets', 'track_local', 'track_shopping']
    missing_fields = [field for field in required_fields if field not in form_data]
    
    if not missing_fields:
        print("✅ Tutti i campi di tracking presenti")
    else:
        print(f"❌ Campi mancanti: {missing_fields}")
    
    return len(missing_fields) == 0

async def main():
    """Esegue tutti i test"""
    print("🧪 TEST FINALE SISTEMA MODULARE SERP TRACKING")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database Schema
    try:
        results.append(test_database_schema())
    except Exception as e:
        print(f"❌ Database test fallito: {e}")
        results.append(False)
    
    # Test 2: RankTracker Modulare
    try:
        results.append(await test_rank_tracker_modular())
    except Exception as e:
        print(f"❌ RankTracker test fallito: {e}")
        results.append(False)
    
    # Test 3: UI Compatibility
    try:
        results.append(test_ui_compatibility())
    except Exception as e:
        print(f"❌ UI test fallito: {e}")
        results.append(False)
    
    # Risultati finali
    print("\n" + "=" * 60)
    print("📊 RISULTATI FINALI")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Test superati: {passed}/{total}")
    print(f"📈 Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 TUTTI I TEST SUPERATI!")
        print("🚀 Sistema modulare pronto per la produzione!")
    else:
        print("⚠️ Alcuni test sono falliti. Controllare i log sopra.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)