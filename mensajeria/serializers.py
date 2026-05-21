from rest_framework import serializers
from .models import Conversation, Message, VideoCall

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
        return data

class ConversationSerializer(serializers.ModelSerializer):
    ultimo_mensaje = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'paciente', 'terapeuta', 'created_at', 'updated_at', 'ultimo_mensaje']

    def get_ultimo_mensaje(self, obj):
        ultimo = obj.mensajes.last()
        if ultimo:
            return MessageSerializer(ultimo).data
        return None

class VideoCallSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.ReadOnlyField()

    class Meta:
        model = VideoCall
        fields = [
            'id', 'room_id', 'conversation', 'initiator', 
            'created_at', 'started_at', 'ended_at', 'status', 'duration_minutes'
        ]
        read_only_fields = ['id', 'room_id', 'initiator', 'created_at']