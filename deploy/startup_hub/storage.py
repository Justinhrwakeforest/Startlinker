# Custom storage backends for AWS S3

from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class StaticStorage(S3Boto3Storage):
    """Custom storage for static files"""
    location = 'static'
    default_acl = 'public-read'
    file_overwrite = True
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN


class MediaStorage(S3Boto3Storage):
    """Custom storage for media files"""
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN


class PrivateMediaStorage(S3Boto3Storage):
    """Custom storage for private media files (like pitch decks)"""
    location = 'private'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False  # Use direct S3 URLs for private files
    
    def url(self, name):
        """Generate presigned URLs for private files"""
        if not name:
            return name
        
        # Generate a presigned URL that expires in 1 hour
        from botocore.exceptions import ClientError
        try:
            url = self.connection.meta.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': self._encode_name(name)},
                ExpiresIn=3600  # 1 hour
            )
            return url
        except ClientError:
            return None