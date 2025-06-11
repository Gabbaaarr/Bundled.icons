import boto3
from django.core.management.base import BaseCommand
from django.db import transaction
from icons.models import Icon, IconCategory
from django.conf import settings
import logging
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Load icons from S3 bucket into the database using exact folder names as categories'

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
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing icons and categories before loading'
        )

    def get_cloudfront_url(self, key):
        """Generate a CloudFront URL for the given S3 key."""
        if not settings.AWS_CLOUDFRONT_DOMAIN:
            raise ValueError("AWS_CLOUDFRONT_DOMAIN not set in settings")
        return f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{key}"

    def validate_url(self, url):
        """Validate and clean URL if necessary."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    @transaction.atomic
    def handle(self, *args, **options):
        bucket_name = options.get('bucket') or settings.AWS_STORAGE_BUCKET_NAME
        prefix = options.get('prefix')
        clear_existing = options.get('clear')

        if not bucket_name:
            self.stdout.write(self.style.ERROR('No bucket name provided and AWS_STORAGE_BUCKET_NAME not set in settings'))
            return

        if not settings.AWS_CLOUDFRONT_DOMAIN:
            self.stdout.write(self.style.ERROR('AWS_CLOUDFRONT_DOMAIN not set in settings'))
            return

        # Clear existing data if requested
        if clear_existing:
            self.stdout.write("Clearing existing icons and categories...")
            Icon.objects.all().delete()
            IconCategory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing data"))

        # Initialize S3 client
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize S3 client: {str(e)}'))
            return

        self.stdout.write(f"Scanning S3 bucket: {bucket_name} with prefix: {prefix}")

        # First, get all folders (categories) in the bucket
        folders = set()
        paginator = s3.get_paginator('list_objects_v2')
        
        try:
            # List all objects to get unique folder names
            for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
                if 'CommonPrefixes' in page:
                    for prefix_obj in page['CommonPrefixes']:
                        folder_path = prefix_obj['Prefix']
                        folder_name = folder_path[len(prefix):].rstrip('/')
                        if folder_name:
                            folders.add(folder_name)

            if not folders:
                self.stdout.write(self.style.WARNING(f"No folders found in bucket {bucket_name} with prefix {prefix}"))
                return

            self.stdout.write(f"Found {len(folders)} folders: {', '.join(folders)}")

            # Process each folder
            for folder in folders:
                try:
                    # Create category with exact folder name
                    category, created = IconCategory.objects.get_or_create(name=folder)
                    if created:
                        self.stdout.write(f"Created category: {folder}")

                    # List all objects in this folder
                    folder_prefix = f"{prefix}{folder}/"
                    icons_processed = 0
                    icons_skipped = 0

                    for page in paginator.paginate(Bucket=bucket_name, Prefix=folder_prefix):
                        if 'Contents' not in page:
                            continue

                        for obj in page['Contents']:
                            key = obj['Key']
                            
                            # Skip if not an SVG file
                            if not key.endswith('.svg'):
                                continue

                            try:
                                # Get the filename without extension
                                filename = os.path.basename(key)
                                name = os.path.splitext(filename)[0]

                                # Generate CloudFront URL
                                cloudfront_url = self.get_cloudfront_url(key)
                                
                                if not self.validate_url(cloudfront_url):
                                    self.stdout.write(self.style.WARNING(f"Invalid URL generated for {key}, skipping..."))
                                    icons_skipped += 1
                                    continue

                                # Create or update icon
                                icon, created = Icon.objects.update_or_create(
                                    name=name,
                                    category=category,
                                    defaults={
                                        's3_url': cloudfront_url,
                                        'tags': None  # Set to None instead of empty string
                                    }
                                )

                                icons_processed += 1
                                if created:
                                    self.stdout.write(f"Created icon: {name} in {folder}")
                                else:
                                    self.stdout.write(f"Updated icon: {name} in {folder}")

                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Error processing icon {key}: {str(e)}"))
                                icons_skipped += 1
                                continue

                    self.stdout.write(self.style.SUCCESS(
                        f"Processed folder {folder}: {icons_processed} icons processed, {icons_skipped} skipped"
                    ))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing folder {folder}: {str(e)}"))
                    continue

            # Final summary
            total_icons = Icon.objects.count()
            total_categories = IconCategory.objects.count()
            self.stdout.write(self.style.SUCCESS(
                f"\nImport completed successfully:\n"
                f"Total categories: {total_categories}\n"
                f"Total icons: {total_icons}"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to process S3 bucket: {str(e)}"))
            raise 