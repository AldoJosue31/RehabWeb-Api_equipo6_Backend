from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, VideoCall
from .serializers import ConversationSerializer, MessageSerializer, VideoCallSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(paciente=user) | Q(terapeuta=user))

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Filtrar mensajes de las conversaciones del usuario
        return Message.objects.filter(
            Q(conversation__paciente=user) | Q(conversation__terapeuta=user)
        )

    def perform_create(self, serializer):
        # Asigna automáticamente el usuario autenticado como el remitente
        serializer.save(sender=self.request.user)
        
        # Al enviar un mensaje, actualizamos la fecha de la conversación para que suba en la lista
        conversation = serializer.validated_data['conversation']
        conversation.save() # Dispara el auto_now del updated_at

    @action(detail=True, methods=['patch'])
    def cambiar_estado(self, request, pk=None):
        mensaje = self.get_object()
        nuevo_estado = request.data.get('status')
        
        estados_validos = dict(Message.STATUS_CHOICES).keys()
        
        if nuevo_estado in estados_validos:
            mensaje.status = nuevo_estado
            mensaje.save()
            return Response({'status': f'Mensaje marcado como {nuevo_estado}'})
            
        return Response(
            {'error': 'Estado no válido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
class VideoCallViewSet(viewsets.ModelViewSet):
    serializer_class = VideoCallSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Solo puedes ver las llamadas de las que eres parte
        user = self.request.user
        return VideoCall.objects.filter(
            Q(conversation__paciente=user) | Q(conversation__terapeuta=user)
        )

    @action(detail=False, methods=['post'])
    def iniciar_llamada(self, request):
        user = self.request.user
        conversation_id = request.data.get('conversation_id')
        
        if not conversation_id:
            return Response({"error": "Debe proporcionar conversation_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Validar que la conversación existe y el usuario es participante
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if user != conversation.paciente and user != conversation.terapeuta:
            return Response({"error": "No tienes permiso para iniciar una llamada aquí."}, status=status.HTTP_403_FORBIDDEN)

        # Buscar si ya hay una llamada activa para reciclar la sala
        llamada_activa = VideoCall.objects.filter(
            conversation=conversation, 
            status='activa'
        ).first()

        if llamada_activa:
            serializer = self.get_serializer(llamada_activa)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Si no hay, crear una nueva sala segura
        nueva_llamada = VideoCall.objects.create(
            conversation=conversation,
            initiator=user,
            status='activa'
        )

        # Registrar en el chat como un "Mensaje del sistema" (Opcional pero recomendado para UX)
        Message.objects.create(
            conversation=conversation,
            sender=user,
            encrypted_text=f"📞 Videollamada iniciada. Sala: {nueva_llamada.room_id}",
            status='entregado'
        )
        
        conversation.save() # Actualizar updated_at
        
        serializer = self.get_serializer(nueva_llamada)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def finalizar_llamada(self, request, pk=None):
        llamada = self.get_object()
        
        if llamada.status != 'finalizada':
            llamada.status = 'finalizada'
            llamada.ended_at = timezone.now()
            llamada.save()
            
        return Response({"status": "Llamada finalizada", "duracion_minutos": llamada.duration_minutes})