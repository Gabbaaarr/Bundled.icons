from django.shortcuts import render,get_object_or_404
from .models import Icon, Category
from django.conf import settings
import logging
import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from urllib.parse import unquote
import boto3
from datetime import datetime, timedelta
from botocore.config import Config

logger = logging.getLogger(__name__)

def home(request):
    query = request.GET.get("q", "")
    categories = Category.objects.all()
    icons = Icon.objects.all()
    
    if query:
        icons = icons.filter(name__icontains=query) | icons.filter(tags__icontains=query)
    
    # Debug logging
    for icon in icons:
        logger.debug(f"Icon: {icon.name}, Category: {icon.category.name}, S3 URL: {icon.s3_url}")
        # Ensure consistent URL construction
        icon.s3_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/icons/{icon.category.name}/{icon.name}.svg"
        logger.debug(f"Updated S3 URL: {icon.s3_url}")
    
    context = {
        "icons": icons,
        "categories": categories,
        "debug": settings.DEBUG
    }
    
    return render(request, "icons/home.html", context)

@require_GET
def download_icon(request):
    url = unquote(request.GET.get('url', ''))
    name = unquote(request.GET.get('name', 'icon'))
    
    logger.debug(f"Download request received:")
    logger.debug(f"Raw URL parameter: {request.GET.get('url', '')}")
    logger.debug(f"Decoded URL: {url}")
    logger.debug(f"Raw name parameter: {request.GET.get('name', '')}")
    logger.debug(f"Decoded name: {name}")
    
    if not url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Extract bucket and key from URL
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        
        # Extract the key from the URL
        # URL format: https://bundled-icons-dev.s3.amazonaws.com/icons/actions/save.svg
        # We want to get: icons/actions/save.svg
        key = url.split('.com/')[-1]
        
        logger.debug(f"Attempting to download from S3:")
        logger.debug(f"Bucket: {bucket}")
        logger.debug(f"Key: {key}")
        logger.debug(f"Full URL: {url}")
        
        try:
            # Get the object from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            # Create the response with the SVG content
            http_response = HttpResponse(
                content,
                content_type='image/svg+xml'
            )
            
            # Set the Content-Disposition header to trigger download
            http_response['Content-Disposition'] = f'attachment; filename="{name}.svg"'
            
            return http_response
            
        except s3_client.exceptions.NoSuchKey:
            logger.error(f"File not found in S3: {key}")
            return HttpResponse(f'File not found in S3: {key}', status=404)
        except Exception as e:
            logger.error(f"Error getting object from S3: {str(e)}")
            return HttpResponse(f'Error getting file from S3: {str(e)}', status=500)
            
    except Exception as e:
        logger.error(f"Error in download_icon: {str(e)}")
        return HttpResponse(f'Error downloading file: {str(e)}', status=500)
    
def category_icons(request, category_slug):
    categories = Category.objects.all()
    category = get_object_or_404(Category, name=category_slug.replace('-', ' '))
    icons = Icon.objects.filter(category=category)
    
    # Debug logging
    for icon in icons:
        logger.debug(f"Icon: {icon.name}, Category: {icon.category.name}, S3 URL: {icon.s3_url}")
        # Ensure consistent URL construction
        icon.s3_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/icons/{icon.category.name}/{icon.name}.svg"
        logger.debug(f"Updated S3 URL: {icon.s3_url}")
    
    context = {
        'categories': categories,
        'current_category': category,
        'icons': icons
    }
    
    return render(request, 'icons/category_icons.html', context)

@require_GET
def get_presigned_url(request):
    s3_key = request.GET.get('s3_key')
    if not s3_key:
        return JsonResponse({'error': 'No s3_key provided'}, status=400)
    
    try:
        if settings.CLOUDFRONT_ENABLED:
            # Use CloudFront URL instead of pre-signed URL
            url = f"https://{settings.CLOUDFRONT_DOMAIN}/{s3_key}"
            return JsonResponse({'presigned_url': url})
        else:
            # Fallback to pre-signed URLs if CloudFront is disabled
            s3_client = boto3.client('s3',
                config=Config(
                    region_name=settings.AWS_S3_REGION_NAME,
                    signature_version='s3v4'
                )
            )
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=3600
            )
            return JsonResponse({'presigned_url': presigned_url})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)