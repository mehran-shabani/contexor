"""
URL configuration for AI app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'jobs', views.AiJobViewSet, basename='ai-job')
router.register(r'usage-logs', views.UsageLogViewSet, basename='usage-log')
router.register(r'usage-limits', views.UsageLimitViewSet, basename='usage-limit')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('usage/summary/', views.usage_summary, name='usage-summary'),
    path('', include(router.urls)),
]
