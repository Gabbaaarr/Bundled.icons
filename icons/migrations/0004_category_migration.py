from django.db import migrations, models
import django.db.models.deletion
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
        ('icons', '0003_alter_icon_s3_url'),
    ]

    operations = [
        # Create new Category model
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(blank=True)),
                ('order', models.IntegerField(default=0)),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['order', 'name'],
            },
        ),
        # Create SpriteSheet model
        migrations.CreateModel(
            name='SpriteSheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('file', models.FileField(upload_to='sprite_sheets/')),
                ('icon_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sprite_sheets', to='icons.category')),
            ],
        ),
        # Add new fields to Icon
        migrations.AddField(
            model_name='icon',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='icon',
            name='download_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='icon',
            name='height',
            field=models.IntegerField(default=24),
        ),
        migrations.AddField(
            model_name='icon',
            name='is_featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='icon',
            name='position_x',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='icon',
            name='position_y',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='icon',
            name='s3_key',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='icon',
            name='sprite_sheet',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='icons', to='icons.spritesheet'),
        ),
        migrations.AddField(
            model_name='icon',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='icon',
            name='width',
            field=models.IntegerField(default=24),
        ),
        # Add temporary category field
        migrations.AddField(
            model_name='icon',
            name='new_category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='new_icons', to='icons.category'),
        ),
        # Run the data migration
        migrations.RunPython(migrate_categories, reverse_migrate_categories),
        # Remove old category field
        migrations.RemoveField(
            model_name='icon',
            name='category',
        ),
        # Rename new_category to category
        migrations.RenameField(
            model_name='icon',
            old_name='new_category',
            new_name='category',
        ),
        # Remove old fields
        migrations.RemoveField(
            model_name='icon',
            name='s3_url',
        ),
        # Remove old model
        migrations.DeleteModel(
            name='IconCategory',
        ),
    ] 