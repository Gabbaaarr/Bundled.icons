from django.db import migrations
from django.utils.text import slugify
from django.utils import timezone

def migrate_categories(apps, schema_editor):
    IconCategory = apps.get_model('icons', 'IconCategory')
    Category = apps.get_model('icons', 'Category')
    Icon = apps.get_model('icons', 'Icon')
    
    # Create new categories
    for old_cat in IconCategory.objects.all():
        new_cat = Category.objects.create(
            name=old_cat.name,
            slug=slugify(old_cat.name),
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        # Update icons to point to new category
        Icon.objects.filter(category_id=old_cat.id).update(category=new_cat)

def reverse_migrate_categories(apps, schema_editor):
    Category = apps.get_model('icons', 'Category')
    IconCategory = apps.get_model('icons', 'IconCategory')
    Icon = apps.get_model('icons', 'Icon')
    
    # Create old categories
    for new_cat in Category.objects.all():
        old_cat = IconCategory.objects.create(name=new_cat.name)
        # Update icons to point to old category
        Icon.objects.filter(category_id=new_cat.id).update(category=old_cat)

class Migration(migrations.Migration):

    dependencies = [
        ('icons', '0003_auto_20240607_0841'),  # Update this to match your actual previous migration
    ]

    operations = [
        migrations.RunPython(migrate_categories, reverse_migrate_categories),
    ] 