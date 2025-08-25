#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

def debug_firstname_validation():
    print("DEBUGGING FIRST NAME VALIDATION")
    print("=" * 35)
    
    from apps.users.models import validate_first_name
    from django.core.exceptions import ValidationError
    
    test_names = ['Admin', 'John', 'Mary', 'Test']
    
    for name in test_names:
        try:
            validate_first_name(name)
            print(f"'{name}': VALID")
        except ValidationError as e:
            print(f"'{name}': INVALID - {e}")

if __name__ == "__main__":
    debug_firstname_validation()