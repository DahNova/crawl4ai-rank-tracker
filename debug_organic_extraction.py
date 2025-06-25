#!/usr/bin/env python3
"""
Debug dell'estrazione dei risultati organici
"""

from rank_tracker import RankTracker
from serp_analyzer import SERPAnalyzer
import asyncio
import re

async def debug_organic_extraction():
    """Debug dell'estrazione risultati organici"""
    print("🔍 DEBUG: Estrazione risultati organici")
    print("="*60)
    
    tracker = RankTracker()
    analyzer = SERPAnalyzer()
    
    try:
        await tracker.init_crawler()
        
        # Test con keyword che dovrebbe avere isacco.it primo
        keyword = "isacco abbigliamento"
        localization_config = {
            'country_code': 'IT',
            'language_code': 'it',
            'city_code': None,
            'content_restriction': True
        }
        
        url = tracker.build_google_url(keyword, localization_config)
        print(f"📡 URL: {url}")
        
        # Crawl
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        result = await tracker.crawler.arun(
            url=url, 
            headers=headers, 
            wait_for="body", 
            delay_before_return_html=2
        )
        
        if not result.success:
            print(f"❌ Crawling fallito: {result.error_message}")
            return
        
        html = result.html
        print(f"✅ HTML ottenuto: {len(html)} caratteri")
        
        # 1. Cerca manualmente "isacco.it" nell'HTML
        print(f"\n🔍 STEP 1: Ricerca manuale 'isacco.it' nell'HTML")
        isacco_it_direct = html.count('isacco.it')
        print(f"Occorrenze 'isacco.it': {isacco_it_direct}")
        
        # Trova contesti dove appare isacco.it
        isacco_contexts = []
        for match in re.finditer(r'.{0,100}isacco\.it.{0,100}', html, re.IGNORECASE):
            isacco_contexts.append(match.group())
        
        print(f"Contesti trovati: {len(isacco_contexts)}")
        for i, context in enumerate(isacco_contexts[:5], 1):
            print(f"  {i}. ...{context}...")
        
        # 2. Test dei pattern del SERPAnalyzer
        print(f"\n🔍 STEP 2: Test pattern SERPAnalyzer")
        
        patterns = [
            r'<cite[^>]*class=\"[^\"]*\"[^>]*>(?:https?://)?([^<\\s]+)',
            r'<div[^>]*class=\"[^\"]*\\bg[^\"]*\"[^>]*>.*?<a[^>]*href=\"https?://([^/\"]+)',
            r'<h3[^>]*><a[^>]*href=\"https?://([^/\"]+)',
        ]
        
        for i, pattern in enumerate(patterns, 1):
            print(f"\nPattern {i}: {pattern}")
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            print(f"  Matches totali: {len(matches)}")
            
            # Filtra per isacco
            isacco_matches = [m for m in matches if 'isacco' in m.lower()]
            print(f"  Matches con 'isacco': {len(isacco_matches)}")
            
            for j, match in enumerate(isacco_matches, 1):
                clean_match = analyzer._clean_domain(match)
                print(f"    {j}. {match} -> {clean_match}")
        
        # 3. Test del metodo completo
        print(f"\n🔍 STEP 3: Metodo _extract_organic_results completo")
        organic_results = analyzer._extract_organic_results(html)
        print(f"Risultati organici estratti: {len(organic_results)}")
        
        for i, result in enumerate(organic_results, 1):
            domain = result.get('domain')
            print(f"  {i}. {domain}")
            
            if 'isacco' in domain.lower():
                print(f"      ✅ ISACCO TROVATO: {result}")
        
        # 4. Test con pattern più aggressivi per cite
        print(f"\n🔍 STEP 4: Pattern cite più aggressivi")
        
        cite_patterns = [
            r'<cite[^>]*>([^<]+)</cite>',
            r'<cite[^>]*class=\"[^\"]*\"[^>]*>([^<]+)</cite>',
            r'<cite[^>]*>(?:https?://)?([^<\\s]+)</cite>',
        ]
        
        for i, pattern in enumerate(cite_patterns, 1):
            print(f"\nCite pattern {i}: {pattern}")
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            print(f"  Cite matches: {len(matches)}")
            
            for j, match in enumerate(matches, 1):
                if 'isacco' in match.lower():
                    clean_match = analyzer._clean_domain(match)
                    print(f"    {j}. {match} -> {clean_match}")
        
        # 5. Salva HTML per debug
        debug_filename = f"debug_organic_extraction.html"
        with open(debug_filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n💾 HTML salvato in: {debug_filename}")
        
    except Exception as e:
        print(f"❌ Errore durante debug: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tracker.close_crawler()

if __name__ == "__main__":
    asyncio.run(debug_organic_extraction())