# Production Setup Instructions

## Required Steps After Deployment

### 1. Populate Job Types
After the first deployment, you need to populate the job types in the database:

```bash
python manage.py populate_job_types
```

This creates the standard job types:
- Full-time
- Part-time
- Contract
- Internship
- Freelance

### 2. Run Migrations
Ensure all migrations are applied:

```bash
python manage.py migrate
```

### 3. Create Superuser (if needed)
```bash
python manage.py createsuperuser
```

## Troubleshooting

### Job Creation Returns 400 Error
If job creation fails with validation errors, check:

1. **Job types exist**: Run `populate_job_types` command
2. **Email field**: Ensure the latest migration (0003_alter_job_company_email) is applied
3. **Required fields**: Check that all required fields are provided

### API Returns 401 Error
If API returns authentication errors, verify the frontend is sending proper auth tokens.

## Recent Changes

### Email Field Made Optional
- Job model: `company_email` field now has `blank=True`
- Serializer: Email validation only runs if email is provided
- Migration: `0003_alter_job_company_email.py` updates database schema
