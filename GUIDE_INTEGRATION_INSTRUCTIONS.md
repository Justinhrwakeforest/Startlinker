# Guide Button Integration Instructions

## Problem
The Guide button on the startup page is redirecting to the home page instead of showing the startup guide.

## Solution
I've created a complete guide system with the following components:

### 1. Backend API Endpoint
- **URL**: `/api/startups/guide/`
- **Method**: GET
- **Response**: Returns the startup guide content in markdown format

### 2. Guide Content
- **File**: `STARTUP_SUBMISSION_GUIDE.md`
- **Location**: Project root directory
- **Content**: Comprehensive guide covering all startup-related features

### 3. Frontend Integration Script
- **File**: `static/js/startup-guide.js`
- **Purpose**: Handles the Guide button click and displays the guide in a modal

## How to Fix the Guide Button

### Option 1: Include the JavaScript File
Add this script to your HTML page where the Guide button appears:

```html
<script src="/static/js/startup-guide.js"></script>
```

The script will automatically:
- Find the Guide button on the page
- Attach a click handler
- Display the guide in a beautiful modal when clicked

### Option 2: Manual Integration (React/Vue/Angular)

If you're using a modern framework, you can call the API directly:

```javascript
// Fetch the guide
async function fetchGuide() {
    try {
        const response = await fetch('/api/startups/guide/');
        const data = await response.json();
        // Display data.content in your UI
        console.log(data.title); // "Startup Hub - Complete Startup Guide"
        console.log(data.content); // Markdown content
    } catch (error) {
        console.error('Failed to load guide:', error);
    }
}
```

### Option 3: Direct Link
Create a dedicated guide page that fetches and displays the content:

```html
<a href="/startups/guide" class="btn btn-secondary">
    📖 Guide
</a>
```

Then create a route that serves the guide content.

## Features of the Guide System

### The Guide Includes:
- How to discover startups
- Step-by-step submission process
- Managing and editing startups
- Claiming your company
- User engagement features
- Search and filtering
- Premium features
- Admin capabilities

### The Modal Display:
- Beautiful overlay modal
- Markdown to HTML conversion
- Responsive design
- Smooth animations
- Easy close (X button, overlay click, or ESC key)

## Testing

### Test the API Endpoint:
```bash
curl http://localhost:8000/api/startups/guide/
```

### Test in Browser Console:
```javascript
// If startup-guide.js is loaded
StartupGuide.show();

// Or manually fetch
fetch('/api/startups/guide/')
    .then(r => r.json())
    .then(console.log);
```

## Troubleshooting

### If the Guide button still redirects to home:

1. **Check if the script is loaded**:
   Open browser console and type: `StartupGuide`
   
2. **Manually attach the handler**:
   ```javascript
   StartupGuide.attach();
   ```

3. **Check for JavaScript errors**:
   Look in the browser console for any errors

4. **Verify API is working**:
   Visit: `http://localhost:8000/api/startups/guide/`

### Common Issues:

- **Button not found**: The script looks for buttons/links containing "Guide" text
- **API 404**: Ensure the Django server is running and URLs are configured
- **CORS issues**: If frontend is on different port, configure CORS settings

## Alternative: Inline Implementation

If you can't load external scripts, add this directly to your page:

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    const guideBtn = document.querySelector('button:contains("Guide"), a:contains("Guide")');
    if (guideBtn) {
        guideBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            const response = await fetch('/api/startups/guide/');
            const data = await response.json();
            alert('Guide loaded! Check console for content.');
            console.log(data.content);
        });
    }
});
</script>
```

## Contact

If you need further assistance integrating the guide, the implementation is modular and can be adapted to any frontend framework or technology stack.