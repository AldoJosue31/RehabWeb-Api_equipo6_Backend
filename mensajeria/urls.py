from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet, VideoCallViewSet

router = DefaultRouter()
router.register(r'conversaciones', ConversationViewSet, basename='conversacion')
router.register(r'mensajes', MessageViewSet, basename='mensaje')
router.register(r'videollamadas', VideoCallViewSet, basename='videollamada')

urlpatterns = [
    path('', include(router.urls)),
]