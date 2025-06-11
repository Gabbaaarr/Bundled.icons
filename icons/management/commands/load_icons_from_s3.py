import boto3
from django.core.management.base import BaseCommand
from icons.models import Icon, IconCategory
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Load icons from S3 bucket into the database using folder names as categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket',
            type=str,
            help='S3 bucket name (optional, will use settings.AWS_STORAGE_BUCKET_NAME if not provided)',
            required=False
        )
        parser.add_argument(
            '--prefix',
            type=str,
            help='Prefix/folder path in S3 bucket (e.g., "icons/")',
            default='icons/'
        )

    def get_cloudfront_url(self, key):
        """Generate a CloudFront URL for the given S3 key."""
        if not settings.AWS_CLOUDFRONT_DOMAIN:
            raise ValueError("AWS_CLOUDFRONT_DOMAIN not set in settings")
        return f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{key}"

    def handle(self, *args, **options):
        bucket_name = options.get('bucket') or settings.AWS_STORAGE_BUCKET_NAME
        prefix = options.get('prefix')

        if not bucket_name:
            self.stdout.write(self.style.ERROR('No bucket name provided and AWS_STORAGE_BUCKET_NAME not set in settings'))
            return

        if not settings.AWS_CLOUDFRONT_DOMAIN:
            self.stdout.write(self.style.ERROR('AWS_CLOUDFRONT_DOMAIN not set in settings'))
            return

        # Initialize S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        self.stdout.write(f"Scanning S3 bucket: {bucket_name} with prefix: {prefix}")

        # List all objects in the bucket with the given prefix
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        # Track categories we've seen
        categories = set()

        for page in pages:
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']
                
                # Skip if not an SVG file
                if not key.endswith('.svg'):
                    continue

                # Extract category and filename from the key
                # Expected format: icons/category/filename.svg
                parts = key.split('/')
                if len(parts) < 3:
                    continue

                category_name = parts[1]  # Get the folder name as category
                filename = parts[-1]
                name = filename.replace('.svg', '')

                # Create or get category (using folder name as is)
                category, created = IconCategory.objects.get_or_create(name=category_name)
                if created:
                    self.stdout.write(f"Created new category: {category_name}")

                # Generate CloudFront URL
                cloudfront_url = self.get_cloudfront_url(key)
                
                # Create or update icon with minimal information
                icon, created = Icon.objects.update_or_create(
                    name=name,
                    category=category,
                    defaults={
                        's3_url': cloudfront_url,
                        'tags': ''  # Empty tags as we're not auto-generating them
                    }
                )

                status = 'created' if created else 'updated'
                self.stdout.write(f"Icon '{name}' {status} in category '{category_name}'")

        self.stdout.write(self.style.SUCCESS("Successfully processed all icons from S3")) 