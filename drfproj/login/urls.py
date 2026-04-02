from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register('users', views.userviewset)
router.register('login', views.loginviewset, basename='login')
router.register('verify-otp', views.VerifyOtpViewSet, basename='verify-otp')
router.register('check-result', views.checkresultviewset, basename='check-result')
router.register('generate-pdf', views.GeneratePDF, basename='generate-pdf')


urlpatterns = [
    path('', include(router.urls)),
    path('api/', include(router.urls)),
    path('api/check-result/<int:pk>/', views.checkresultviewset.as_view({'put': 'update', 'delete': 'destroy'}), name='check-result-detail'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]