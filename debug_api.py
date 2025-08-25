#!/usr/bin/env python
"""
Debug the API to see what's happening with validation.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

def debug_serializer_validation():
    """Debug why serializer validation isn't working in the live API"""
    print("DEBUGGING SERIALIZER VALIDATION")
    print("="*50)
    
    from apps.users.serializers import UserRegistrationSerializer
    from apps.users.models import validate_username, validate_first_name
    import importlib
    
    # Check if our modules are properly loaded
    print("1. Checking module loading:")
    print(f"   UserRegistrationSerializer location: {UserRegistrationSerializer.__module__}")
    print(f"   validate_username location: {validate_username.__module__}")
    
    # Reload modules to make sure we have the latest
    print("\n2. Reloading modules...")
    import apps.users.profanity_filter
    import apps.users.models  
    import apps.users.serializers
    importlib.reload(apps.users.profanity_filter)
    importlib.reload(apps.users.models)
    importlib.reload(apps.users.serializers)
    
    # Test validation functions directly
    print("\n3. Testing validation functions directly:")
    try:
        validate_username('nigga')
        print("   [CRITICAL] validate_username('nigga') did NOT raise error!")
    except Exception as e:
        print(f"   [OK] validate_username('nigga') raised: {e}")
    
    try:
        validate_first_name('nigga')
        print("   [CRITICAL] validate_first_name('nigga') did NOT raise error!")
    except Exception as e:
        print(f"   [OK] validate_first_name('nigga') raised: {e}")
    
    # Test serializer after reload
    print("\n4. Testing serializer after module reload:")
    from apps.users.serializers import UserRegistrationSerializer
    
    test_data = {
        'username': 'nigga',
        'email': 'debug@test.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123',
        'first_name': 'nigga',
        'last_name': 'test'
    }
    
    serializer = UserRegistrationSerializer(data=test_data)
    
    print(f"   Serializer is_valid(): {serializer.is_valid()}")
    if not serializer.is_valid():
        print(f"   Errors: {dict(serializer.errors)}")
    else:
        print("   [CRITICAL] Serializer validation passed - this is the problem!")
    
    # Check what validation methods are actually being called
    print("\n5. Checking serializer validation methods:")
    serializer_instance = UserRegistrationSerializer()
    
    # Check if our validation methods exist
    validation_methods = [
        'validate_username', 'validate_first_name', 'validate_last_name',
        'validate_email', 'validate_password'
    ]
    
    for method_name in validation_methods:
        if hasattr(serializer_instance, method_name):
            method = getattr(serializer_instance, method_name)
            print(f"   {method_name}: EXISTS - {method}")
        else:
            print(f"   {method_name}: MISSING!")

def test_with_debugged_view():
    """Test the view with debug output"""
    print("\n6. Testing view with debug:")
    
    from apps.users.views import UserRegistrationView
    from django.test import RequestFactory
    from django.http import QueryDict
    from io import StringIO
    import sys
    
    # Capture print output
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        factory = RequestFactory()
        
        # Create POST data
        post_data = {
            'username': 'nigga',
            'email': 'debugview@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'nigga',
            'last_name': 'test'
        }
        
        request = factory.post('/api/auth/register/', post_data, content_type='application/x-www-form-urlencoded')
        
        # Add the data attribute that DRF expects
        request.data = post_data
        
        view = UserRegistrationView()
        response = view.create(request)
        
        sys.stdout = old_stdout
        captured = captured_output.getvalue()
        
        print(f"   View response status: {response.status_code}")
        if captured:
            print(f"   Captured output: {captured}")
        
        if response.status_code == 201:
            print("   [CRITICAL] View allowed registration!")
        else:
            print("   [OK] View blocked registration")
            
    except Exception as e:
        sys.stdout = old_stdout
        print(f"   Error testing view: {e}")

if __name__ == "__main__":
    try:
        debug_serializer_validation()
        test_with_debugged_view()
        
        print("\n" + "="*50)
        print("DEBUG COMPLETE")
        print("Look for [CRITICAL] messages above to find the issue")
        
    except Exception as e:
        print(f"Debug failed with error: {e}")
        import traceback
        traceback.print_exc()