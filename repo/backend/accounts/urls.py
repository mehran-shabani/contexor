"""
URL configuration for accounts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet, basename='organization')
router.register(r'organization-members', views.OrganizationMemberViewSet, basename='organization-member')
router.register(r'workspaces', views.WorkspaceViewSet, basename='workspace')

urlpatterns = [
    # OTP Authentication
    path('otp/request/', views.request_otp, name='otp-request'),
    path('otp/verify/', views.verify_otp, name='otp-verify'),
    
    # JWT Token Refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Current User
    path('me/', views.current_user, name='current-user'),
    
    # Router URLs
    path('', include(router.urls)),
]
