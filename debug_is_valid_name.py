#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

def debug_is_valid_name():
    print("DEBUGGING IS_VALID_NAME FUNCTION")
    print("=" * 35)
    
    from apps.users.profanity_filter import is_valid_name
    
    test_names = ['Admin', 'admin', 'John', 'Mary', 'Test', 'fuck', 'nigga']
    
    for name in test_names:
        is_valid, error_message = is_valid_name(name)
        print(f"'{name}': valid={is_valid}, error='{error_message}'")

if __name__ == "__main__":
    debug_is_valid_name()