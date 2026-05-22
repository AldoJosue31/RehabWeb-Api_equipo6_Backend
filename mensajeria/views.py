from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, VideoCall
from .serializers import ConversationSerializer, MessageSerializer, VideoCallSerializer
from RehabWeb_API.permissions import HasSelectedRole
from RehabWeb_API.roles import (
    ROLE_PACIENTE,
    ROLE_TERAPEUTA,
    get_request_role,
    user_matches_conversation_role,
)

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get_queryset(self):
        user = self.request.user
        selected_role = get_request_role(self.request)
        if selected_role == ROLE_PACIENTE:
            return Conversation.objects.select_related('paciente', 'terapeuta').filter(paciente=user)
        if selected_role == ROLE_TERAPEUTA:
            return Conversation.objects.select_related('paciente', 'terapeuta').filter(terapeuta=user)

        return Conversation.objects.select_related('paciente', 'terapeuta').filter(Q(paciente=user) | Q(terapeuta=user))

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get_queryset(self):
        user = self.request.user
        selected_role = get_request_role(self.request)
        conversation_id = self.request.query_params.get('conversation')
        if selected_role == ROLE_PACIENTE:
            queryset = Message.objects.filter(conversation__paciente=user)
        elif selected_role == ROLE_TERAPEUTA:
            queryset = Message.objects.filter(conversation__terapeuta=user)
        else:
            queryset = Message.objects.filter(
                Q(conversation__paciente=user) | Q(conversation__terapeuta=user)
            )

        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)

        return queryset.select_related('conversation', 'sender')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        conversation_id = request.query_params.get('conversation')

        if conversation_id:
            before = request.query_params.get('before')
            if before:
                before_date = parse_datetime(before)
                if before_date:
                    queryset = queryset.filter(timestamp__lt=before_date)

            limit = min(int(request.query_params.get('limit', 20)), 20)
            page = list(queryset.order_by('-timestamp')[:limit + 1])
            has_more = len(page) > limit
            page = sorted(page[:limit], key=lambda message: message.timestamp)
            serializer = self.get_serializer(page, many=True)
            return Response(serializer.data, headers={'X-Has-More': 'true' if has_more else 'false'})

        return super().list(request, *args, **kwargs)

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
    @action(detail=False, methods=['patch'])
    def marcar_vistos(self, request):
        conversation_id = request.data.get('conversation_id')
        if not conversation_id:
            return Response({'error': 'Debe proporcionar conversation_id'}, status=status.HTTP_400_BAD_REQUEST)

        updated = self.get_queryset().filter(
            conversation_id=conversation_id,
        ).exclude(sender=request.user).exclude(status='visto').update(status='visto')

        return Response({'actualizados': updated})
    
class VideoCallViewSet(viewsets.ModelViewSet):
    serializer_class = VideoCallSerializer
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get_queryset(self):
        # Solo puedes ver las llamadas de las que eres parte
        user = self.request.user
        selected_role = get_request_role(self.request)
        if selected_role == ROLE_PACIENTE:
            return VideoCall.objects.filter(conversation__paciente=user)
        if selected_role == ROLE_TERAPEUTA:
            return VideoCall.objects.filter(conversation__terapeuta=user)

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

        selected_role = get_request_role(request)
        if selected_role != ROLE_TERAPEUTA:
            return Response({"error": "Solo el terapeuta puede iniciar la videoconsulta."}, status=status.HTTP_403_FORBIDDEN)

        if selected_role and not user_matches_conversation_role(user, conversation, selected_role):
            return Response({"error": "El rol seleccionado no participa en esta conversacion."}, status=status.HTTP_403_FORBIDDEN)

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
            encrypted_text=f"Videollamada iniciada. Sala: {nueva_llamada.room_id}",
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
