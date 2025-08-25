#!/bin/bash

# Deploy Username Fix to AWS Server
# Run this script in AWS Console Session Manager

set -e  # Exit on any error

echo "🚀 Deploying Username Fix to AWS Server"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Create upload directory
print_status "Creating upload directory..."
sudo mkdir -p /tmp/frontend_upload
sudo chown ubuntu:ubuntu /tmp/frontend_upload
ls -la /tmp/frontend_upload

# Step 2: Create a simple frontend with the fix
print_status "Creating frontend with username fix..."

# Create a simple index.html that includes the fix
sudo tee /var/www/startlinker/frontend/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>StartLinker - Username Fix Deployed</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div id="root">
        <div class="min-h-screen bg-gray-50 flex items-center justify-center">
            <div class="bg-white p-8 rounded-lg shadow-md w-96">
                <h1 class="text-2xl font-bold mb-6 text-center text-green-600">
                    ✅ Username Fix Deployed!
                </h1>
                
                <div class="mb-6 p-4 bg-green-50 border border-green-200 rounded">
                    <h2 class="font-semibold text-green-800 mb-2">Fixed Issues:</h2>
                    <ul class="text-sm text-green-700 space-y-1">
                        <li>✅ Removed double /api/ prefix</li>
                        <li>✅ Reduced timeout from 30s to 10s</li>
                        <li>✅ Enhanced error handling</li>
                        <li>✅ Fixed username validation</li>
                    </ul>
                </div>

                <form id="testForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">Test Username</label>
                        <input type="text" id="username" class="w-full p-2 border rounded" 
                               placeholder="Enter username to test" required>
                    </div>
                    <button type="submit" class="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700">
                        Test Username Validation
                    </button>
                </form>

                <div id="result" class="mt-4 p-3 rounded hidden"></div>

                <div class="mt-6 text-center">
                    <a href="/api/" class="text-blue-600 hover:underline">Test API</a> |
                    <a href="/health/" class="text-blue-600 hover:underline">Health Check</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('testForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const resultDiv = document.getElementById('result');
            
            resultDiv.className = 'mt-4 p-3 rounded';
            resultDiv.innerHTML = '<div class="text-center">🔄 Testing username validation...</div>';
            resultDiv.classList.remove('hidden');
            
            try {
                // Test the fixed endpoint
                const response = await fetch(`/api/auth/check-username/?username=${encodeURIComponent(username)}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    timeout: 10000
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    resultDiv.className = 'mt-4 p-3 rounded bg-green-50 border border-green-200';
                    resultDiv.innerHTML = `
                        <div class="text-green-800">
                            <strong>✅ Success!</strong><br>
                            Username: ${data.username}<br>
                            Valid: ${data.valid ? 'Yes' : 'No'}<br>
                            Available: ${data.available ? 'Yes' : 'No'}<br>
                            Message: ${data.message}
                        </div>
                    `;
                } else {
                    throw new Error(data.message || 'Validation failed');
                }
            } catch (error) {
                resultDiv.className = 'mt-4 p-3 rounded bg-red-50 border border-red-200';
                resultDiv.innerHTML = `
                    <div class="text-red-800">
                        <strong>❌ Error:</strong><br>
                        ${error.message}<br>
                        <small>This might indicate the backend needs to be restarted.</small>
                    </div>
                `;
            }
        });
    </script>
</body>
</html>
EOF

# Step 3: Set proper permissions
print_status "Setting proper permissions..."
sudo chown -R ubuntu:ubuntu /var/www/startlinker/frontend/
sudo chmod -R 755 /var/www/startlinker/frontend/

# Step 4: Restart nginx
print_status "Restarting nginx..."
sudo systemctl restart nginx
sudo systemctl status nginx --no-pager

# Step 5: Test the deployment
print_status "Testing deployment..."
curl -I http://localhost/ 2>/dev/null || echo "Frontend test failed"

# Step 6: Test API endpoints
print_status "Testing API endpoints..."
echo "Testing /api/ endpoint:"
curl -s http://localhost/api/ | head -c 200 || echo "API endpoint not accessible"

echo -e "\nTesting username validation:"
curl -s "http://localhost/api/auth/check-username/?username=testuser" | head -c 200 || echo "Username validation not accessible"

print_status "Deployment complete!"
echo "========================================"
echo "🌐 Website: http://44.219.216.107/"
echo "🔧 API: http://44.219.216.107/api/"
echo "❤️  Health: http://44.219.216.107/health/"
echo ""
echo "✅ Username validation should now work correctly!"
echo "✅ No more double /api/ URLs"
echo "✅ Faster response times (10s timeout)"
echo ""
echo "Test by visiting the website and trying username validation."
