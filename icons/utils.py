import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

def upload_icon_to_s3(icon_file, category_name):
    """
    Upload an icon file to S3 and return the URL
    """
    # Create a unique filename
    file_name = f"icons/{category_name}/{icon_file.name}"
    
    # Upload to S3
    path = default_storage.save(file_name, ContentFile(icon_file.read()))
    
    # Get the URL
    url = default_storage.url(path)
    
    return url

def delete_icon_from_s3(s3_url):
    """
    Delete an icon file from S3
    """
    if s3_url:
        # Extract the key from the URL (works for both CloudFront and S3 URLs)
        if settings.AWS_CLOUDFRONT_DOMAIN and settings.AWS_CLOUDFRONT_DOMAIN in s3_url:
            key = s3_url.split('/icons/')[-1]
            key = f"icons/{key}"
        else:
            key = s3_url.replace(f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/", "")
        default_storage.delete(key) 