"""
Modulo per analisi completa SERP con tutti i tipi di risultati
"""

import re
from typing import Dict, List, Optional, Tuple

class SERPAnalyzer:
    """Analizzatore completo per tutti i tipi di risultati SERP"""
    
    def __init__(self):
        pass
    
    def analyze_complete_serp(self, html: str, target_domain: str = None) -> Dict:
        """Analizza completamente una SERP per tutti i tipi di risultati"""
        results = {
            'organic': [],
            'ads': [],
            'featured_snippets': [],
            'local_pack': [],
            'shopping': [],
            'target_positions': {}
        }
        
        # Analizza ogni tipo di risultato
        results['organic'] = self._extract_organic_results(html)
        results['ads'] = self._extract_ads(html)
        results['featured_snippets'] = self._extract_featured_snippets(html)
        results['local_pack'] = self._extract_local_pack(html)
        results['shopping'] = self._extract_shopping_results(html)
        
        # Se specificato, trova le posizioni del dominio target
        if target_domain:
            results['target_positions'] = self._find_target_positions(results, target_domain)
        
        return results
    
    def _extract_organic_results(self, html: str) -> List[Dict]:
        """Estrae risultati organici ordinati per posizione"""
        organic_results = []
        
        # Pattern migliorati per risultati organici
        patterns = [
            # Pattern principale per cite (più affidabile per ordine)
            r'<cite[^>]*class="[^"]*"[^>]*>(?:https?://)?([^<\s]+)',
            # Pattern backup per div container organici
            r'<div[^>]*class="[^"]*\bg[^"]*"[^>]*>.*?<a[^>]*href="https?://([^/"]+)',
            # Pattern per h3 link
            r'<h3[^>]*><a[^>]*href="https?://([^/"]+)',
        ]
        
        # Trova tutti i domini organici in ordine
        organic_domains = []
        organic_details = {}
        
        for pattern in patterns:
            if 'cite' in pattern:
                # Per cite, cattura anche URL completa e titolo
                cite_matches = re.findall(
                    pattern, 
                    html, re.IGNORECASE | re.DOTALL
                )
                
                for match in cite_matches:
                    domain = self._clean_domain(match)
                    if domain and self._is_valid_organic_domain(domain) and domain not in organic_domains:
                        organic_domains.append(domain)
                        
                        # Cerca contesto per URL e titolo
                        context = self._find_result_context(html, domain)
                        organic_details[domain] = context
            else:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    domain = self._clean_domain(match)
                    if domain and self._is_valid_organic_domain(domain) and domain not in organic_domains:
                        organic_domains.append(domain)
                        organic_details[domain] = self._find_result_context(html, domain)
            
            if organic_domains:  # Se troviamo risultati, usiamo questi
                break
        
        # Crea lista organica con posizioni
        for i, domain in enumerate(organic_domains, 1):
            details = organic_details.get(domain, {})
            organic_results.append({
                'position': i,
                'domain': domain,
                'url': details.get('url', f'https://{domain}'),
                'title': details.get('title', ''),
                'snippet': details.get('snippet', ''),
                'result_type': 'organic'
            })
        
        return organic_results
    
    def _extract_ads(self, html: str) -> List[Dict]:
        """Estrae annunci sponsorizzati"""
        ads_results = []
        
        # Pattern per identificare ads
        ads_patterns = [
            # Contenitori ads comuni
            r'<div[^>]*class="[^"]*(?:ads|uEierd|mnr-c|v0rgu|pla-unit)[^"]*"[^>]*>.*?href="([^"]*)"[^>]*>.*?([^<]+)</a>',
            # Testo sponsorizzato
            r'<span[^>]*(?:sponsorizzato|sponsored|annuncio)[^>]*>.*?href="([^"]*)"[^>]*>.*?([^<]+)</a>',
            # Data-text-ad
            r'<div[^>]*data-text-ad[^>]*>.*?href="([^"]*)"[^>]*>.*?([^<]+)</a>',
        ]
        
        position = 1
        found_urls = set()
        
        for pattern in ads_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for url, title in matches:
                if url not in found_urls:
                    domain = self._extract_domain_from_url(url)
                    if domain:
                        ads_results.append({
                            'position': position,
                            'domain': domain,
                            'url': url,
                            'title': self._clean_text(title),
                            'snippet': '',
                            'result_type': 'ads'
                        })
                        found_urls.add(url)
                        position += 1
        
        return ads_results
    
    def _extract_featured_snippets(self, html: str) -> List[Dict]:
        """Estrae featured snippets e knowledge panels"""
        snippets = []
        
        # Pattern per featured snippets
        snippet_patterns = [
            # Knowledge panel
            r'<div[^>]*class="[^"]*(?:kno-rdesc|IZ6rdc|xpdopen|g9WsWb)[^"]*"[^>]*>.*?(?:https?://)?([^/\s<>"]+\.[a-z]{2,})',
            # Featured snippet standard
            r'<div[^>]*data-attrid="[^"]*"[^>]*>.*?<cite[^>]*>(?:https?://)?([^/<\s]+)',
            # Answer box
            r'<div[^>]*class="[^"]*(?:Z0LcW|XcVN5d)[^"]*"[^>]*>.*?([^/\s<>"]+\.[a-z]{2,})',
        ]
        
        found_domains = set()
        
        for pattern in snippet_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                domain = self._clean_domain(match)
                if domain and domain not in found_domains:
                    context = self._find_result_context(html, domain)
                    snippets.append({
                        'position': 0,  # Featured snippets sono posizione 0
                        'domain': domain,
                        'url': context.get('url', f'https://{domain}'),
                        'title': context.get('title', ''),
                        'snippet': context.get('snippet', ''),
                        'result_type': 'featured_snippet'
                    })
                    found_domains.add(domain)
        
        return snippets
    
    def _extract_local_pack(self, html: str) -> List[Dict]:
        """Estrae risultati del local pack / Google Maps"""
        local_results = []
        
        # Pattern per local pack
        local_patterns = [
            r'<div[^>]*class="[^"]*(?:rllt__details|VkpGBb|dbg0pd)[^"]*"[^>]*>.*?(?:https?://)?([^/\s<>"]+\.[a-z]{2,})',
            r'<div[^>]*data-local-attribute[^>]*>.*?<cite[^>]*>(?:https?://)?([^/<\s]+)',
        ]
        
        position = 1
        found_domains = set()
        
        for pattern in local_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                domain = self._clean_domain(match)
                if domain and domain not in found_domains:
                    context = self._find_result_context(html, domain)
                    local_results.append({
                        'position': position,
                        'domain': domain,
                        'url': context.get('url', f'https://{domain}'),
                        'title': context.get('title', ''),
                        'snippet': context.get('snippet', ''),
                        'result_type': 'local_pack'
                    })
                    found_domains.add(domain)
                    position += 1
        
        return local_results
    
    def _extract_shopping_results(self, html: str) -> List[Dict]:
        """Estrae risultati shopping"""
        shopping_results = []
        
        # Pattern per shopping results
        shopping_patterns = [
            r'<div[^>]*class="[^"]*(?:pla-unit|sh-dlr)[^"]*"[^>]*>.*?href="([^"]*)"[^>]*>.*?([^<]+)</a>',
            r'<div[^>]*data-shopping[^>]*>.*?href="([^"]*)"[^>]*>.*?([^<]+)</a>',
        ]
        
        position = 1
        found_urls = set()
        
        for pattern in shopping_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for url, title in matches:
                if url not in found_urls:
                    domain = self._extract_domain_from_url(url)
                    if domain:
                        shopping_results.append({
                            'position': position,
                            'domain': domain,
                            'url': url,
                            'title': self._clean_text(title),
                            'snippet': '',
                            'result_type': 'shopping'
                        })
                        found_urls.add(url)
                        position += 1
        
        return shopping_results
    
    def _find_target_positions(self, results: Dict, target_domain: str) -> Dict:
        """Trova le posizioni del dominio target in tutti i tipi di risultati"""
        target_domain_clean = self._clean_domain(target_domain)
        positions = {}
        
        for result_type, result_list in results.items():
            if result_type == 'target_positions':
                continue
                
            for result in result_list:
                result_domain = result.get('domain', '')
                
                # Match preciso usando solo il metodo _domains_match
                if self._domains_match(target_domain_clean, result_domain):
                    positions[result_type] = {
                        'position': result['position'],
                        'url': result.get('url'),
                        'title': result.get('title')
                    }
                    break  # Prendi solo la prima occorrenza per tipo
        
        return positions
    
    def _domains_match(self, domain1: str, domain2: str) -> bool:
        """Verifica se due domini sono equivalenti (gestisce www, subdomini)"""
        if not domain1 or not domain2:
            return False
        
        # Pulisci entrambi i domini
        clean1 = domain1.lower().replace('www.', '').strip()
        clean2 = domain2.lower().replace('www.', '').strip()
        
        # Match esatto
        if clean1 == clean2:
            return True
        
        # Match root domain PRECISO (es. shop.example.com vs example.com)
        parts1 = clean1.split('.')
        parts2 = clean2.split('.')
        
        if len(parts1) >= 2 and len(parts2) >= 2:
            root1 = '.'.join(parts1[-2:])  # ultimi 2 parti (domain.tld)
            root2 = '.'.join(parts2[-2:])
            
            # Match solo se i root domain sono identici
            if root1 == root2:
                return True
        
        # Match subdominio solo se uno è sottodominio dell'altro
        # es. blog.isacco.it matches isacco.it, ma worklinediviseisacco.it NON matches isacco.it
        if clean1.endswith('.' + clean2):  # clean1 è subdomain di clean2
            return True
        if clean2.endswith('.' + clean1):  # clean2 è subdomain di clean1
            return True
        
        return False
    
    def _find_result_context(self, html: str, domain: str) -> Dict:
        """Trova contesto (URL, titolo, snippet) per un dominio"""
        context = {'url': '', 'title': '', 'snippet': ''}
        
        # Cerca URL completa
        url_pattern = rf'href="(https?://[^"]*{re.escape(domain)}[^"]*)"'
        url_match = re.search(url_pattern, html, re.IGNORECASE)
        if url_match:
            context['url'] = url_match.group(1)
        
        # Cerca titolo (di solito in h3 vicino al link)
        title_pattern = rf'<h3[^>]*>.*?<a[^>]*href="[^"]*{re.escape(domain)}[^"]*"[^>]*>([^<]+)</a>'
        title_match = re.search(title_pattern, html, re.IGNORECASE | re.DOTALL)
        if title_match:
            context['title'] = self._clean_text(title_match.group(1))
        
        return context
    
    def _clean_domain(self, domain_str: str) -> Optional[str]:
        """Pulisce e normalizza un dominio"""
        if not domain_str:
            return None
        
        domain = domain_str.lower().strip()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0].split('?')[0].split('#')[0]
        domain = re.sub(r'[^\w\.-]', '', domain)
        
        return domain if '.' in domain and len(domain) > 2 else None
    
    def _extract_domain_from_url(self, url: str) -> Optional[str]:
        """Estrae dominio da URL"""
        if not url:
            return None
        
        # Rimuovi protocollo
        domain = re.sub(r'^https?://', '', url.lower())
        # Rimuovi www
        domain = re.sub(r'^www\.', '', domain)
        # Prendi solo la parte del dominio
        domain = domain.split('/')[0].split('?')[0].split('#')[0]
        
        return domain if '.' in domain and len(domain) > 2 else None
    
    def _is_valid_organic_domain(self, domain: str) -> bool:
        """Verifica se un dominio è valido per risultati organici"""
        if not domain:
            return False
        
        # Escludi domini Google
        google_domains = ['google.', 'youtube.', 'maps.google', 'translate.google']
        if any(gd in domain for gd in google_domains):
            return False
        
        return '.' in domain and len(domain) > 2
    
    def _clean_text(self, text: str) -> str:
        """Pulisce testo da HTML e whitespace"""
        if not text:
            return ''
        
        # Rimuovi tag HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Normalizza whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()