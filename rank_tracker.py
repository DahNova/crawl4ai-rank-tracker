import asyncio
import random
from urllib.parse import quote_plus
from fake_useragent import UserAgent
from crawl4ai import AsyncWebCrawler
import re
import time
from typing import Dict, List, Optional
from localization import GoogleLocalization
from serp_analyzer import SERPAnalyzer

class RankTracker:
    def __init__(self):
        self.ua = UserAgent()
        self.crawler = None
        self.rate_limit_delay = 10  # secondi tra requests - conservativo per evitare CAPTCHA
        self.localizer = GoogleLocalization()
        self.serp_analyzer = SERPAnalyzer()
        
    async def init_crawler(self):
        if not self.crawler:
            # Browser mode avanzato per evitare detection
            self.crawler = AsyncWebCrawler(
                browser_type="chromium",
                headless=True,
                verbose=False,
                # Configurazione browser realistica
                viewport_width=1920,
                viewport_height=1080,
                # Simula comportamento umano
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                # Anti-detection features
                accept_downloads=False,
                override_navigator=True,
                mask_fingerprint=True,
                simulate_user=True,
                magic=True  # Attiva tutte le feature anti-detection
            )
            print("🌐 Browser mode inizializzato con anti-detection")
    
    async def close_crawler(self):
        if self.crawler:
            try:
                await self.crawler.aclose()
            except AttributeError:
                # Versioni più recenti usano close() o non richiedono chiusura esplicita
                try:
                    await self.crawler.close()
                except:
                    pass
            self.crawler = None
    
    def build_google_url(self, keyword: str, localization_config: Dict) -> str:
        """Usa il nuovo sistema di localizzazione"""
        return self.localizer.build_google_url(
            keyword=keyword,
            country_code=localization_config.get('country_code', 'IT'),
            language_code=localization_config.get('language_code', 'it'),
            city_code=localization_config.get('city_code'),
            content_restriction=localization_config.get('content_restriction', True)
        )
    
    
    async def search_keyword_complete(self, keyword: str, domain: str, localization_config: Dict, 
                                    tracking_config: Dict = None) -> Dict:
        """Cerca una keyword e restituisce analisi completa SERP"""
        try:
            await self.init_crawler()
            
            url = self.build_google_url(keyword, localization_config)
            
            # Headers realistici per evitare detection
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            # Crawl della SERP con comportamento umano
            try:
                # Simula navigazione umana
                result = await self.crawler.arun(
                    url=url,
                    headers=headers,
                    wait_for="body",
                    delay_before_return_html=3,  # Più tempo per caricamento completo
                    # Comportamenti umani
                    page_timeout=30000,  # 30 secondi timeout
                    magic=True,  # Anti-detection avanzato
                    # Simula scroll per caricare contenuto lazy
                    js_code=[
                        "window.scrollTo(0, document.body.scrollHeight/3);",
                        "await new Promise(resolve => setTimeout(resolve, 1000));",
                        "window.scrollTo(0, document.body.scrollHeight/2);", 
                        "await new Promise(resolve => setTimeout(resolve, 1000));",
                        "window.scrollTo(0, 0);"
                    ]
                )
            except Exception as e:
                # Fallback senza comportamenti avanzati
                try:
                    result = await self.crawler.arun(
                        url=url, 
                        headers=headers,
                        wait_for="body",
                        delay_before_return_html=2
                    )
                except Exception as e2:
                    print(f"❌ Crawling fallito: {e}, {e2}")
                    return {'error': f"Crawling failed: {e2}"}
            
            if not result.success:
                return {'error': f"Crawling failed: {result.error_message}"}
            
            # Analisi completa SERP
            serp_analysis = self.serp_analyzer.analyze_complete_serp(result.html, domain)
            
            # Filtra risultati in base alla configurazione di tracking
            if tracking_config:
                serp_analysis = self._filter_by_tracking_config(serp_analysis, tracking_config)
            
            # Aggiungi metadata
            serp_analysis['metadata'] = {
                'keyword': keyword,
                'url': url,
                'crawl_time': time.time(),
                'tracking_config': tracking_config or {}
            }
            
            # Rate limiting aggressivo per evitare CAPTCHA
            delay = self.rate_limit_delay + random.uniform(2, 8)
            print(f"⏱️ Pausa {delay:.1f}s per evitare rate limiting...")
            await asyncio.sleep(delay)
            
            return serp_analysis
            
        except Exception as e:
            print(f"Errore durante ricerca completa '{keyword}': {str(e)}")
            return {'error': str(e)}
    
    def _filter_by_tracking_config(self, serp_analysis: Dict, tracking_config: Dict) -> Dict:
        """Filtra risultati SERP in base alla configurazione di tracking"""
        tracking_mode = tracking_config.get('tracking_mode', 'ORGANIC_ONLY')
        
        if tracking_mode == 'ORGANIC_ONLY':
            # Mantieni solo organici
            return {
                'organic': serp_analysis.get('organic', []),
                'target_positions': {
                    k: v for k, v in serp_analysis.get('target_positions', {}).items() 
                    if k == 'organic'
                }
            }
        elif tracking_mode == 'FULL_SERP':
            # Mantieni tutto
            return serp_analysis
        else:  # CUSTOM
            # Filtra in base alle impostazioni specifiche
            filtered = {}
            
            # Organici sempre inclusi
            filtered['organic'] = serp_analysis.get('organic', [])
            
            # Ads se abilitati
            if tracking_config.get('track_ads', False):
                filtered['ads'] = serp_analysis.get('ads', [])
            
            # Featured snippets se abilitati
            if tracking_config.get('track_snippets', False):
                filtered['featured_snippets'] = serp_analysis.get('featured_snippets', [])
            
            # Local pack se abilitato
            if tracking_config.get('track_local', False):
                filtered['local_pack'] = serp_analysis.get('local_pack', [])
            
            # Shopping se abilitato
            if tracking_config.get('track_shopping', False):
                filtered['shopping'] = serp_analysis.get('shopping', [])
            
            # Filtra target positions
            filtered['target_positions'] = {
                k: v for k, v in serp_analysis.get('target_positions', {}).items()
                if k in filtered
            }
            
            return filtered
    
    
    async def check_rankings_complete(self, domain: str, keywords: List[str], 
                                     localization_config: Dict, tracking_config: Dict) -> Dict:
        """Controlla il ranking per multiple keywords con analisi completa SERP"""
        results = {}
        
        # Pulisci il dominio per il matching
        clean_domain = self._clean_domain_for_search(domain)
        
        # Crea descrizione localizzazione per log
        loc_info = f"{localization_config.get('country_code', 'IT')}"
        if localization_config.get('city_code'):
            loc_info += f"/{localization_config['city_code']}"
        if localization_config.get('content_restriction'):
            loc_info += "/CR"
            
        print(f"🎯 Inizio check ranking MODERNO per {len(keywords)} keywords su dominio {clean_domain}")
        print(f"📍 Localizzazione: {loc_info}")
        print(f"📊 Tracking mode: {tracking_config.get('tracking_mode', 'ORGANIC_ONLY')}")
        
        # Processa in batch per evitare sovraccarico
        batch_size = 5  # Ridotto perché il nuovo metodo è più complesso
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i+batch_size]
            
            print(f"\n📦 Elaborando batch {i//batch_size + 1}/{(len(keywords)-1)//batch_size + 1}")
            
            # Processa batch sequenzialmente per evitare rate limiting
            for keyword in batch:
                try:
                    result = await self.search_keyword_complete(
                        keyword=keyword,
                        domain=clean_domain,
                        localization_config=localization_config,
                        tracking_config=tracking_config
                    )
                    
                    results[keyword] = result
                    
                    # Log risultato
                    if 'error' in result:
                        print(f"❌ {keyword}: {result['error']}")
                    else:
                        # Estrai posizione organica per il log
                        target_positions = result.get('target_positions', {})
                        organic_pos = target_positions.get('organic', {}).get('position')
                        
                        if organic_pos:
                            print(f"✅ {keyword}: posizione organica {organic_pos}")
                            
                            # Log altre posizioni se presenti
                            other_positions = []
                            for result_type, pos_info in target_positions.items():
                                if result_type != 'organic':
                                    other_positions.append(f"{result_type}: {pos_info.get('position')}")
                            
                            if other_positions:
                                print(f"   📊 Altri: {', '.join(other_positions)}")
                        else:
                            print(f"❌ {keyword}: non trovato nei risultati organici")
                            
                            # Controlla se è presente in ads/local/snippets
                            found_elsewhere = []
                            for result_type, pos_info in target_positions.items():
                                found_elsewhere.append(f"{result_type}: {pos_info.get('position')}")
                            
                            if found_elsewhere:
                                print(f"   📍 Trovato in: {', '.join(found_elsewhere)}")
                
                except Exception as e:
                    print(f"❌ Errore per keyword '{keyword}': {str(e)}")
                    results[keyword] = {'error': str(e)}
            
            # Pausa tra batch per evitare rate limiting
            if i + batch_size < len(keywords):
                delay = 15 + random.uniform(5, 15)
                print(f"⏱️ Pausa {delay:.1f}s prima del prossimo batch...")
                await asyncio.sleep(delay)
        
        await self.close_crawler()
        print(f"\n🏁 Check completato per {len(keywords)} keywords!")
        return results
    
    def _clean_domain_for_search(self, domain: str) -> str:
        """Pulisce il dominio dal database per la ricerca"""
        if not domain:
            return domain
        
        # Rimuovi protocollo
        clean = domain.replace('https://', '').replace('http://', '')
        # Rimuovi slash finale
        clean = clean.rstrip('/')
        # Rimuovi www se presente
        if clean.startswith('www.'):
            clean = clean[4:]
        
        return clean