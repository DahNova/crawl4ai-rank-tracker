#!/usr/bin/env python3
"""
Test del nuovo browser mode anti-detection
"""

from rank_tracker import RankTracker
import asyncio

async def test_browser_mode():
    """Testa il nuovo browser mode"""
    print("🌐 TEST BROWSER MODE ANTI-DETECTION")
    print("="*50)
    
    tracker = RankTracker()
    
    try:
        # Test con keyword semplice
        keyword = "abbigliamento cucina"
        domain = "isacco.it"
        
        localization_config = {
            'country_code': 'IT',
            'language_code': 'it',
            'city_code': None,
            'content_restriction': True
        }
        
        tracking_config = {
            'tracking_mode': 'ORGANIC_ONLY',
            'track_ads': False,
            'track_snippets': False,
            'track_local': False,
            'track_shopping': False
        }
        
        print(f"🔍 Testing: '{keyword}' per dominio {domain}")
        print("🌐 Usando browser mode avanzato...")
        
        result = await tracker.search_keyword_complete(
            keyword=keyword,
            domain=domain,
            localization_config=localization_config,
            tracking_config=tracking_config
        )
        
        print("\n📊 RISULTATI:")
        print("-" * 30)
        
        if 'error' in result:
            print(f"❌ Errore: {result['error']}")
        else:
            # Mostra dimensione HTML se disponibile
            metadata = result.get('metadata', {})
            print(f"✅ Crawling riuscito!")
            
            # Mostra risultati organici
            organic_results = result.get('organic', [])
            print(f"📈 Risultati organici: {len(organic_results)}")
            
            for i, res in enumerate(organic_results[:10], 1):
                domain_found = res.get('domain', 'N/A')
                print(f"  {i}. {domain_found}")
            
            # Mostra target positions
            target_positions = result.get('target_positions', {})
            if target_positions:
                print(f"\n🎯 Target '{domain}' trovato:")
                for result_type, pos_info in target_positions.items():
                    pos = pos_info.get('position')
                    url = pos_info.get('url', '')
                    print(f"  {result_type}: posizione {pos}")
                    if url:
                        print(f"    URL: {url}")
            else:
                print(f"\n❌ Target '{domain}' non trovato")
        
        print(f"\n🏁 Test completato!")
        
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tracker.close_crawler()

if __name__ == "__main__":
    asyncio.run(test_browser_mode())