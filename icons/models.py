from django.db import models
from django.conf import settings
from .utils import upload_icon_to_s3, delete_icon_from_s3

class IconCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Icon(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(IconCategory, on_delete=models.CASCADE)
    tags = models.CharField(max_length=250, blank=True)
    s3_url = models.URLField(blank=True)
    file = models.FileField(upload_to='icons/', null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.file and not self.s3_url:
            # Upload to S3 and get URL
            self.s3_url = upload_icon_to_s3(self.file, self.category.name)
        elif not self.s3_url:
            # Generate S3 URL if not present
            if settings.DEBUG:
                # Use Nginx proxy in development
                self.s3_url = f"http://{settings.AWS_S3_CUSTOM_DOMAIN}{settings.S3_PROXY_PREFIX}/icons/{self.category.name}/{self.name}.svg"
            else:
                # Use direct S3 URL in production
                self.s3_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/icons/{self.category.name}/{self.name}.svg"
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete from S3 before deleting the model
        if self.s3_url:
            delete_icon_from_s3(self.s3_url)
        super().delete(*args, **kwargs)
