"""
URL configuration for content management app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'prompts', views.PromptViewSet, basename='prompt')
router.register(r'contents', views.ContentViewSet, basename='content')
router.register(r'content-versions', views.ContentVersionViewSet, basename='content-version')
router.register(r'versions', views.VersionViewSet, basename='version')

urlpatterns = [
    path('', include(router.urls)),
]
