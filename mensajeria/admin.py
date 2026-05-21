from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    # Columnas en la tabla principal
    list_display = ('id', 'paciente', 'terapeuta', 'created_at', 'updated_at')
    
    # Filtros laterales por fechas
    list_filter = ('created_at', 'updated_at')
    
    # Buscador por nombres de usuario de paciente o terapeuta
    search_fields = ('paciente__username', 'terapeuta__username')
    
    # Orden predeterminado (más actualizados arriba)
    ordering = ('-updated_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    # Columnas principales
    list_display = ('id', 'conversation', 'sender', 'timestamp', 'status')
    
    # Filtros por estado y fecha
    list_filter = ('status', 'timestamp')
    
    # Búsqueda por texto del mensaje o por usuario
    search_fields = ('encrypted_text', 'sender__username')
    
    # Orden cronológico descendente
    ordering = ('-timestamp',)