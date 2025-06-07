import boto3
from django.core.management.base import BaseCommand
from icons.models import Icon, Category
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Load icons from S3 bucket'

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

    def generate_tags(self, icon_name, category):
        base_tags = icon_name.split("-")
        category_tags = [category.lower()]
        extra_tags = {
            'arrows': ['navigation', 'direction'],
            'weather': ['nature', 'climate'],
            'media': ['audio', 'video'],
            'navigation': ['location', 'travel'],
            'objects': ['item', 'tool'],
            'actions': ['modify', 'action'],
            'social': ['network', 'share'],
            'status': ['notification', 'state']
        }.get(category, [])
        return ",".join(set(base_tags + category_tags + extra_tags))

    def handle(self, *args, **options):
        bucket_name = options.get('bucket') or settings.AWS_STORAGE_BUCKET_NAME
        prefix = options.get('prefix')

        if not bucket_name:
            self.stdout.write(self.style.ERROR('No bucket name provided and AWS_STORAGE_BUCKET_NAME not set in settings'))
            return

        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        self.stdout.write(f"Scanning S3 bucket: {bucket_name} with prefix: {prefix}")

        # List all objects in the bucket with the given prefix
        paginator = s3_client.get_paginator('list_objects_v2')
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

                category_name = parts[1]
                filename = parts[-1]
                name = filename.replace('.svg', '')

                # Create or get category
                category, created = Category.objects.get_or_create(name=category_name)
                if created:
                    self.stdout.write(f"Created new category: {category_name}")

                # Generate S3 URL
                s3_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{key}"
                
                # Generate tags
                tags = self.generate_tags(name, category_name)

                # Create or update icon
                icon, created = Icon.objects.update_or_create(
                    name=name,
                    category=category,
                    defaults={
                        'tags': tags,
                        's3_url': s3_url,
                        's3_key': key
                    }
                )

                status = 'created' if created else 'updated'
                self.stdout.write(f"Icon '{name}' {status} in category '{category_name}'")

        self.stdout.write(self.style.SUCCESS("Successfully processed all icons from S3")) 