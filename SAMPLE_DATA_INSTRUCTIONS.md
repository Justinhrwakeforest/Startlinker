# Sample Data Instructions

## Overview
This guide explains how to load sample data for the social features (Collections, Achievements, and Scheduled Posts) into your StartupHub database.

## Prerequisites
- Django project must be set up and running
- Database migrations must be applied
- At least some users and startups should exist in the database

## Method 1: Using Django Management Command (Recommended)

### Step 1: Apply Migrations
First, ensure all migrations are applied:
```bash
python manage.py migrate
```

### Step 2: Load Basic Data (if not already done)
If you haven't loaded users and startups yet:
```bash
python manage.py loaddata initial_data.json  # If you have fixtures
# OR
python manage.py createsuperuser  # Create at least one admin user
```

### Step 3: Run the Social Sample Data Command
```bash
python manage.py load_social_sample_data
```

This command will:
- Create sample achievements (16 different types)
- Create 8 startup collections with various types (public, private, collaborative)
- Add startups to collections with custom notes and tags
- Create scheduled posts for future publication
- Set up user follow relationships
- Create stories (24-hour content)
- Assign achievements to users

## Method 2: Using SQL Script (Alternative)

### For PostgreSQL:
```bash
psql -U your_username -d your_database_name -f sample_social_data.sql
```

### For SQLite:
```bash
sqlite3 db.sqlite3 < sample_social_data.sql
```

### Note for SQL Method:
- You'll need to adjust user IDs and startup IDs in the SQL script based on your existing data
- The SQL script uses PostgreSQL syntax (gen_random_uuid(), INTERVAL)
- For SQLite, replace gen_random_uuid() with hex(randomblob(16))
- For SQLite, replace NOW() with datetime('now')
- For SQLite, replace INTERVAL syntax with datetime('now', '+1 day')

## Sample Data Overview

### Achievements Created:
1. **Profile Achievements**: First Steps, Profile Pro
2. **Social Achievements**: Social Butterfly, Influencer
3. **Content Achievements**: First Post, Content Creator, Curator, Scheduler Master
4. **Networking Achievements**: Connector, Community Builder
5. **Startup Achievements**: Startup Founder, Serial Entrepreneur
6. **Jobs Achievements**: Job Creator, Hiring Manager
7. **Special Achievements**: Early Adopter (Secret), Night Owl (Secret)

### Collections Created:
1. **AI & Machine Learning Innovators** - Featured public collection
2. **Green Tech & Sustainability** - Featured public collection
3. **EdTech Revolution** - Collaborative collection
4. **My Investment Watchlist** - Private collection
5. **HealthTech Pioneers** - Public collection
6. **FinTech Disruptors** - Public collection
7. **Social Impact Startups** - Featured collaborative collection
8. **Future of Work** - Public collection

### Scheduled Posts Created:
1. **Weekly Startup Spotlight** - Discussion post scheduled for tomorrow
2. **Green Tech Summit Announcement** - Event announcement for next week
3. **EdTech Feature Request** - Question post for community feedback
4. **Financial Planning Resources** - Resource sharing post
5. **FinTech Meetup** - Event post with details

### Other Features:
- User follow relationships between sample users
- Stories with different types (text, achievement, link)
- Collection items with custom notes and tags
- Achievement progress tracking

## Verifying the Data

### Check Achievements:
```python
python manage.py shell
>>> from apps.users.social_models import Achievement
>>> Achievement.objects.count()
>>> Achievement.objects.values_list('name', 'category', 'rarity')
```

### Check Collections:
```python
>>> from apps.users.social_models import StartupCollection
>>> StartupCollection.objects.count()
>>> for c in StartupCollection.objects.all():
...     print(f"{c.name} by {c.owner.username} - {c.collection_type}")
```

### Check Scheduled Posts:
```python
>>> from apps.users.social_models import ScheduledPost
>>> ScheduledPost.objects.filter(status='scheduled').count()
>>> for sp in ScheduledPost.objects.filter(status='scheduled'):
...     print(f"{sp.title} - scheduled for {sp.scheduled_for}")
```

## Testing the Features

### 1. View Achievements:
- Login to the platform
- Go to your profile
- Check the achievements section

### 2. Browse Collections:
- Navigate to the Collections section
- View featured collections
- Try creating your own collection

### 3. Check Scheduled Posts:
- Go to create a post
- Look for the "Schedule" option
- View your scheduled posts in your dashboard

### 4. View Stories:
- Check the stories bar at the top of the feed
- Click to view active stories
- Stories expire after 24 hours

## Troubleshooting

### If data doesn't load:
1. Check that migrations are applied: `python manage.py showmigrations`
2. Ensure you have users and startups in the database
3. Check for any error messages in the console
4. Verify database connection settings

### If achievements don't show:
1. Make sure the achievement earned_count is updated
2. Check that UserAchievement records were created
3. Verify is_active=True on achievements

### If collections are empty:
1. Ensure startups exist in the database
2. Check that CollectionItem records were created
3. Verify the collection type permissions

## Customizing Sample Data

To modify the sample data:
1. Edit `apps/core/management/commands/load_social_sample_data.py`
2. Adjust the data arrays in the respective create methods
3. Run the command again (it uses get_or_create to avoid duplicates)

## Clean Up

To remove all sample data:
```python
python manage.py shell
>>> from apps.users.social_models import *
>>> Achievement.objects.all().delete()
>>> StartupCollection.objects.all().delete()
>>> ScheduledPost.objects.all().delete()
>>> Story.objects.all().delete()
>>> UserFollow.objects.all().delete()
```

**Warning**: This will delete ALL data for these models, not just sample data!