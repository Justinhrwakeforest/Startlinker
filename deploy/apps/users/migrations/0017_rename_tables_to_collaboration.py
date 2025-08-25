# Migration to rename database tables from collection to collaboration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_rename_collections_to_collaborations'),
    ]

    operations = [
        # Rename the main table
        migrations.RunSQL(
            "ALTER TABLE users_startupcollection RENAME TO users_startupcollaboration;",
            reverse_sql="ALTER TABLE users_startupcollaboration RENAME TO users_startupcollection;"
        ),
        
        # Rename the collaborator table
        migrations.RunSQL(
            "ALTER TABLE users_collectioncollaborator RENAME TO users_collaborationcollaborator;",
            reverse_sql="ALTER TABLE users_collaborationcollaborator RENAME TO users_collectioncollaborator;"
        ),
        
        # Rename the item table
        migrations.RunSQL(
            "ALTER TABLE users_collectionitem RENAME TO users_collaborationitem;",
            reverse_sql="ALTER TABLE users_collaborationitem RENAME TO users_collectionitem;"
        ),
        
        # Rename the follow table
        migrations.RunSQL(
            "ALTER TABLE users_collectionfollow RENAME TO users_collaborationfollow;",
            reverse_sql="ALTER TABLE users_collaborationfollow RENAME TO users_collectionfollow;"
        ),
        
        # Rename field in collaboration table
        migrations.RunSQL(
            "ALTER TABLE users_startupcollaboration RENAME COLUMN collection_type TO collaboration_type;",
            reverse_sql="ALTER TABLE users_startupcollaboration RENAME COLUMN collaboration_type TO collection_type;"
        ),
        
        # Update foreign key column names in related tables
        migrations.RunSQL(
            "ALTER TABLE users_collaborationcollaborator RENAME COLUMN collection_id TO collaboration_id;",
            reverse_sql="ALTER TABLE users_collaborationcollaborator RENAME COLUMN collaboration_id TO collection_id;"
        ),
        
        migrations.RunSQL(
            "ALTER TABLE users_collaborationitem RENAME COLUMN collection_id TO collaboration_id;",
            reverse_sql="ALTER TABLE users_collaborationitem RENAME COLUMN collaboration_id TO collection_id;"
        ),
        
        migrations.RunSQL(
            "ALTER TABLE users_collaborationfollow RENAME COLUMN collection_id TO collaboration_id;",
            reverse_sql="ALTER TABLE users_collaborationfollow RENAME COLUMN collaboration_id TO collection_id;"
        ),
        
        # Update references in other tables that have foreign keys to the collaboration
        migrations.RunSQL(
            "UPDATE users_projecttask SET project_id = project_id WHERE project_id IN (SELECT id FROM users_startupcollaboration);",
            reverse_sql="UPDATE users_projecttask SET project_id = project_id WHERE project_id IN (SELECT id FROM users_startupcollaboration);"
        ),
    ]