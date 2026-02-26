from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from app.views import *
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'templates', PreparationTemplateViewSet)
router.register(r'preparations', PatientPreparationViewSet)
router.register(r'iol-calculations', IOLCalculationViewSet)
router.register(r'feedback', SurgeonFeedbackViewSet)
router.register(r'media', MediaFileViewSet)
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'me', CurrentUserViewSet, basename='me')

urlpatterns = [
    path('', lambda request: redirect('admin/')),  # Редирект на админку
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("api/login/", LoginView.as_view(), name="login"),
    path("csrf/", CSFView.as_view(), name="csrf"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)