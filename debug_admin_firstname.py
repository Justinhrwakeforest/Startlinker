#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

def debug_admin_firstname():
    print("DEBUGGING ADMIN AS FIRST NAME")
    print("=" * 35)
    
    from apps.users.profanity_filter import contains_offensive_word
    
    # Test different cases
    test_cases = ['admin', 'Admin', 'ADMIN', 'AdMiN']
    
    for case in test_cases:
        result = contains_offensive_word(case)
        print(f"contains_offensive_word('{case}'): {result}")
        if result[0]:
            print(f"  -> Blocked because of word: '{result[1]}'")

if __name__ == "__main__":
    debug_admin_firstname()