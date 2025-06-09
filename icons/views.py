from django.shortcuts import render, get_object_or_404
from .models import Icon, IconCategory
from django.conf import settings
import logging
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from urllib.parse import unquote
import boto3

logger = logging.getLogger(__name__)

def home(request):
    query = request.GET.get("q", "")
    categories = IconCategory.objects.all()
    icons = Icon.objects.all()
    
    if query:
        icons = icons.filter(name__icontains=query) | icons.filter(tags__icontains=query)
    
    # Debug logging
    for icon in icons:
        logger.debug(f"Icon: {icon.name}, Category: {icon.category.name}, URL: {icon.s3_url}")
    
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
        
        # Extract the key from the URL (works for both CloudFront and S3 URLs)
        if settings.AWS_CLOUDFRONT_DOMAIN and settings.AWS_CLOUDFRONT_DOMAIN in url:
            key = url.split('/icons/')[-1]
            key = f"icons/{key}"
        else:
            key = url.split('.com/')[-1]
        
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
    categories = IconCategory.objects.all()
    category = get_object_or_404(IconCategory, name=category_slug.replace('-', ' '))
    icons = Icon.objects.filter(category=category)
    
    # Debug logging
    for icon in icons:
        logger.debug(f"Icon: {icon.name}, Category: {icon.category.name}, URL: {icon.s3_url}")
    
    context = {
        'category': category,
        'icons': icons,
        'categories': categories,
        'debug': settings.DEBUG
    }
    
    return render(request, 'icons/category_icons.html', context)