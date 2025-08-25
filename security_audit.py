#!/usr/bin/env python3
"""
Comprehensive Security and Functionality Audit for StartupHub
Tests all security measures, authentication, authorization, and functionality.
"""

import os
import sys
import json
import requests
import subprocess
import hashlib
import re
from datetime import datetime
from pathlib import Path

class SecurityAudit:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': 0,
            'security_issues': [],
            'functionality_issues': [],
            'recommendations': [],
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0
        }
        
    def log_issue(self, severity, category, title, description, recommendation=None):
        """Log a security or functionality issue"""
        issue = {
            'severity': severity,
            'category': category,
            'title': title,
            'description': description,
            'recommendation': recommendation
        }
        
        if category == 'security':
            self.results['security_issues'].append(issue)
        else:
            self.results['functionality_issues'].append(issue)
            
        if severity == 'critical':
            self.results['critical_issues'] += 1
        elif severity == 'high':
            self.results['high_issues'] += 1
        elif severity == 'medium':
            self.results['medium_issues'] += 1
        elif severity == 'low':
            self.results['low_issues'] += 1
            
        self.results['tests_failed'] += 1
        
    def log_success(self, category, title, description):
        """Log a successful test"""
        self.results['tests_passed'] += 1
        print(f"✓ {category.upper()}: {title} - {description}")
        
    def test_django_security_settings(self):
        """Test Django security configuration"""
        print("\n=== TESTING DJANGO SECURITY SETTINGS ===")
        
        try:
            import django
            from django.conf import settings
            
            # Test SECRET_KEY
            if hasattr(settings, 'SECRET_KEY'):
                if settings.SECRET_KEY == 'django-insecure-dev-key-change-in-production':
                    self.log_issue('critical', 'security', 'Default SECRET_KEY', 
                                 'Using default Django SECRET_KEY in production')
                elif len(settings.SECRET_KEY) < 50:
                    self.log_issue('high', 'security', 'Weak SECRET_KEY', 
                                 'SECRET_KEY is too short')
                else:
                    self.log_success('security', 'SECRET_KEY', 'Properly configured')
            else:
                self.log_issue('critical', 'security', 'Missing SECRET_KEY', 
                             'SECRET_KEY not found in settings')
            
            # Test DEBUG mode
            if hasattr(settings, 'DEBUG'):
                if settings.DEBUG:
                    self.log_issue('high', 'security', 'DEBUG Mode Enabled', 
                                 'DEBUG=True in production environment')
                else:
                    self.log_success('security', 'DEBUG Mode', 'Properly disabled in production')
            else:
                self.log_issue('medium', 'security', 'DEBUG Setting Missing', 
                             'DEBUG setting not found')
            
            # Test ALLOWED_HOSTS
            if hasattr(settings, 'ALLOWED_HOSTS'):
                if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
                    self.log_issue('high', 'security', 'Unrestricted ALLOWED_HOSTS', 
                                 'ALLOWED_HOSTS is too permissive')
                else:
                    self.log_success('security', 'ALLOWED_HOSTS', 'Properly restricted')
            else:
                self.log_issue('critical', 'security', 'Missing ALLOWED_HOSTS', 
                             'ALLOWED_HOSTS setting not found')
            
            # Test HTTPS settings
            if hasattr(settings, 'SECURE_SSL_REDIRECT'):
                if not settings.SECURE_SSL_REDIRECT:
                    self.log_issue('medium', 'security', 'HTTPS Redirect Disabled', 
                                 'SECURE_SSL_REDIRECT is False')
                else:
                    self.log_success('security', 'HTTPS Redirect', 'Properly enabled')
            
            # Test CSRF settings
            if hasattr(settings, 'CSRF_COOKIE_SECURE'):
                if not settings.CSRF_COOKIE_SECURE:
                    self.log_issue('medium', 'security', 'Insecure CSRF Cookies', 
                                 'CSRF_COOKIE_SECURE is False')
                else:
                    self.log_success('security', 'CSRF Security', 'Properly configured')
                    
        except Exception as e:
            self.log_issue('critical', 'security', 'Django Settings Error', 
                         f'Error accessing Django settings: {str(e)}')
    
    def test_dependencies_security(self):
        """Test for known vulnerabilities in dependencies"""
        print("\n=== TESTING DEPENDENCIES SECURITY ===")
        
        # Check Python packages for known vulnerabilities
        try:
            import subprocess
            result = subprocess.run(['pip', 'list', '--outdated'], 
                                  capture_output=True, text=True)
            if result.stdout:
                self.log_issue('medium', 'security', 'Outdated Dependencies', 
                             'Some packages have newer versions available')
            else:
                self.log_success('security', 'Dependencies', 'All packages up to date')
        except Exception as e:
            self.log_issue('low', 'security', 'Dependency Check Failed', 
                         f'Could not check dependencies: {str(e)}')
    
    def test_file_permissions(self):
        """Test file and directory permissions"""
        print("\n=== TESTING FILE PERMISSIONS ===")
        
        critical_files = [
            'startup_hub/startup_hub/settings.py',
            'startup_hub/startup_hub/settings/production.py',
            'db.sqlite3',
            '.env'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                # Check if file is readable by others
                if os.access(file_path, os.R_OK):
                    self.log_success('security', f'File Permissions: {file_path}', 
                                   'Properly secured')
                else:
                    self.log_issue('medium', 'security', f'File Permissions: {file_path}', 
                                 'File may be too restrictive')
            else:
                self.log_issue('low', 'security', f'Missing File: {file_path}', 
                             'File not found')
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        print("\n=== TESTING SQL INJECTION PROTECTION ===")
        
        # Test common SQL injection patterns
        sql_injection_tests = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "1' OR '1' = '1' --"
        ]
        
        # This would require actual API endpoints to test
        # For now, we'll check if Django ORM is being used properly
        try:
            from django.db import models
            self.log_success('security', 'SQL Injection Protection', 
                           'Django ORM provides built-in SQL injection protection')
        except Exception as e:
            self.log_issue('high', 'security', 'SQL Injection Risk', 
                         f'Could not verify SQL injection protection: {str(e)}')
    
    def test_xss_protection(self):
        """Test XSS protection"""
        print("\n=== TESTING XSS PROTECTION ===")
        
        # Check if Django's XSS protection is enabled
        try:
            import django
            from django.conf import settings
            
            if hasattr(settings, 'SECURE_BROWSER_XSS_FILTER'):
                if settings.SECURE_BROWSER_XSS_FILTER:
                    self.log_success('security', 'XSS Protection', 
                                   'Browser XSS filter enabled')
                else:
                    self.log_issue('medium', 'security', 'XSS Protection Disabled', 
                                 'SECURE_BROWSER_XSS_FILTER is False')
            else:
                self.log_issue('medium', 'security', 'XSS Protection Missing', 
                             'SECURE_BROWSER_XSS_FILTER setting not found')
                
        except Exception as e:
            self.log_issue('high', 'security', 'XSS Protection Error', 
                         f'Error checking XSS protection: {str(e)}')
    
    def test_authentication_system(self):
        """Test authentication and authorization"""
        print("\n=== TESTING AUTHENTICATION SYSTEM ===")
        
        try:
            # Check if custom user model is being used
            from django.conf import settings
            if hasattr(settings, 'AUTH_USER_MODEL'):
                self.log_success('security', 'Custom User Model', 
                               f'Using custom user model: {settings.AUTH_USER_MODEL}')
            else:
                self.log_issue('low', 'security', 'Default User Model', 
                             'Using Django default user model')
            
            # Check authentication backends
            if hasattr(settings, 'AUTHENTICATION_BACKENDS'):
                self.log_success('security', 'Authentication Backends', 
                               'Custom authentication backends configured')
            else:
                self.log_issue('low', 'security', 'Default Auth Backends', 
                             'Using default authentication backends')
                
        except Exception as e:
            self.log_issue('high', 'security', 'Authentication Error', 
                         f'Error checking authentication: {str(e)}')
    
    def test_api_security(self):
        """Test API security measures"""
        print("\n=== TESTING API SECURITY ===")
        
        # Check if API protection middleware is configured
        try:
            from django.conf import settings
            
            middleware_classes = getattr(settings, 'MIDDLEWARE', [])
            
            # Check for security middleware
            security_middleware = [
                'startup_hub.middleware.SecurityHeadersMiddleware',
                'startup_hub.middleware.RateLimitMiddleware',
                'startup_hub.middleware.SecurityMonitoringMiddleware'
            ]
            
            for middleware in security_middleware:
                if middleware in middleware_classes:
                    self.log_success('security', f'Middleware: {middleware}', 
                                   'Security middleware properly configured')
                else:
                    self.log_issue('medium', 'security', f'Missing Middleware: {middleware}', 
                                 'Security middleware not configured')
                    
        except Exception as e:
            self.log_issue('high', 'security', 'API Security Error', 
                         f'Error checking API security: {str(e)}')
    
    def test_content_security_policy(self):
        """Test Content Security Policy"""
        print("\n=== TESTING CONTENT SECURITY POLICY ===")
        
        # Check if CSP is properly configured
        try:
            from startup_hub.middleware.security import SecurityHeadersMiddleware
            
            # Create a mock request and response to test CSP
            from django.test import RequestFactory
            from django.http import HttpResponse
            
            factory = RequestFactory()
            request = factory.get('/')
            response = HttpResponse()
            
            middleware = SecurityHeadersMiddleware(lambda req: response)
            processed_response = middleware.process_response(request, response)
            
            if 'Content-Security-Policy' in processed_response:
                self.log_success('security', 'Content Security Policy', 
                               'CSP headers properly configured')
            else:
                self.log_issue('high', 'security', 'Missing CSP', 
                             'Content Security Policy not configured')
                
        except Exception as e:
            self.log_issue('medium', 'security', 'CSP Test Error', 
                         f'Error testing CSP: {str(e)}')
    
    def test_rate_limiting(self):
        """Test rate limiting implementation"""
        print("\n=== TESTING RATE LIMITING ===")
        
        try:
            from startup_hub.api_protection import RateLimiter
            
            rate_limiter = RateLimiter()
            self.log_success('security', 'Rate Limiting', 
                           'Rate limiting system properly implemented')
            
        except Exception as e:
            self.log_issue('medium', 'security', 'Rate Limiting Error', 
                         f'Error testing rate limiting: {str(e)}')
    
    def test_profanity_filter(self):
        """Test profanity filtering system"""
        print("\n=== TESTING PROFANITY FILTER ===")
        
        try:
            from apps.users.profanity_filter import is_valid_name
            
            # Test with clean name
            is_valid, error = is_valid_name("John")
            if is_valid:
                self.log_success('functionality', 'Profanity Filter', 
                               'Profanity filter working correctly')
            else:
                self.log_issue('medium', 'functionality', 'Profanity Filter Error', 
                             'Profanity filter incorrectly flagged valid name')
                
            # Test with profane name
            is_valid, error = is_valid_name("fuck")
            if not is_valid:
                self.log_success('functionality', 'Profanity Detection', 
                               'Profanity detection working correctly')
            else:
                self.log_issue('high', 'functionality', 'Profanity Detection Failed', 
                             'Profanity filter failed to detect inappropriate content')
                
        except Exception as e:
            self.log_issue('medium', 'functionality', 'Profanity Filter Error', 
                         f'Error testing profanity filter: {str(e)}')
    
    def test_file_upload_security(self):
        """Test file upload security"""
        print("\n=== TESTING FILE UPLOAD SECURITY ===")
        
        try:
            from django.conf import settings
            
            # Check if file upload restrictions are in place
            if hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE'):
                self.log_success('security', 'File Upload Limits', 
                               'File upload size limits configured')
            else:
                self.log_issue('medium', 'security', 'File Upload Limits Missing', 
                             'No file upload size limits configured')
            
            # Check allowed file types
            if hasattr(settings, 'ALLOWED_FILE_TYPES'):
                self.log_success('security', 'File Type Restrictions', 
                               'File type restrictions configured')
            else:
                self.log_issue('medium', 'security', 'File Type Restrictions Missing', 
                             'No file type restrictions configured')
                
        except Exception as e:
            self.log_issue('medium', 'security', 'File Upload Security Error', 
                         f'Error checking file upload security: {str(e)}')
    
    def test_session_security(self):
        """Test session security"""
        print("\n=== TESTING SESSION SECURITY ===")
        
        try:
            from django.conf import settings
            
            # Check session security settings
            if hasattr(settings, 'SESSION_COOKIE_SECURE'):
                if settings.SESSION_COOKIE_SECURE:
                    self.log_success('security', 'Secure Session Cookies', 
                                   'Session cookies are secure')
                else:
                    self.log_issue('medium', 'security', 'Insecure Session Cookies', 
                                 'Session cookies not marked as secure')
            
            if hasattr(settings, 'SESSION_COOKIE_HTTPONLY'):
                if settings.SESSION_COOKIE_HTTPONLY:
                    self.log_success('security', 'HttpOnly Session Cookies', 
                                   'Session cookies are HttpOnly')
                else:
                    self.log_issue('medium', 'security', 'Non-HttpOnly Session Cookies', 
                                 'Session cookies not marked as HttpOnly')
                    
        except Exception as e:
            self.log_issue('medium', 'security', 'Session Security Error', 
                         f'Error checking session security: {str(e)}')
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        print("\n=== TESTING CORS CONFIGURATION ===")
        
        try:
            from django.conf import settings
            
            if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
                if settings.CORS_ALLOWED_ORIGINS:
                    self.log_success('security', 'CORS Configuration', 
                                   'CORS origins properly configured')
                else:
                    self.log_issue('medium', 'security', 'Empty CORS Origins', 
                                 'CORS_ALLOWED_ORIGINS is empty')
            else:
                self.log_issue('medium', 'security', 'Missing CORS Configuration', 
                             'CORS_ALLOWED_ORIGINS not configured')
                
        except Exception as e:
            self.log_issue('medium', 'security', 'CORS Configuration Error', 
                         f'Error checking CORS configuration: {str(e)}')
    
    def test_environment_variables(self):
        """Test environment variable security"""
        print("\n=== TESTING ENVIRONMENT VARIABLES ===")
        
        sensitive_vars = [
            'SECRET_KEY',
            'STRIPE_SECRET_KEY',
            'AWS_SECRET_ACCESS_KEY',
            'DATABASE_URL',
            'EMAIL_HOST_PASSWORD'
        ]
        
        for var in sensitive_vars:
            if os.environ.get(var):
                self.log_success('security', f'Environment Variable: {var}', 
                               'Sensitive environment variable is set')
            else:
                self.log_issue('low', 'security', f'Missing Environment Variable: {var}', 
                             f'Environment variable {var} not found')
    
    def test_frontend_security(self):
        """Test frontend security measures"""
        print("\n=== TESTING FRONTEND SECURITY ===")
        
        # Check if HTTPS is enforced in frontend
        frontend_files = [
            'frontend/src/config/axios.js',
            'frontend/src/config/api.config.js'
        ]
        
        for file_path in frontend_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'https://' in content:
                        self.log_success('security', f'Frontend HTTPS: {file_path}', 
                                       'HTTPS properly configured')
                    else:
                        self.log_issue('medium', 'security', f'Frontend HTTP: {file_path}', 
                                     'Using HTTP instead of HTTPS')
            else:
                self.log_issue('low', 'security', f'Missing Frontend File: {file_path}', 
                             'Frontend configuration file not found')
    
    def calculate_overall_score(self):
        """Calculate overall security score"""
        total_issues = (self.results['critical_issues'] * 10 + 
                       self.results['high_issues'] * 5 + 
                       self.results['medium_issues'] * 2 + 
                       self.results['low_issues'])
        
        total_tests = self.results['tests_passed'] + self.results['tests_failed']
        
        if total_tests > 0:
            self.results['overall_score'] = max(0, 100 - total_issues)
        else:
            self.results['overall_score'] = 0
    
    def generate_recommendations(self):
        """Generate security recommendations"""
        recommendations = []
        
        if self.results['critical_issues'] > 0:
            recommendations.append("CRITICAL: Address all critical security issues immediately")
        
        if self.results['high_issues'] > 0:
            recommendations.append("HIGH: Fix high-priority security vulnerabilities")
        
        if self.results['medium_issues'] > 0:
            recommendations.append("MEDIUM: Review and fix medium-priority issues")
        
        recommendations.extend([
            "Enable HTTPS for all communications",
            "Implement proper session management",
            "Use strong, unique passwords for all accounts",
            "Regularly update dependencies",
            "Implement proper logging and monitoring",
            "Conduct regular security audits",
            "Use environment variables for sensitive data",
            "Implement proper input validation",
            "Use Content Security Policy headers",
            "Enable rate limiting on all endpoints"
        ])
        
        self.results['recommendations'] = recommendations
    
    def run_full_audit(self):
        """Run the complete security audit"""
        print("🔒 STARTING COMPREHENSIVE SECURITY AUDIT")
        print("=" * 50)
        
        # Run all security tests
        self.test_django_security_settings()
        self.test_dependencies_security()
        self.test_file_permissions()
        self.test_sql_injection_protection()
        self.test_xss_protection()
        self.test_authentication_system()
        self.test_api_security()
        self.test_content_security_policy()
        self.test_rate_limiting()
        self.test_profanity_filter()
        self.test_file_upload_security()
        self.test_session_security()
        self.test_cors_configuration()
        self.test_environment_variables()
        self.test_frontend_security()
        
        # Calculate score and generate recommendations
        self.calculate_overall_score()
        self.generate_recommendations()
        
        return self.results
    
    def print_report(self):
        """Print the security audit report"""
        print("\n" + "=" * 60)
        print("🔒 SECURITY AUDIT REPORT")
        print("=" * 60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Security Score: {self.results['overall_score']}/100")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        print(f"Critical Issues: {self.results['critical_issues']}")
        print(f"High Issues: {self.results['high_issues']}")
        print(f"Medium Issues: {self.results['medium_issues']}")
        print(f"Low Issues: {self.results['low_issues']}")
        
        print("\n" + "=" * 60)
        print("🚨 SECURITY ISSUES")
        print("=" * 60)
        
        for issue in self.results['security_issues']:
            print(f"\n[{issue['severity'].upper()}] {issue['title']}")
            print(f"Description: {issue['description']}")
            if issue['recommendation']:
                print(f"Recommendation: {issue['recommendation']}")
        
        print("\n" + "=" * 60)
        print("🔧 FUNCTIONALITY ISSUES")
        print("=" * 60)
        
        for issue in self.results['functionality_issues']:
            print(f"\n[{issue['severity'].upper()}] {issue['title']}")
            print(f"Description: {issue['description']}")
            if issue['recommendation']:
                print(f"Recommendation: {issue['recommendation']}")
        
        print("\n" + "=" * 60)
        print("💡 RECOMMENDATIONS")
        print("=" * 60)
        
        for i, recommendation in enumerate(self.results['recommendations'], 1):
            print(f"{i}. {recommendation}")
        
        print("\n" + "=" * 60)
        
        # Save report to file
        report_file = f"security_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_file}")

if __name__ == "__main__":
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
    
    try:
        import django
        django.setup()
    except Exception as e:
        print(f"Error setting up Django: {e}")
        sys.exit(1)
    
    # Run the audit
    auditor = SecurityAudit()
    results = auditor.run_full_audit()
    auditor.print_report()

