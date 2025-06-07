from django.contrib import admin
from .models import Icon, Category, SpriteSheet

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_featured', 'created_at')
    list_filter = ('is_featured',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

@admin.register(SpriteSheet)
class SpriteSheetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'icon_count', 'created_at')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(Icon)
class IconAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sprite_sheet', 'width', 'height', 'download_count', 'is_featured', 'created_at')
    list_filter = ('category', 'sprite_sheet', 'is_featured')
    search_fields = ('name', 's3_key')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'download_count')
