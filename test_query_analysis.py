#!/usr/bin/env python3
"""
Test script per analizzare tutti i tipi di risultati di una query SERP
"""

from rank_tracker import RankTracker
from localization import GoogleLocalization
import asyncio
import re

class SERPAnalyzer:
    def __init__(self):
        self.tracker = RankTracker()
        self.localizer = GoogleLocalization()
    
    def analyze_serp_comprehensive(self, html: str):
        """Analizza tutti i tipi di risultati nella SERP"""
        results = {
            'featured_snippets': [],
            'ads': [],
            'organic': [],
            'local_pack': [],
            'shopping': []
        }
        
        # 1. Featured Snippets / Knowledge Panel
        featured_patterns = [
            r'<div[^>]*class="[^"]*(?:kno-rdesc|IZ6rdc|xpdopen|g9WsWb)[^"]*"[^>]*>.*?(?:https?://)?([^/\s<>"]+\.[a-z]{2,})',
            r'<div[^>]*data-attrid="[^"]*"[^>]*>.*?<cite[^>]*>(?:https?://)?([^/<\s]+)',
        ]
        
        for pattern in featured_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                domain = self._clean_domain(match)
                if domain and domain not in [r['domain'] for r in results['featured_snippets']]:
                    results['featured_snippets'].append({
                        'domain': domain,
                        'type': 'featured_snippet'
                    })
        
        # 2. Ads / Sponsored Results
        ads_patterns = [
            r'<div[^>]*class="[^"]*(?:ads|uEierd|com-md-adsheader|v0rgu|mnr-c|pla-unit)[^"]*"[^>]*>.*?<a[^>]*href="[^"]*"[^>]*>.*?(?:https?://)?([^/\s<>"]+\.[a-z]{2,})',
            r'<span[^>]*class="[^"]*(?:sponsorizzato|sponsored|annuncio)[^"]*"[^>]*>.*?(?:https?://)?([^/\s<>"]+\.[a-z]{2,})',
            r'<div[^>]*data-text-ad[^>]*>.*?<cite[^>]*>(?:https?://)?([^/<\s]+)',
        ]
        
        for pattern in ads_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                domain = self._clean_domain(match)
                if domain and domain not in [r['domain'] for r in results['ads']]:
                    results['ads'].append({
                        'domain': domain,
                        'type': 'sponsored'
                    })
        
        # 3. Local Pack / Maps Results
        local_patterns = [
            r'<div[^>]*class="[^"]*(?:rllt__details|VkpGBb|dbg0pd)[^"]*"[^>]*>.*?(?:https?://)?([^/\s<>"]+\.[a-z]{2,})',
            r'<div[^>]*data-local-attribute[^>]*>.*?<cite[^>]*>(?:https?://)?([^/<\s]+)',
        ]
        
        for pattern in local_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                domain = self._clean_domain(match)
                if domain and domain not in [r['domain'] for r in results['local_pack']]:
                    results['local_pack'].append({
                        'domain': domain,
                        'type': 'local_pack'
                    })
        
        # 4. Organic Results (migliorato)
        organic_patterns = [
            # Pattern principale per cite elements (più affidabile)
            r'<cite[^>]*class="[^"]*"[^>]*>(?:https?://)?([^/<\s]+)',
            # Pattern backup per div con g class
            r'<div[^>]*class="[^"]*\bg[^"]*"[^>]*>.*?<a[^>]*href="https?://([^/"]+)',
            # Pattern per h3 con link
            r'<h3[^>]*><a[^>]*href="https?://([^/"]+)',
        ]
        
        # Trova tutti i domini organici in ordine
        organic_domains = []
        for pattern in organic_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                domain = self._clean_domain(match)
                if domain and self._is_organic_domain(domain) and domain not in organic_domains:
                    organic_domains.append(domain)
            
            if organic_domains:  # Se troviamo risultati con questo pattern, usiamoli
                break
        
        # Aggiungi domini organici con posizione
        for i, domain in enumerate(organic_domains[:20], 1):  # Top 20 risultati
            results['organic'].append({
                'domain': domain,
                'position': i,
                'type': 'organic'
            })
        
        return results
    
    def _clean_domain(self, domain_str):
        """Pulisce e normalizza un dominio"""
        if not domain_str:
            return None
        
        domain = domain_str.lower().strip()
        # Rimuovi protocolli
        domain = re.sub(r'^https?://', '', domain)
        # Rimuovi www
        domain = re.sub(r'^www\.', '', domain)
        # Rimuovi path
        domain = domain.split('/')[0]
        # Rimuovi parametri
        domain = domain.split('?')[0]
        domain = domain.split('#')[0]
        # Rimuovi spazi e caratteri strani
        domain = re.sub(r'[^\w\.-]', '', domain)
        
        # Valida che sia un dominio valido
        if '.' not in domain or len(domain) < 3:
            return None
        
        return domain
    
    def _is_organic_domain(self, domain):
        """Verifica se un dominio è valido per risultati organici"""
        if not domain:
            return False
        
        # Escludi domini Google
        google_domains = ['google.', 'youtube.', 'maps.google', 'translate.google', 'support.google']
        if any(gd in domain for gd in google_domains):
            return False
        
        # Deve essere un dominio valido
        if '.' not in domain or len(domain) < 3:
            return False
        
        return True
    
    async def test_query(self, keyword, localization_config=None):
        """Testa una query specifica e analizza tutti i risultati"""
        if not localization_config:
            localization_config = {
                'country_code': 'IT',
                'language_code': 'it',
                'city_code': 'milano',  # Test con Milano per Brescia
                'content_restriction': True
            }
        
        print(f"🔍 Testing query: '{keyword}'")
        print(f"📍 Localizzazione: {localization_config}")
        
        try:
            await self.tracker.init_crawler()
            
            url = self.tracker.build_google_url(keyword, localization_config)
            print(f"🌐 URL: {url}")
            
            # Headers per sembrare più umani
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Crawl della SERP
            result = await self.tracker.crawler.arun(
                url=url,
                headers=headers,
                wait_for="body",
                delay_before_return_html=3
            )
            
            if not result.success:
                print(f"❌ Errore crawling: {result.error_message}")
                return
            
            print(f"✅ SERP crawlata con successo ({len(result.html)} caratteri)")
            
            # Analizza tutti i tipi di risultati
            analysis = self.analyze_serp_comprehensive(result.html)
            
            # Stampa risultati
            self._print_results(analysis)
            
            # Salva HTML per debug
            with open(f"serp_debug_{keyword.replace(' ', '_')}.html", 'w', encoding='utf-8') as f:
                f.write(result.html)
            print(f"💾 HTML salvato come: serp_debug_{keyword.replace(' ', '_')}.html")
            
        except Exception as e:
            print(f"❌ Errore durante test: {e}")
        finally:
            await self.tracker.close_crawler()
    
    def _print_results(self, analysis):
        """Stampa i risultati dell'analisi in modo ordinato"""
        print("\n" + "="*60)
        print("📊 ANALISI RISULTATI SERP")
        print("="*60)
        
        # Featured Snippets
        if analysis['featured_snippets']:
            print(f"\n🏆 FEATURED SNIPPETS ({len(analysis['featured_snippets'])})")
            for i, result in enumerate(analysis['featured_snippets'], 1):
                print(f"  {i}. {result['domain']} ({result['type']})")
        
        # Ads
        if analysis['ads']:
            print(f"\n💰 ANNUNCI SPONSORIZZATI ({len(analysis['ads'])})")
            for i, result in enumerate(analysis['ads'], 1):
                print(f"  {i}. {result['domain']} (SPONSORED)")
        
        # Local Pack
        if analysis['local_pack']:
            print(f"\n📍 LOCAL PACK ({len(analysis['local_pack'])})")
            for i, result in enumerate(analysis['local_pack'], 1):
                print(f"  {i}. {result['domain']} (local)")
        
        # Organic Results
        print(f"\n🌿 RISULTATI ORGANICI ({len(analysis['organic'])})")
        for result in analysis['organic']:
            print(f"  {result['position']}. {result['domain']}")
        
        print("\n" + "="*60)

async def main():
    analyzer = SERPAnalyzer()
    
    # Test con query "web agency a brescia"
    await analyzer.test_query(
        keyword="web agency a brescia",
        localization_config={
            'country_code': 'IT',
            'language_code': 'it',
            'city_code': None,  # Senza localizzazione specifica
            'content_restriction': True
        }
    )

if __name__ == "__main__":
    asyncio.run(main())