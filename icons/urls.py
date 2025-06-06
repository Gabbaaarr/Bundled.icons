from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('download/', views.download_icon, name='download_icon'),
    path('icons/<slug:category_slug>/', views.category_icons, name='category_icons'),
    path('api/presigned-url/', views.get_presigned_url, name='get_presigned_url'),
]