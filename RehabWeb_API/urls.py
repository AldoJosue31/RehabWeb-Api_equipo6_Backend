from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from RehabWeb_API.views.auth import AuthTokenView
from RehabWeb_API.views.accounts import RoleAccountDetailView, RoleAccountListCreateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/auth/token/', AuthTokenView.as_view(), name='api-token-auth'),
    path('api/accounts/<str:role>/', RoleAccountListCreateView.as_view(), name='role-account-list'),
    path('api/accounts/<str:role>/<int:pk>/', RoleAccountDetailView.as_view(), name='role-account-detail'),
    path('api/mensajeria/', include('mensajeria.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
