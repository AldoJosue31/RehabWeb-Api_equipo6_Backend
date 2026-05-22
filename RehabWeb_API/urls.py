from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from RehabWeb_API.views.auth import AuthTokenView
from RehabWeb_API.views.accounts import RoleAccountDetailView, RoleAccountListCreateView
from RehabWeb_API.views.engagement import (
    AlertViewSet,
    ExerciseSessionViewSet,
    LeaderboardView,
    MotivationProfileView,
    PatientBadgeListView,
    WeeklySummaryView,
)

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'sessions', ExerciseSessionViewSet, basename='session')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/auth/token/', AuthTokenView.as_view(), name='api-token-auth'),
    path('api/accounts/<str:role>/', RoleAccountListCreateView.as_view(), name='role-account-list'),
    path('api/accounts/<str:role>/<int:pk>/', RoleAccountDetailView.as_view(), name='role-account-detail'),
    path('api/motivation/me/', MotivationProfileView.as_view(), name='motivation-profile'),
    path('api/motivation/badges/', PatientBadgeListView.as_view(), name='motivation-badges'),
    path('api/motivation/weekly-summary/', WeeklySummaryView.as_view(), name='weekly-summary'),
    path('api/motivation/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('api/mensajeria/', include('mensajeria.urls')),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
