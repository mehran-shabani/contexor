"""
URL configuration for Contexor project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('contentmgmt.urls')),
    path('api/ai/', include('ai.urls')),
]
