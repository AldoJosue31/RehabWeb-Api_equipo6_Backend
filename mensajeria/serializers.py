from rest_framework import serializers
from .models import Conversation, Message, VideoCall
from RehabWeb_API.models import PacienteProfile, TerapeutaProfile
from RehabWeb_API.roles import (
    ROLE_PACIENTE,
    ROLE_TERAPEUTA,
    get_request_role,
    user_has_role,
    user_matches_conversation_role,
)

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'encrypted_text', 
            'file_attachment', 'timestamp', 'status'
        ]
        read_only_fields = ['id', 'sender', 'timestamp', 'status']

    def validate_file_attachment(self, value):
        if value:
            limit_mb = 5
            if value.size > limit_mb * 1024 * 1024:
                raise serializers.ValidationError(f"El archivo es demasiado grande. El máximo permitido es {limit_mb}MB.")
        return value

    def validate(self, data):
        if not data.get('encrypted_text') and not data.get('file_attachment'):
            raise serializers.ValidationError("El mensaje debe contener texto cifrado o un archivo adjunto.")

        request = self.context.get('request')
        conversation = data.get('conversation') or getattr(self.instance, 'conversation', None)
        if request and conversation:
            if request.user.id not in (conversation.paciente_id, conversation.terapeuta_id):
                raise serializers.ValidationError("No puedes enviar mensajes en una conversacion ajena.")

            selected_role = get_request_role(request)
            if selected_role and not user_matches_conversation_role(request.user, conversation, selected_role):
                raise serializers.ValidationError("El rol seleccionado no participa en esta conversacion.")

        return data

class ConversationSerializer(serializers.ModelSerializer):
    ultimo_mensaje = serializers.SerializerMethodField()
    paciente_info = serializers.SerializerMethodField()
    terapeuta_info = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'paciente',
            'terapeuta',
            'paciente_info',
            'terapeuta_info',
            'created_at',
            'updated_at',
            'ultimo_mensaje',
        ]

    def get_ultimo_mensaje(self, obj):
        ultimo = obj.mensajes.last()
        if ultimo:
            return MessageSerializer(ultimo).data
        return None

    def get_paciente_info(self, obj):
        return self._serialize_user(obj.paciente, ROLE_PACIENTE)

    def get_terapeuta_info(self, obj):
        return self._serialize_user(obj.terapeuta, ROLE_TERAPEUTA)

    def _serialize_user(self, user, role):
        full_name = user.get_full_name().strip()
        data = {
            'id': user.id,
            'username': user.username,
            'nombre_completo': full_name or user.username,
            'email': user.email,
            'role': role,
        }

        if role == ROLE_TERAPEUTA:
            try:
                profile = user.perfil_terapeuta
                data.update({
                    'especialidad': profile.especialidad,
                    'numero_licencia': profile.numero_licencia,
                })
            except TerapeutaProfile.DoesNotExist:
                data.update({'especialidad': '', 'numero_licencia': ''})
        else:
            try:
                profile = user.perfil_paciente
                data.update({
                    'estado': profile.estado,
                    'fecha_nacimiento': profile.fecha_nacimiento,
                    'estrategia_validacion': profile.estrategia_validacion,
                    'estrategia_progreso': profile.estrategia_progreso,
                })
            except PacienteProfile.DoesNotExist:
                data.update({
                    'estado': '',
                    'fecha_nacimiento': None,
                    'estrategia_validacion': '',
                    'estrategia_progreso': '',
                })

        return data

    def validate(self, data):
        paciente = data.get('paciente') or getattr(self.instance, 'paciente', None)
        terapeuta = data.get('terapeuta') or getattr(self.instance, 'terapeuta', None)

        if paciente and terapeuta and paciente == terapeuta:
            raise serializers.ValidationError("Paciente y terapeuta deben ser usuarios distintos.")

        if paciente and not user_has_role(paciente, ROLE_PACIENTE):
            raise serializers.ValidationError({"paciente": "El usuario no tiene rol de paciente."})

        if terapeuta and not user_has_role(terapeuta, ROLE_TERAPEUTA):
            raise serializers.ValidationError({"terapeuta": "El usuario no tiene rol de terapeuta."})

        request = self.context.get('request')
        if request and paciente and terapeuta and not request.user.is_staff:
            selected_role = get_request_role(request)
            if selected_role == ROLE_PACIENTE and paciente.id != request.user.id:
                raise serializers.ValidationError("Como paciente solo puedes crear conversaciones propias.")
            if selected_role == ROLE_TERAPEUTA and terapeuta.id != request.user.id:
                raise serializers.ValidationError("Como terapeuta solo puedes crear conversaciones propias.")
            if not selected_role and request.user.id not in (paciente.id, terapeuta.id):
                raise serializers.ValidationError("Solo puedes crear conversaciones donde participas.")

        return data

class VideoCallSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.ReadOnlyField()

    class Meta:
        model = VideoCall
        fields = [
            'id', 'room_id', 'conversation', 'initiator', 
            'created_at', 'started_at', 'ended_at', 'status', 'duration_minutes'
        ]
        read_only_fields = ['id', 'room_id', 'initiator', 'created_at']
