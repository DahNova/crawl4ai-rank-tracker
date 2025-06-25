#!/usr/bin/env python3
"""
Test script per verificare il parsing SERP corretto
"""

from rank_tracker import RankTracker
import asyncio

async def test_serp_parsing():
    tracker = RankTracker()
    
    # Leggi la SERP HTML di esempio
    try:
        with open('fullserpage.html', 'r', encoding='utf-8') as f:
            html = f.read()
        print("✓ SERP HTML caricata")
    except Exception as e:
        print(f"✗ Errore caricamento SERP: {e}")
        return
    
    # Test parsing con dominio isacco.it
    domain = "isacco.it"
    position = tracker.parse_serp_position(html, domain)
    
    print(f"\n=== Test Parsing SERP ===")
    print(f"Dominio: {domain}")
    print(f"Posizione trovata: {position}")
    
    if position == 1:
        print("✓ SUCCESSO: Posizione corretta identificata (dovrebbe essere 1)")
    else:
        print(f"✗ ERRORE: Posizione incorretta. Dovrebbe essere 1, trovata {position}")
    
    # Test per debug: mostra i primi risultati organici trovati
    print(f"\n=== Debug Info ===")
    print("Testando pattern di parsing...")
    
    import re
    organic_patterns = [
        r'<div[^>]*class="[^"]*(?:g|tF2Cxc|yuRUbf)[^"]*"[^>]*>.*?<a[^>]*href="https?://([^/"]+)(?:/[^"]*)?[^"]*>.*?<h3',
        r'<h3[^>]*class="[^"]*"[^>]*><a[^>]*href="https?://([^/"]+)(?:/[^"]*)?[^"]*>',
        r'<cite[^>]*class="[^"]*"[^>]*>(?:https?://)?([^/<\s]+)',
    ]
    
    for i, pattern in enumerate(organic_patterns, 1):
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        print(f"Pattern {i}: {len(matches)} matches")
        for j, match in enumerate(matches[:5], 1):
            clean_match = match.lower().replace('www.', '').strip()
            print(f"  {j}. {clean_match}")
        if matches:
            break

if __name__ == "__main__":
    asyncio.run(test_serp_parsing())