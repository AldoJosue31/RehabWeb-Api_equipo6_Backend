from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from RehabWeb_API.views.auth import AuthTokenView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/auth/token/', AuthTokenView.as_view(), name='api-token-auth'),
    path('api/mensajeria/', include('mensajeria.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
