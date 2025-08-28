"""
Quick fix for authentication issues
Add this to your Render environment variables temporarily
"""

print("Quick Fix for Authentication Issues")
print("=" * 50)

print("\n1. Add these environment variables to Render backend service:")
print("   CORS_DEBUG=true")
print("   FRONTEND_URL=https://startlinker-frontend.onrender.com")

print("\n2. Ensure these are also set:")
print("   SENDGRID_API_KEY=your_sendgrid_api_key")
print("   DEFAULT_FROM_EMAIL=noreply@startlinker.com")

print("\n3. After adding CORS_DEBUG=true, your CORS will be permissive")
print("   This should fix the 403 errors temporarily")

print("\n4. The 500 error in send-verification should be fixed with better error handling")

print("\n5. Check Render logs after deploying to see exact error messages")

print("\n6. Test endpoints after deployment:")
print("   - https://startlinker-backend.onrender.com/api/users/debug/email-config/")
print("   - https://startlinker-backend.onrender.com/api/users/debug/email-ui/")

print("\nTo deploy fixes:")
print("git add .")
print('git commit -m "Fix auth errors and add debugging"')
print("git push origin main")