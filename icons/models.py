from django.db import models
from django.conf import settings
from .utils import upload_icon_to_s3, delete_icon_from_s3
from django.utils.text import slugify
import os

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SpriteSheet(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sprite_sheets')
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='sprite_sheets/')
    icon_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Icon(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='icons')
    sprite_sheet = models.ForeignKey(SpriteSheet, on_delete=models.SET_NULL, null=True, related_name='icons')
    position_x = models.IntegerField(default=0)  # Position in sprite sheet
    position_y = models.IntegerField(default=0)  # Position in sprite sheet
    width = models.IntegerField(default=24)      # Icon width in sprite sheet
    height = models.IntegerField(default=24)     # Icon height in sprite sheet
    tags = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    s3_key = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'category']

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    def get_s3_url(self):
        if self.s3_key:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.s3_key}"
        return None

    def save(self, *args, **kwargs):
        if self.sprite_sheet:
            # Upload to S3 and get URL
            self.s3_key = self.s3_key
        elif not self.s3_key:
            # Generate S3 URL if not present
            self.s3_key = self.s3_key
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete from S3 before deleting the model
        if self.s3_key:
            delete_icon_from_s3(self.s3_key)
        super().delete(*args, **kwargs)
