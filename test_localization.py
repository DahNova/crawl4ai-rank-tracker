#!/usr/bin/env python3
"""
Test script per verificare la localizzazione
"""

from localization import GoogleLocalization

def test_localization():
    localizer = GoogleLocalization()
    
    # Test configurazioni diverse
    configs = [
        {
            'country_code': 'IT',
            'language_code': 'it',
            'city_code': None,
            'content_restriction': True
        },
        {
            'country_code': 'IT', 
            'language_code': 'it',
            'city_code': 'roma',
            'content_restriction': True
        }
    ]
    
    keyword = "divise isacco"
    
    for i, config in enumerate(configs, 1):
        print(f"\n=== Test {i} ===")
        print(f"Config: {config}")
        
        url = localizer.build_google_url(keyword, **config)
        print(f"URL: {url}")
        
        loc_config = localizer.get_localization_config(**config)
        print(f"Localizzazione: {loc_config}")

if __name__ == "__main__":
    test_localization()