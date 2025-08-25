/**
 * Quick Guide Button Fix
 * 
 * INSTRUCTIONS:
 * 1. Go to your startup page where the Guide button is
 * 2. Open browser Developer Tools (F12)
 * 3. Go to Console tab
 * 4. Copy and paste this entire script
 * 5. Press Enter
 * 6. Try clicking the Guide button
 */

(function() {
    console.log('🔧 Starting Guide Button Fix...');
    
    // Function to fix a single element
    function fixGuideElement(element) {
        console.log('📝 Fixing element:', element.tagName, element.textContent.substring(0, 30));
        
        // Remove all existing click handlers
        const newElement = element.cloneNode(true);
        element.parentNode.replaceChild(newElement, element);
        
        // Add new click handler
        newElement.addEventListener('click', function(e) {
            console.log('✅ Guide button clicked - redirecting to guide page');
            e.preventDefault();
            e.stopPropagation();
            
            // Try different approaches
            try {
                // First try: open in same tab
                window.location.href = '/api/startups/guide/';
            } catch (error) {
                console.log('⚠️ Same tab failed, trying new tab');
                try {
                    // Second try: open in new tab
                    window.open('/api/startups/guide/', '_blank');
                } catch (error2) {
                    console.log('❌ Both methods failed:', error2);
                    alert('Guide page URL: /api/startups/guide/\n\nPlease navigate there manually.');
                }
            }
            
            return false;
        });
        
        // If it's a link, also update the href
        if (newElement.tagName === 'A') {
            newElement.href = '/api/startups/guide/';
        }
        
        return newElement;
    }
    
    // Find and fix all Guide buttons
    let fixedCount = 0;
    
    // Method 1: Look for elements containing "Guide" text
    const allElements = document.querySelectorAll('*');
    allElements.forEach(element => {
        const text = element.textContent || element.innerText || '';
        
        if (text.toLowerCase().includes('guide') && 
            element.offsetHeight > 0 && 
            element.offsetWidth > 0 &&
            (element.tagName === 'BUTTON' || 
             element.tagName === 'A' || 
             element.onclick ||
             element.classList.contains('btn') ||
             element.classList.contains('button'))) {
            
            fixGuideElement(element);
            fixedCount++;
        }
    });
    
    // Method 2: Look for common button selectors
    const selectors = [
        'button[data-action*="guide"]',
        'a[href*="guide"]',
        '.guide-button',
        '.btn-guide',
        '[data-testid*="guide"]'
    ];
    
    selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            fixGuideElement(element);
            fixedCount++;
        });
    });
    
    // Method 3: React component detection
    try {
        const reactElements = document.querySelectorAll('[data-reactroot] *, [id*="react"] *');
        reactElements.forEach(element => {
            if (element.textContent && element.textContent.includes('Guide') && 
                (element.onclick || element.getAttribute('onClick'))) {
                fixGuideElement(element);
                fixedCount++;
            }
        });
    } catch (e) {
        console.log('React detection failed (this is normal if not using React)');
    }
    
    // Results
    if (fixedCount > 0) {
        console.log(`✅ Fixed ${fixedCount} Guide button(s)!`);
        console.log('Try clicking your Guide button now.');
        
        // Show visual confirmation
        const notification = document.createElement('div');
        notification.innerHTML = `
            <div style="position: fixed; top: 20px; right: 20px; background: #28a745; color: white; 
                        padding: 15px 20px; border-radius: 8px; z-index: 10000; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-family: Arial, sans-serif;">
                ✅ Fixed ${fixedCount} Guide button(s)!<br>
                <small>Click Guide button to test</small>
            </div>
        `;
        document.body.appendChild(notification);
        
        // Remove notification after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
    } else {
        console.log('❌ No Guide buttons found on this page.');
        console.log('Possible reasons:');
        console.log('1. The Guide button is in a different page');
        console.log('2. The button text is not exactly "Guide"');
        console.log('3. The button is dynamically loaded');
        
        // Show all clickable elements that might be the guide button
        console.log('\n🔍 All clickable elements on page:');
        const clickables = document.querySelectorAll('button, a, [onclick], .btn');
        clickables.forEach((el, index) => {
            console.log(`${index + 1}. <${el.tagName}> "${el.textContent?.substring(0, 50) || 'no text'}" 
                        href: ${el.href || 'none'} 
                        onclick: ${el.onclick ? 'yes' : 'no'}`);
        });
        
        // Try to find it anyway
        const possibleGuides = [];
        clickables.forEach(el => {
            const text = el.textContent || '';
            if (text.match(/guide|help|info|docs|documentation/i)) {
                possibleGuides.push(el);
            }
        });
        
        if (possibleGuides.length > 0) {
            console.log(`\n🤔 Found ${possibleGuides.length} possible Guide buttons:`);
            possibleGuides.forEach((el, index) => {
                console.log(`${index + 1}. "${el.textContent?.substring(0, 30)}"`);
                // Fix these too
                fixGuideElement(el);
            });
        }
    }
    
    // Test if guide endpoint is accessible
    console.log('\n🧪 Testing guide endpoint...');
    fetch('/api/startups/guide/')
        .then(response => {
            if (response.ok) {
                console.log('✅ Guide endpoint is working!');
                return response.json();
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        })
        .then(data => {
            console.log('📄 Guide data loaded:', data.title);
        })
        .catch(error => {
            console.log('❌ Guide endpoint error:', error);
            console.log('Check if Django server is running on the right port');
        });
    
    console.log('\n💡 If the fix doesn\'t work, try:');
    console.log('1. Refresh the page and run this script again');
    console.log('2. Navigate directly to: /api/startups/guide/');
    console.log('3. Check if you\'re on the right page (startup page)');
    
})();

// Export function for manual use
window.fixGuideButton = function() {
    console.log('Running manual Guide button fix...');
    // Re-run the script
    location.reload(); // Reload and run again
};