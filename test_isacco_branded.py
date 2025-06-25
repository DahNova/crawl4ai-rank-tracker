#!/usr/bin/env python3
"""
Test browser mode con keyword branded di isacco.it
"""

from rank_tracker import RankTracker
import asyncio

async def test_isacco_branded():
    """Test con keyword branded di isacco"""
    print("🎯 TEST KEYWORD BRANDED ISACCO")
    print("="*50)
    
    tracker = RankTracker()
    
    try:
        # Test con keyword branded che dovrebbe trovare isacco
        branded_keywords = [
            "isacco abbigliamento",
            "isacco uniformi",
            "isacco.it",
            "isacco lavoro"
        ]
        
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
        
        for keyword in branded_keywords:
            print(f"\n🔍 Testing: '{keyword}' per dominio {domain}")
            
            result = await tracker.search_keyword_complete(
                keyword=keyword,
                domain=domain,
                localization_config=localization_config,
                tracking_config=tracking_config
            )
            
            print(f"📊 RISULTATI per '{keyword}':")
            print("-" * 40)
            
            if 'error' in result:
                print(f"❌ Errore: {result['error']}")
            else:
                # Mostra risultati organici
                organic_results = result.get('organic', [])
                print(f"📈 Risultati organici: {len(organic_results)}")
                
                for i, res in enumerate(organic_results[:5], 1):
                    domain_found = res.get('domain', 'N/A')
                    print(f"  {i}. {domain_found}")
                
                # Mostra target positions
                target_positions = result.get('target_positions', {})
                if target_positions:
                    print(f"✅ Target '{domain}' TROVATO:")
                    for result_type, pos_info in target_positions.items():
                        pos = pos_info.get('position')
                        url = pos_info.get('url', '')
                        print(f"  {result_type}: posizione {pos}")
                        if url:
                            print(f"    URL: {url}")
                else:
                    print(f"❌ Target '{domain}' non trovato")
            
            # Pausa tra keyword per evitare rate limiting
            await asyncio.sleep(5)
        
        print(f"\n🏁 Test branded completato!")
        
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tracker.close_crawler()

if __name__ == "__main__":
    asyncio.run(test_isacco_branded())