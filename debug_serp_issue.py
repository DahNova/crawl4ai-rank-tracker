#!/usr/bin/env python3
"""
Debug per capire perché il SERPAnalyzer non trova isacco.it
"""

from rank_tracker import RankTracker
from serp_analyzer import SERPAnalyzer
import asyncio
import re

async def debug_serp_parsing():
    """Debug completo del parsing SERP"""
    print("🔍 DEBUG: Analisi SERP per abbigliamento cucina")
    print("="*60)
    
    tracker = RankTracker()
    analyzer = SERPAnalyzer()
    
    try:
        await tracker.init_crawler()
        
        # Test una keyword che sappiamo dovrebbe funzionare
        keyword = "abbigliamento cucina"
        localization_config = {
            'country_code': 'IT',
            'language_code': 'it',
            'city_code': None,
            'content_restriction': True
        }
        
        url = tracker.build_google_url(keyword, localization_config)
        print(f"📡 URL: {url}")
        
        # Crawl
        headers = {'User-Agent': tracker.ua.random}
        result = await tracker.crawler.arun(url=url, headers=headers, wait_for="body", delay_before_return_html=2)
        
        if not result.success:
            print(f"❌ Crawling fallito: {result.error_message}")
            return
        
        html = result.html
        print(f"✅ HTML ottenuto: {len(html)} caratteri")
        
        # 1. Debug: cerca manualmente isacco.it nell'HTML
        print("\n🔍 STEP 1: Ricerca manuale di 'isacco' nell'HTML")
        isacco_mentions = re.findall(r'[^a-zA-Z]isacco[^a-zA-Z].*?', html, re.IGNORECASE)
        print(f"Menzioni 'isacco' trovate: {len(isacco_mentions)}")
        for i, mention in enumerate(isacco_mentions[:5], 1):
            print(f"  {i}. {mention[:100]}...")
        
        # 2. Debug: cerca cite specificamente
        print("\n🔍 STEP 2: Pattern cite utilizzati dal SERPAnalyzer")
        cite_pattern = r'<cite[^>]*class="[^"]*"[^>]*>(?:https?://)?([^<\s]+)</cite>'
        cite_matches = re.findall(cite_pattern, html, re.IGNORECASE | re.DOTALL)
        
        print(f"Cite trovate: {len(cite_matches)}")
        for i, cite in enumerate(cite_matches, 1):
            clean_cite = cite.lower().replace('www.', '').strip()
            print(f"  {i}. {clean_cite}")
            
            if 'isacco' in clean_cite:
                print(f"     ✅ MATCH ISACCO! Posizione {i}")
        
        # 3. Debug: usa il SERPAnalyzer completo
        print("\n🔍 STEP 3: SERPAnalyzer completo")
        analysis = analyzer.analyze_complete_serp(html, "isacco.it")
        
        print(f"Risultati organici trovati: {len(analysis.get('organic', []))}")
        for i, result in enumerate(analysis.get('organic', []), 1):
            print(f"  {i}. {result.get('domain')} (pos: {result.get('position')})")
        
        print(f"\nTarget positions: {analysis.get('target_positions', {})}")
        
        # 4. Debug: pattern più aggressivo
        print("\n🔍 STEP 4: Pattern aggressivo per trovare isacco")
        aggressive_patterns = [
            r'isacco\.it',
            r'www\.isacco\.it', 
            r'https?://[^"]*isacco\.it[^"]*',
            r'<cite[^>]*>[^<]*isacco[^<]*</cite>',
            r'<a[^>]*href="[^"]*isacco\.it[^"]*"'
        ]
        
        for i, pattern in enumerate(aggressive_patterns, 1):
            matches = re.findall(pattern, html, re.IGNORECASE)
            print(f"Pattern {i}: {len(matches)} matches")
            if matches:
                for j, match in enumerate(matches[:3], 1):
                    print(f"  {j}. {match}")
        
        # 5. Debug: salva HTML per ispezione manuale
        debug_filename = f"debug_serp_{keyword.replace(' ', '_')}.html"
        with open(debug_filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n💾 HTML salvato in: {debug_filename}")
        
        # 6. Test con dominio diverso per confronto
        print("\n🔍 STEP 5: Test con altri domini presenti")
        other_domains = ['amazon.it', 'zalando.it', 'epipoli.it']
        
        for domain in other_domains:
            analysis_test = analyzer.analyze_complete_serp(html, domain)
            target_pos = analysis_test.get('target_positions', {})
            if target_pos:
                print(f"✅ {domain} trovato: {target_pos}")
            else:
                print(f"❌ {domain} non trovato")
        
    except Exception as e:
        print(f"❌ Errore durante debug: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tracker.close_crawler()

if __name__ == "__main__":
    asyncio.run(debug_serp_parsing())