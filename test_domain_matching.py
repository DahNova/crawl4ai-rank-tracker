#!/usr/bin/env python3
"""
Test del metodo di matching dei domini
"""

from serp_analyzer import SERPAnalyzer

def test_domain_matching():
    """Test dei casi di matching dei domini"""
    print("🧪 TEST DOMAIN MATCHING")
    print("="*40)
    
    analyzer = SERPAnalyzer()
    
    test_cases = [
        # (target_domain, result_domain, expected_match)
        ("isacco.it", "isacco.it", True),
        ("isacco.it", "www.isacco.it", True),
        ("isacco.it", "blog.isacco.it", True),
        ("isacco.it", "shop.isacco.it", True),
        ("isacco.it", "worklinediviseisacco.it", False),  # Questo NON dovrebbe fare match
        ("isacco.it", "diviseisacco.it", False),          # Questo NON dovrebbe fare match
        ("example.com", "shop.example.com", True),
        ("example.com", "www.example.com", True),
        ("example.com", "notexample.com", False),
        ("amazon.it", "amazon.it", True),
        ("amazon.it", "www.amazon.it", True),
        ("amazon.it", "affiliate.amazon.it", True),
        ("google.com", "maps.google.com", True),
        ("google.com", "mygoogle.com", False),
    ]
    
    all_passed = True
    
    for target, result, expected in test_cases:
        actual = analyzer._domains_match(target, result)
        status = "✅" if actual == expected else "❌"
        
        if actual != expected:
            all_passed = False
        
        print(f"{status} '{target}' vs '{result}' -> {actual} (expected: {expected})")
    
    print(f"\n{'🎉 TUTTI I TEST PASSATI!' if all_passed else '❌ ALCUNI TEST FALLITI'}")
    
    # Test specifico per isacco
    print(f"\n🎯 TEST SPECIFICI ISACCO:")
    print("-" * 30)
    
    isacco_tests = [
        "worklinediviseisacco.it",
        "blog.worklinediviseisacco.it", 
        "diviseisacco.it",
        "isaccodivise.it",
        "blog.isacco.it",
        "www.isacco.it",
        "isacco.it"
    ]
    
    for domain in isacco_tests:
        match = analyzer._domains_match("isacco.it", domain)
        status = "✅ MATCH" if match else "❌ NO MATCH"
        print(f"{status} isacco.it vs {domain}")

if __name__ == "__main__":
    test_domain_matching()