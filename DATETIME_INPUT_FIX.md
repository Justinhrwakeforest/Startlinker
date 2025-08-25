# DateTime Input Visibility Fix

## Issue
The datetime-local input in the "Schedule New Post" modal was not displaying typed text, showing only placeholder text while the actual input values remained invisible.

## Root Cause
- Browser's default color scheme handling for `input[type="datetime-local"]`
- WebKit browsers applying system colors that conflict with the light theme
- Missing explicit text color declarations for datetime input components

## Solution Applied

### 1. Inline Styles Added
```jsx
style={{
  colorScheme: 'light',
  WebkitAppearance: 'none',
  color: '#111827 !important',
  backgroundColor: '#ffffff !important',
  fontSize: '14px',
  fontFamily: 'inherit'
}}
```

### 2. CSS File Created
**Location:** `frontend/src/styles/datetime-input-fix.css`

**Key Features:**
- Forces light color scheme on all datetime inputs
- Targets WebKit-specific pseudo-elements
- Handles dark mode override
- Provides cross-browser compatibility

### 3. Component Updates
**File:** `frontend/src/components/social/PostScheduler.js`

**Changes:**
- Imported the CSS fix file
- Added `datetime-input-custom` class
- Applied inline styles with `!important` declarations
- Wrapped input in relative div for better control

## Technical Details

### WebKit Pseudo-Elements Targeted:
- `::-webkit-datetime-edit`
- `::-webkit-datetime-edit-fields-wrapper`
- `::-webkit-datetime-edit-text`
- `::-webkit-datetime-edit-month-field`
- `::-webkit-datetime-edit-day-field`
- `::-webkit-datetime-edit-year-field`
- `::-webkit-datetime-edit-hour-field`
- `::-webkit-datetime-edit-minute-field`

### Cross-Browser Support:
- **Chrome/Safari:** WebKit pseudo-elements + colorScheme
- **Firefox:** Direct color/background-color properties
- **Edge:** Combination of both approaches

### Dark Mode Handling:
```css
@media (prefers-color-scheme: dark) {
  input[type="datetime-local"] {
    color-scheme: light !important;
    color: #111827 !important;
    background-color: #ffffff !important;
  }
}
```

## Result
✅ **Before:** Invisible text input with only placeholder visible  
✅ **After:** Clearly visible dark text on white background  
✅ **Cross-browser:** Works in Chrome, Safari, Firefox, and Edge  
✅ **Responsive:** Maintains styling across different screen sizes  

## Files Modified
1. `frontend/src/components/social/PostScheduler.js` - Component updates
2. `frontend/src/styles/datetime-input-fix.css` - CSS fixes (new file)

## Testing
- Tested input text visibility
- Verified placeholder text distinction
- Confirmed focus states work properly
- Validated cross-browser compatibility