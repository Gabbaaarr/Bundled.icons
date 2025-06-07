import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import boto3
from svgutils import transform
import math

def upload_icon_to_s3(file, category_name):
    s3_client = boto3.client('s3')
    file_name = os.path.basename(file.name)
    s3_key = f'icons/{category_name}/{file_name}'
    
    s3_client.upload_fileobj(
        file,
        settings.AWS_STORAGE_BUCKET_NAME,
        s3_key,
        ExtraArgs={'ContentType': 'image/svg+xml'}
    )
    
    return s3_key

def delete_icon_from_s3(s3_key):
    s3_client = boto3.client('s3')
    try:
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=s3_key
        )
    except Exception as e:
        print(f"Error deleting from S3: {e}")

def generate_sprite_sheet(icons, category_name, sheet_name, icons_per_row=10):
    # Create a new SVG
    width = 24 * icons_per_row
    height = 24 * math.ceil(len(icons) / icons_per_row)
    
    # Create the sprite sheet SVG
    sprite_sheet = transform.SVGFigure(width, height)
    
    # Add each icon to the sprite sheet
    for i, icon in enumerate(icons):
        row = i // icons_per_row
        col = i % icons_per_row
        
        # Load the icon SVG
        icon_svg = transform.fromfile(icon.file.path)
        icon_root = icon_svg.getroot()
        
        # Position the icon
        icon_root.moveto(col * 24, row * 24)
        
        # Add to sprite sheet
        sprite_sheet.append(icon_root)
    
    # Save the sprite sheet
    sprite_sheet_path = f'sprite_sheets/{category_name}/{sheet_name}.svg'
    sprite_sheet.save(sprite_sheet_path)
    
    # Upload to S3
    with open(sprite_sheet_path, 'rb') as f:
        s3_key = upload_icon_to_s3(f, f'sprite_sheets/{category_name}')
    
    return s3_key

def get_icon_from_sprite_sheet(sprite_sheet_url, x, y, width=24, height=24):
    # This function would be used to extract a single icon from the sprite sheet
    # Implementation depends on how you want to handle the extraction
    pass 