# PostgreSQL Setup Instructions

## Current Status
The application is currently using SQLite for simplicity. PostgreSQL is installed but needs configuration.

## To Switch to PostgreSQL:

### 1. Set PostgreSQL Password
First, you need to know your PostgreSQL password. If you forgot it, you can reset it:

```bash
# Run as Administrator in Command Prompt
net stop postgresql-x64-17
# Edit pg_hba.conf to trust local connections temporarily
# Located at: C:\Program Files\PostgreSQL\17\data\pg_hba.conf
# Change "md5" or "scram-sha-256" to "trust" for local connections
net start postgresql-x64-17
```

### 2. Create Database
Run the setup script:
```bash
setup_postgres.bat
```

Or manually:
```bash
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres
CREATE DATABASE startup_hub;
\q
```

### 3. Update Configuration

Update `.env` file:
```env
DB_PASSWORD=your_actual_postgres_password
```

### 4. Switch Settings
Edit `startup_hub/settings/local.py`:
- Comment out the SQLite configuration
- Uncomment the PostgreSQL configuration
- Update the password

### 5. Migrate Data

Export from SQLite:
```bash
python manage.py dumpdata > data.json
```

Switch to PostgreSQL and import:
```bash
python manage.py migrate
python manage.py loaddata data.json
```

### 6. Test Connection
```bash
python manage.py dbshell
```

## Benefits of PostgreSQL
- Better performance for production
- Advanced features (JSON fields, full-text search)
- Better concurrency handling
- More robust for large datasets

## Current SQLite is Fine For:
- Local development
- Testing
- Small to medium projects
- Up to ~100GB of data

The application will work perfectly with SQLite for now!