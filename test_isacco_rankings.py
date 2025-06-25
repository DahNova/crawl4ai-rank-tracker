#!/usr/bin/env python3
"""
Test script per tracciare le posizioni specifiche di isacco.it su keyword target
"""

from rank_tracker import RankTracker
from localization import GoogleLocalization
import asyncio
import re
import time

class IsaccoRankingTester:
    def __init__(self):
        self.tracker = RankTracker()
        self.localizer = GoogleLocalization()
        self.target_domain = "isacco.it"
        
    def analyze_isacco_position(self, html: str):
        """Analizza la posizione specifica di isacco.it nei risultati organici"""
        results = {
            'organic_position': None,
            'organic_url': None,
            'found_in_ads': False,
            'ads_urls': [],
            'all_isacco_urls': []
        }
        
        # 1. Trova tutti i link a isacco.it
        all_isacco_pattern = r'href="([^"]*isacco\.it[^"]*)"'
        all_matches = re.findall(all_isacco_pattern, html, re.IGNORECASE)
        results['all_isacco_urls'] = list(set(all_matches))
        
        # 2. Controlla se è presente negli ads
        ads_context_patterns = [
            r'<div[^>]*class="[^"]*(?:ads|uEierd|mnr-c|v0rgu)[^"]*"[^>]*>.*?href="([^"]*isacco\.it[^"]*)"',
            r'<span[^>]*(?:sponsorizzato|sponsored|annuncio)[^>]*>.*?href="([^"]*isacco\.it[^"]*)"',
        ]
        
        for pattern in ads_context_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            if matches:
                results['found_in_ads'] = True
                results['ads_urls'].extend(matches)
        
        # 3. Trova posizione organica usando pattern migliorati
        organic_patterns = [
            # Pattern principale per cite (più affidabile per ordine)
            r'<cite[^>]*class="[^"]*"[^>]*>(?:https?://)?([^/<\s]+)',
            # Pattern backup per div container organici
            r'<div[^>]*class="[^"]*\bg[^"]*"[^>]*>.*?<a[^>]*href="https?://([^/"]+)',
            # Pattern per h3 link
            r'<h3[^>]*><a[^>]*href="https?://([^/"]+)',
        ]
        
        # Trova tutti i domini organici in ordine
        organic_domains = []
        organic_urls_map = {}  # Mappa dominio -> URL completa
        
        for pattern in organic_patterns:
            # Pattern modificato per catturare anche URL completa
            if 'cite' in pattern:
                # Per cite, modifica pattern per catturare URL completa
                url_pattern = r'<cite[^>]*class="[^"]*"[^>]*>(?:https?://)?([^<\s]+)'
                matches = re.findall(url_pattern, html, re.IGNORECASE | re.DOTALL)
                
                for match in matches:
                    # Pulisci l'URL
                    clean_url = match.strip().rstrip('/')
                    if not clean_url.startswith('http'):
                        clean_url = 'https://' + clean_url
                    
                    domain = self._extract_domain(clean_url)
                    if domain and self._is_valid_organic_domain(domain) and domain not in organic_domains:
                        organic_domains.append(domain)
                        organic_urls_map[domain] = clean_url
            else:
                # Per altri pattern, trova dominio e poi cerca URL completa nel contesto
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    domain = self._clean_domain(match)
                    if domain and self._is_valid_organic_domain(domain) and domain not in organic_domains:
                        organic_domains.append(domain)
                        # Cerca URL completa nel contesto
                        url_search = re.search(rf'href="(https?://{re.escape(domain)}[^"]*)"', html, re.IGNORECASE)
                        if url_search:
                            organic_urls_map[domain] = url_search.group(1)
            
            if organic_domains:  # Se troviamo risultati, usiamo questi
                break
        
        # 4. Trova posizione di isacco.it
        isacco_domain = self._clean_domain(self.target_domain)
        for i, domain in enumerate(organic_domains, 1):
            if domain == isacco_domain:
                results['organic_position'] = i
                results['organic_url'] = organic_urls_map.get(domain, f"https://{domain}")
                break
        
        # Debug info
        results['debug'] = {
            'total_organic_found': len(organic_domains),
            'organic_domains_top10': organic_domains[:10],
            'total_isacco_urls': len(results['all_isacco_urls'])
        }
        
        return results
    
    def _extract_domain(self, url):
        """Estrae il dominio da una URL"""
        if not url:
            return None
        
        # Rimuovi protocollo
        domain = re.sub(r'^https?://', '', url.lower())
        # Rimuovi www
        domain = re.sub(r'^www\.', '', domain)
        # Prendi solo la parte del dominio
        domain = domain.split('/')[0].split('?')[0].split('#')[0]
        
        return domain if '.' in domain and len(domain) > 2 else None
    
    def _clean_domain(self, domain_str):
        """Pulisce e normalizza un dominio"""
        if not domain_str:
            return None
        
        domain = domain_str.lower().strip()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0].split('?')[0].split('#')[0]
        domain = re.sub(r'[^\w\.-]', '', domain)
        
        return domain if '.' in domain and len(domain) > 2 else None
    
    def _is_valid_organic_domain(self, domain):
        """Verifica se un dominio è valido per risultati organici"""
        if not domain:
            return False
        
        # Escludi domini Google
        google_domains = ['google.', 'youtube.', 'maps.google', 'translate.google']
        if any(gd in domain for gd in google_domains):
            return False
        
        return '.' in domain and len(domain) > 2
    
    async def test_keyword_rankings(self, keywords):
        """Testa le posizioni di isacco.it per una lista di keyword"""
        print(f"🎯 Testing rankings per isacco.it su {len(keywords)} keywords")
        print("="*80)
        
        results = {}
        
        try:
            await self.tracker.init_crawler()
            
            for i, keyword in enumerate(keywords, 1):
                print(f"\n🔍 [{i}/{len(keywords)}] Testing: '{keyword}'")
                
                try:
                    # Configurazione localizzazione Italia
                    localization_config = {
                        'country_code': 'IT',
                        'language_code': 'it',
                        'city_code': None,
                        'content_restriction': True
                    }
                    
                    url = self.tracker.build_google_url(keyword, localization_config)
                    
                    # Headers realistici
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                    }
                    
                    # Crawl
                    result = await self.tracker.crawler.arun(
                        url=url,
                        headers=headers,
                        wait_for="body",
                        delay_before_return_html=2
                    )
                    
                    if not result.success:
                        print(f"   ❌ Errore crawling: {result.error_message}")
                        results[keyword] = {'error': result.error_message}
                        continue
                    
                    # Analizza posizione isacco.it
                    analysis = self.analyze_isacco_position(result.html)
                    results[keyword] = analysis
                    
                    # Stampa risultato
                    if analysis['organic_position']:
                        print(f"   ✅ Posizione: {analysis['organic_position']}")
                        print(f"   🔗 URL: {analysis['organic_url']}")
                    else:
                        print(f"   ❌ Non trovato in top {analysis['debug']['total_organic_found']} organici")
                    
                    if analysis['found_in_ads']:
                        print(f"   💰 Trovato anche negli ads: {len(analysis['ads_urls'])} link")
                    
                    # Delay tra le richieste per evitare rate limiting
                    if i < len(keywords):
                        await asyncio.sleep(3)
                        
                except Exception as e:
                    print(f"   ❌ Errore: {e}")
                    results[keyword] = {'error': str(e)}
            
        finally:
            await self.tracker.close_crawler()
        
        # Stampa riassunto finale
        self._print_summary(results)
        return results
    
    def _print_summary(self, results):
        """Stampa riassunto finale dei risultati"""
        print("\n" + "="*80)
        print("📊 RIASSUNTO POSIZIONI ISACCO.IT")
        print("="*80)
        
        found_count = 0
        not_found_count = 0
        
        for keyword, data in results.items():
            if 'error' in data:
                print(f"❌ {keyword:<40} ERROR: {data['error']}")
            elif data.get('organic_position'):
                pos = data['organic_position']
                url = data.get('organic_url', '').replace('https://www.isacco.it', '').replace('https://isacco.it', '')
                ads_note = " + ADS" if data.get('found_in_ads') else ""
                print(f"✅ {keyword:<40} Posizione {pos:>2}{ads_note}")
                print(f"   🔗 {url}")
                found_count += 1
            else:
                total_organic = data.get('debug', {}).get('total_organic_found', '?')
                print(f"❌ {keyword:<40} Non in top {total_organic} organici")
                not_found_count += 1
        
        print("\n" + "-"*80)
        print(f"📈 Trovato in {found_count} keyword")
        print(f"📉 Non trovato in {not_found_count} keyword")
        print(f"🎯 Success rate: {found_count/(found_count+not_found_count)*100:.1f}%")

async def main():
    tester = IsaccoRankingTester()
    
    # Keywords da testare
    keywords = [
        "abbigliamento alberghiere",
        "abbigliamento cucina", 
        "abbigliamento da lavoro",
        "abbigliamento da lavoro professionale",
        "abbigliamento e divise da lavoro",
        "abbigliamento e divise da lavoro online",
        "abbigliamento fiorista"
    ]
    
    await tester.test_keyword_rankings(keywords)

if __name__ == "__main__":
    asyncio.run(main())