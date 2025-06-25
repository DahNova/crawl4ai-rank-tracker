"""
Sistema di localizzazione moderno per Google Search
Gestisce parametri GL, HL, UULE, CR per 2025
"""

import base64
from typing import Dict, Optional, List

class GoogleLocalization:
    # Mapping paesi con codici
    COUNTRIES = {
        'IT': {'name': 'Italia', 'gl': 'it', 'cr': 'countryIT'},
        'US': {'name': 'Stati Uniti', 'gl': 'us', 'cr': 'countryUS'},
        'DE': {'name': 'Germania', 'gl': 'de', 'cr': 'countryDE'},
        'FR': {'name': 'Francia', 'gl': 'fr', 'cr': 'countryFR'},
        'ES': {'name': 'Spagna', 'gl': 'es', 'cr': 'countryES'},
        'UK': {'name': 'Regno Unito', 'gl': 'uk', 'cr': 'countryUK'},
    }
    
    # Mapping lingue
    LANGUAGES = {
        'it': 'Italiano',
        'en': 'English', 
        'de': 'Deutsch',
        'fr': 'Français',
        'es': 'Español',
    }
    
    # Città italiane principali con codici UULE pre-generati
    ITALIAN_CITIES = {
        'roma': {
            'name': 'Roma',
            'canonical': 'Rome,Lazio,Italy',
            'uule': 'w+CAIQICIGUm9tZSxMYXppbyxJdGFseQ=='
        },
        'milano': {
            'name': 'Milano', 
            'canonical': 'Milan,Lombardy,Italy',
            'uule': 'w+CAIQICIHTWlsYW4sTG9tYmFyZHksaXRhbHk='
        },
        'napoli': {
            'name': 'Napoli',
            'canonical': 'Naples,Campania,Italy', 
            'uule': 'w+CAIQICIITmFwbGVzLENhbXBhbmlhLEl0YWx5'
        },
        'torino': {
            'name': 'Torino',
            'canonical': 'Turin,Piedmont,Italy',
            'uule': 'w+CAIQICIHVHVyaW4sUGllZG1vbnQsSXRhbHk='
        },
        'bologna': {
            'name': 'Bologna',
            'canonical': 'Bologna,Emilia-Romagna,Italy',
            'uule': 'w+CAIQICILQm9sb2duYSxFbWlsaWEtUm9tYWduYSxJdGFseQ=='
        },
        'firenze': {
            'name': 'Firenze',
            'canonical': 'Florence,Tuscany,Italy',
            'uule': 'w+CAIQICIJRmxvcmVuY2UsVHVzY2FueSwgSXRhbHk='
        },
        'genova': {
            'name': 'Genova',
            'canonical': 'Genoa,Liguria,Italy',
            'uule': 'w+CAIQICIHR2Vub2EsTGlndXJpYSxJdGFseQ=='
        },
        'palermo': {
            'name': 'Palermo',
            'canonical': 'Palermo,Sicily,Italy',
            'uule': 'w+CAIQICIJUGFsZXJtbyxTaWNpbHksaXRhbHk='
        }
    }
    
    def __init__(self):
        pass
    
    def generate_uule(self, canonical_name: str) -> str:
        """
        Genera codice UULE da nome canonico
        Formato corretto: w+CAIQICI + base64(canonical_name)
        """
        try:
            encoded = base64.b64encode(canonical_name.encode('utf-8')).decode('utf-8')
            return f"w+CAIQICI{encoded}"
        except Exception as e:
            print(f"Errore generazione UULE per '{canonical_name}': {e}")
            return ""
    
    def build_google_url(self, 
                        keyword: str,
                        country_code: str = 'IT',
                        language_code: str = 'it', 
                        city_code: Optional[str] = None,
                        content_restriction: bool = True) -> str:
        """
        Costruisce URL Google moderno con parametri 2025
        """
        from urllib.parse import quote_plus
        
        base_url = "https://www.google.com/search"
        encoded_keyword = quote_plus(keyword)
        
        # Parametri base
        params = [
            f"q={encoded_keyword}",
            f"gl={self.COUNTRIES[country_code]['gl']}",
            f"hl={language_code}",
            "num=100"
        ]
        
        # Content restriction se richiesto
        if content_restriction and country_code in self.COUNTRIES:
            params.append(f"cr={self.COUNTRIES[country_code]['cr']}")
        
        # UULE per localizzazione precisa
        if city_code and country_code == 'IT' and city_code in self.ITALIAN_CITIES:
            params.append(f"uule={self.ITALIAN_CITIES[city_code]['uule']}")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def get_localization_config(self,
                              country_code: str = 'IT',
                              language_code: str = 'it',
                              city_code: Optional[str] = None,
                              content_restriction: bool = True) -> Dict:
        """
        Restituisce configurazione completa di localizzazione
        """
        config = {
            'country_code': country_code,
            'country_name': self.COUNTRIES.get(country_code, {}).get('name', 'Unknown'),
            'language_code': language_code,
            'language_name': self.LANGUAGES.get(language_code, 'Unknown'),
            'content_restriction': content_restriction,
            'gl_param': self.COUNTRIES.get(country_code, {}).get('gl', 'it'),
            'cr_param': self.COUNTRIES.get(country_code, {}).get('cr', 'countryIT') if content_restriction else None
        }
        
        # Aggiungi info città se specificata
        if city_code and country_code == 'IT' and city_code in self.ITALIAN_CITIES:
            city_info = self.ITALIAN_CITIES[city_code]
            config.update({
                'city_code': city_code,
                'city_name': city_info['name'],
                'city_canonical': city_info['canonical'],
                'uule_param': city_info['uule']
            })
        
        return config
    
    def get_available_countries(self) -> List[Dict]:
        """Restituisce lista paesi disponibili"""
        return [
            {'code': code, 'name': info['name']} 
            for code, info in self.COUNTRIES.items()
        ]
    
    def get_available_languages(self) -> List[Dict]:
        """Restituisce lista lingue disponibili"""
        return [
            {'code': code, 'name': name}
            for code, name in self.LANGUAGES.items()
        ]
    
    def get_available_italian_cities(self) -> List[Dict]:
        """Restituisce lista città italiane disponibili"""
        return [
            {'code': code, 'name': info['name']}
            for code, info in self.ITALIAN_CITIES.items()
        ]