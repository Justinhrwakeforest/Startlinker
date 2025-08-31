# Production Setup Instructions

## Populate Industries in Production Database

The startup submit form requires industries to be populated in the production database. Follow these steps:

### Method 1: Run Django Management Command in Render Console

1. **Access Render Dashboard**:
   - Go to [render.com](https://render.com)
   - Navigate to your StartLinker backend service

2. **Open Shell/Console**:
   - Click on your service name
   - Go to the "Shell" tab or "Console" option
   - This opens a terminal connected to your production environment

3. **Run the Population Command**:
   ```bash
   # First, do a dry run to see what will be created
   python manage.py populate_industries --dry-run
   
   # Then run the actual command to populate industries
   python manage.py populate_industries
   
   # Or update existing industries with new descriptions
   python manage.py populate_industries --update
   ```

### Method 2: Use Render Build Command (Alternative)

Add this to your Render service build command:
```bash
# After your existing build commands, add:
python manage.py populate_industries
```

### Expected Output

The command will create **31 comprehensive tech startup industries** including:

- **Core Tech**: AI, SaaS, Mobile Apps, Web Development, Cloud Computing, Cybersecurity, Data Analytics, Blockchain
- **Business**: E-commerce, FinTech, Marketing Tech, HR, Customer Service, Project Management  
- **Industry Specific**: HealthTech, EdTech, AgriTech, Real Estate Tech, Travel, Food & Beverage, Transportation, Clean Tech
- **Emerging Tech**: IoT, AR/VR, Gaming, Social Media, Content & Media, Hardware
- **General**: Enterprise Software, Consumer Software, Other

### Verification

After running the command, verify industries were created:

1. **Check via Django Admin**:
   - Go to: `https://your-app.onrender.com/admin/`
   - Login with admin credentials
   - Navigate to "Startups" → "Industries"
   - You should see 31+ industries listed

2. **Check via API**:
   - Visit: `https://your-app.onrender.com/api/industries/`
   - You should see a JSON list of all industries

### Command Options

- `--dry-run`: Preview what will be created without making changes
- `--update`: Update existing industries with new descriptions/icons
- `--help`: Show all available options

### Troubleshooting

**If command fails with "No module named apps.startups"**:
```bash
# Make sure you're in the correct directory
cd /opt/render/project/src
python manage.py populate_industries
```

**If you get permission errors**:
- Ensure your database user has write permissions
- Check that DJANGO_SETTINGS_MODULE is set correctly

**To check current industry count**:
```bash
python manage.py shell -c "from apps.startups.models import Industry; print(f'Industries: {Industry.objects.count()}')"
```

### After Population

Once industries are populated:
1. The startup submit form will show industry dropdown options
2. Users can select from 31+ comprehensive industry categories
3. The admin panel will show all industries for management
4. API endpoints will return industry data for frontend forms

**Status**: Ready for production use! ✅