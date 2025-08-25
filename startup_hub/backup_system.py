"""
Comprehensive Automated Backup System for StartupHub Production
Implements database backups, media file backups, and disaster recovery procedures.
"""

import os
import sys
import gzip
import shutil
import logging
import subprocess
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.core.cache import cache
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import threading
import time
from pathlib import Path

logger = logging.getLogger('startup_hub.backup')

class DatabaseBackup:
    """
    Advanced database backup with compression and cloud storage.
    """
    
    def __init__(self):
        self.backup_dir = os.environ.get('BACKUP_DIR', '/var/backups/startup_hub')
        self.s3_bucket = os.environ.get('BACKUP_S3_BUCKET')
        self.retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
        self.compress_backups = True
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize S3 client if configured
        self.s3_client = None
        if self.s3_bucket:
            try:
                self.s3_client = boto3.client('s3')
                logger.info("S3 backup client initialized")
            except NoCredentialsError:
                logger.warning("S3 credentials not found, local backups only")
    
    def create_database_backup(self, database_alias='default'):
        """Create a database backup with timestamp."""
        try:
            db_config = settings.DATABASES[database_alias]
            
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"startup_hub_db_{timestamp}.sql"
            
            if self.compress_backups:
                backup_filename += '.gz'
            
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create PostgreSQL backup command
            pg_dump_cmd = [
                'pg_dump',
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                f"--host={db_config['HOST']}",
                f"--port={db_config['PORT']}",
                f"--username={db_config['USER']}",
                db_config['NAME']
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            logger.info(f"Starting database backup: {backup_filename}")
            start_time = time.time()
            
            # Execute backup
            with open(backup_path, 'wb') as backup_file:
                if self.compress_backups:
                    # Use gzip compression
                    process = subprocess.Popen(
                        pg_dump_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    
                    with gzip.GzipFile(fileobj=backup_file, mode='wb') as gz_file:
                        while True:
                            chunk = process.stdout.read(1024 * 1024)  # 1MB chunks
                            if not chunk:
                                break
                            gz_file.write(chunk)
                    
                    process.wait()
                else:
                    # Direct backup without compression
                    process = subprocess.Popen(
                        pg_dump_cmd,
                        stdout=backup_file,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    process.wait()
                
                if process.returncode != 0:
                    error_output = process.stderr.read().decode()
                    raise Exception(f"pg_dump failed: {error_output}")
            
            backup_time = time.time() - start_time
            backup_size = os.path.getsize(backup_path)
            
            logger.info(
                f"Database backup completed: {backup_filename} "
                f"({backup_size / 1024 / 1024:.2f} MB in {backup_time:.2f}s)"
            )
            
            # Upload to S3 if configured
            if self.s3_client:
                self.upload_to_s3(backup_path, f"database/{backup_filename}")
            
            return {
                'filename': backup_filename,
                'path': backup_path,
                'size': backup_size,
                'duration': backup_time,
                'compressed': self.compress_backups
            }
            
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise
    
    def restore_database_backup(self, backup_path, database_alias='default'):
        """Restore database from backup file."""
        try:
            db_config = settings.DATABASES[database_alias]
            
            logger.warning(f"Starting database restore from: {backup_path}")
            
            # Prepare restore command
            psql_cmd = [
                'psql',
                '--no-password',
                '--verbose',
                f"--host={db_config['HOST']}",
                f"--port={db_config['PORT']}",
                f"--username={db_config['USER']}",
                f"--dbname={db_config['NAME']}"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            start_time = time.time()
            
            # Execute restore
            if backup_path.endswith('.gz'):
                # Decompress and restore
                with gzip.open(backup_path, 'rb') as gz_file:
                    process = subprocess.Popen(
                        psql_cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    
                    stdout, stderr = process.communicate(gz_file.read())
            else:
                # Direct restore
                with open(backup_path, 'rb') as backup_file:
                    process = subprocess.Popen(
                        psql_cmd,
                        stdin=backup_file,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    
                    stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Database restore failed: {stderr.decode()}")
            
            restore_time = time.time() - start_time
            logger.info(f"Database restore completed in {restore_time:.2f}s")
            
            return {
                'restored_from': backup_path,
                'duration': restore_time,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            raise
    
    def list_database_backups(self):
        """List available database backup files."""
        backups = []
        
        try:
            # List local backups
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('startup_hub_db_') and filename.endswith(('.sql', '.sql.gz')):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)
                    
                    backups.append({
                        'filename': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'location': 'local'
                    })
            
            # List S3 backups if configured
            if self.s3_client:
                try:
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.s3_bucket,
                        Prefix='database/'
                    )
                    
                    for obj in response.get('Contents', []):
                        backups.append({
                            'filename': os.path.basename(obj['Key']),
                            'path': f"s3://{self.s3_bucket}/{obj['Key']}",
                            'size': obj['Size'],
                            'created': obj['LastModified'],
                            'location': 's3'
                        })
                        
                except ClientError as e:
                    logger.error(f"Failed to list S3 backups: {str(e)}")
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def cleanup_old_backups(self):
        """Remove backup files older than retention period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            
            # Clean local backups
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('startup_hub_db_'):
                    filepath = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        removed_count += 1
                        logger.info(f"Removed old backup: {filename}")
            
            # Clean S3 backups if configured
            if self.s3_client:
                try:
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.s3_bucket,
                        Prefix='database/'
                    )
                    
                    for obj in response.get('Contents', []):
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                            self.s3_client.delete_object(
                                Bucket=self.s3_bucket,
                                Key=obj['Key']
                            )
                            removed_count += 1
                            logger.info(f"Removed old S3 backup: {obj['Key']}")
                            
                except ClientError as e:
                    logger.error(f"Failed to clean S3 backups: {str(e)}")
            
            logger.info(f"Cleaned up {removed_count} old backup files")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
            return 0
    
    def upload_to_s3(self, local_path, s3_key):
        """Upload backup file to S3."""
        try:
            if not self.s3_client:
                return False
            
            logger.info(f"Uploading backup to S3: {s3_key}")
            start_time = time.time()
            
            self.s3_client.upload_file(
                local_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD_IA',  # Cheaper storage for backups
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            upload_time = time.time() - start_time
            logger.info(f"S3 upload completed in {upload_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return False

class MediaBackup:
    """
    Media files backup system.
    """
    
    def __init__(self):
        self.media_root = settings.MEDIA_ROOT
        self.backup_dir = os.environ.get('MEDIA_BACKUP_DIR', '/var/backups/startup_hub/media')
        self.s3_bucket = os.environ.get('BACKUP_S3_BUCKET')
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize S3 client
        self.s3_client = None
        if self.s3_bucket:
            try:
                self.s3_client = boto3.client('s3')
            except NoCredentialsError:
                logger.warning("S3 credentials not found for media backup")
    
    def create_media_backup(self):
        """Create compressed backup of media files."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"startup_hub_media_{timestamp}.tar.gz"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            logger.info(f"Starting media backup: {backup_filename}")
            start_time = time.time()
            
            # Create tar.gz archive
            cmd = [
                'tar',
                '-czf',
                backup_path,
                '-C',
                os.path.dirname(self.media_root),
                os.path.basename(self.media_root)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Media backup failed: {result.stderr}")
            
            backup_time = time.time() - start_time
            backup_size = os.path.getsize(backup_path)
            
            logger.info(
                f"Media backup completed: {backup_filename} "
                f"({backup_size / 1024 / 1024:.2f} MB in {backup_time:.2f}s)"
            )
            
            # Upload to S3
            if self.s3_client:
                self.upload_media_to_s3(backup_path, f"media/{backup_filename}")
            
            return {
                'filename': backup_filename,
                'path': backup_path,
                'size': backup_size,
                'duration': backup_time
            }
            
        except Exception as e:
            logger.error(f"Media backup failed: {str(e)}")
            raise
    
    def upload_media_to_s3(self, local_path, s3_key):
        """Upload media backup to S3."""
        try:
            logger.info(f"Uploading media backup to S3: {s3_key}")
            
            self.s3_client.upload_file(
                local_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'GLACIER',  # Cheaper long-term storage
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            logger.info("Media backup uploaded to S3 successfully")
            
        except Exception as e:
            logger.error(f"Media S3 upload failed: {str(e)}")

class BackupScheduler:
    """
    Automated backup scheduling system.
    """
    
    def __init__(self):
        self.db_backup = DatabaseBackup()
        self.media_backup = MediaBackup()
        self.running = False
    
    def run_daily_backup(self):
        """Run daily backup routine."""
        try:
            logger.info("Starting daily backup routine")
            
            # Database backup
            db_result = self.db_backup.create_database_backup()
            
            # Media backup (less frequent, only if significant changes)
            media_result = None
            if self.should_backup_media():
                media_result = self.media_backup.create_media_backup()
            
            # Cleanup old backups
            cleanup_count = self.db_backup.cleanup_old_backups()
            
            # Store backup status in cache
            backup_status = {
                'timestamp': datetime.now().isoformat(),
                'database_backup': db_result,
                'media_backup': media_result,
                'cleanup_count': cleanup_count,
                'success': True
            }
            
            cache.set('last_backup_status', backup_status, timeout=86400 * 7)  # 1 week
            
            logger.info("Daily backup routine completed successfully")
            
            return backup_status
            
        except Exception as e:
            logger.error(f"Daily backup routine failed: {str(e)}")
            
            backup_status = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
            
            cache.set('last_backup_status', backup_status, timeout=86400 * 7)
            raise
    
    def should_backup_media(self):
        """Determine if media backup is needed."""
        # Check if media directory has been modified recently
        try:
            media_path = Path(self.media_backup.media_root)
            if not media_path.exists():
                return False
            
            # Get last media backup time
            last_backup = cache.get('last_media_backup_time')
            if not last_backup:
                return True  # First backup
            
            last_backup_time = datetime.fromisoformat(last_backup)
            
            # Check for files modified since last backup
            for file_path in media_path.rglob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time > last_backup_time:
                        return True
            
            # Also backup weekly regardless
            if datetime.now() - last_backup_time > timedelta(days=7):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking media backup need: {str(e)}")
            return True  # Default to backing up if uncertain
    
    def verify_backup_integrity(self, backup_path):
        """Verify backup file integrity."""
        try:
            if backup_path.endswith('.gz'):
                # Test gzip file
                with gzip.open(backup_path, 'rb') as f:
                    # Read first few bytes to verify it's valid
                    f.read(1024)
            elif backup_path.endswith('.tar.gz'):
                # Test tar.gz file
                cmd = ['tar', '-tzf', backup_path]
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode != 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Backup integrity check failed: {str(e)}")
            return False

class DisasterRecovery:
    """
    Disaster recovery procedures and utilities.
    """
    
    def __init__(self):
        self.db_backup = DatabaseBackup()
        self.media_backup = MediaBackup()
    
    def create_disaster_recovery_plan(self):
        """Create comprehensive disaster recovery documentation."""
        plan = {
            'created_at': datetime.now().isoformat(),
            'database_config': self.get_database_recovery_info(),
            'media_config': self.get_media_recovery_info(),
            'backup_locations': self.get_backup_locations(),
            'recovery_procedures': self.get_recovery_procedures(),
            'contact_information': self.get_contact_info(),
            'system_dependencies': self.get_system_dependencies()
        }
        
        # Save to file
        plan_path = os.path.join(self.db_backup.backup_dir, 'disaster_recovery_plan.json')
        with open(plan_path, 'w') as f:
            import json
            json.dump(plan, f, indent=2)
        
        logger.info(f"Disaster recovery plan created: {plan_path}")
        return plan
    
    def get_database_recovery_info(self):
        """Get database recovery information."""
        return {
            'database_type': 'PostgreSQL',
            'backup_format': 'pg_dump SQL',
            'compression': 'gzip',
            'restore_command': 'psql < backup_file.sql',
            'estimated_restore_time': '15-30 minutes for typical database size'
        }
    
    def get_media_recovery_info(self):
        """Get media files recovery information."""
        return {
            'backup_format': 'tar.gz',
            'restore_command': 'tar -xzf media_backup.tar.gz',
            'estimated_restore_time': '5-15 minutes depending on file count'
        }
    
    def get_backup_locations(self):
        """Get backup storage locations."""
        locations = [
            {
                'type': 'local',
                'path': self.db_backup.backup_dir,
                'retention': f"{self.db_backup.retention_days} days"
            }
        ]
        
        if self.db_backup.s3_bucket:
            locations.append({
                'type': 's3',
                'bucket': self.db_backup.s3_bucket,
                'region': os.environ.get('AWS_S3_REGION_NAME', 'us-east-1'),
                'retention': 'Configured via S3 lifecycle policy'
            })
        
        return locations
    
    def get_recovery_procedures(self):
        """Get step-by-step recovery procedures."""
        return {
            'database_recovery': [
                '1. Stop application services',
                '2. Create new database if needed',
                '3. Download latest backup from S3 or use local backup',
                '4. Restore database using psql command',
                '5. Update database configuration if needed',
                '6. Run migrations if necessary',
                '7. Start application services',
                '8. Verify application functionality'
            ],
            'media_recovery': [
                '1. Download media backup from S3 or use local backup',
                '2. Extract to correct media directory',
                '3. Set proper file permissions',
                '4. Update media serving configuration if needed',
                '5. Test file access and uploads'
            ],
            'full_system_recovery': [
                '1. Provision new server infrastructure',
                '2. Install required system packages',
                '3. Deploy application code',
                '4. Restore database from backup',
                '5. Restore media files from backup',
                '6. Configure environment variables',
                '7. Set up monitoring and logging',
                '8. Update DNS and load balancer configuration',
                '9. Perform comprehensive testing',
                '10. Notify stakeholders of recovery completion'
            ]
        }
    
    def get_contact_info(self):
        """Get emergency contact information."""
        return {
            'primary_admin': os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
            'backup_admin': os.environ.get('BACKUP_ADMIN_EMAIL', 'backup@example.com'),
            'hosting_provider': 'AWS',
            'domain_registrar': 'To be specified',
            'monitoring_service': 'Sentry/Custom monitoring'
        }
    
    def get_system_dependencies(self):
        """Get critical system dependencies."""
        return {
            'database': 'PostgreSQL 14+',
            'cache': 'Redis 6+',
            'web_server': 'Nginx',
            'application_server': 'Gunicorn',
            'task_queue': 'Celery with Redis broker',
            'file_storage': 'AWS S3',
            'monitoring': 'Sentry, Custom monitoring',
            'ssl_certificates': 'Let\'s Encrypt or custom SSL'
        }

# Global backup instances
db_backup = DatabaseBackup()
media_backup = MediaBackup()
backup_scheduler = BackupScheduler()
disaster_recovery = DisasterRecovery()

def run_backup_now():
    """Run backup immediately (for manual execution)."""
    return backup_scheduler.run_daily_backup()

def get_backup_status():
    """Get latest backup status."""
    return cache.get('last_backup_status', {'error': 'No backup status available'})

def setup_backup_system():
    """Initialize backup system."""
    try:
        # Create backup directories
        os.makedirs(db_backup.backup_dir, exist_ok=True)
        os.makedirs(media_backup.backup_dir, exist_ok=True)
        
        # Create disaster recovery plan
        disaster_recovery.create_disaster_recovery_plan()
        
        logger.info("Backup system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup backup system: {str(e)}")
        raise