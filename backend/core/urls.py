"""
URL configuration for Contexor project.
"""
from django.contrib import admin
from django.urls import path, include
from .views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('contentmgmt.urls')),
    path('api/ai/', include('ai.urls')),
]
