from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from RehabWeb_API.models import PacienteProfile, TerapeutaProfile
from RehabWeb_API.roles import ROLE_PACIENTE, ROLE_TERAPEUTA
from RehabWeb_API.serializers import AccountSerializer
from mensajeria.models import Conversation


class RoleAccountListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, role):
        role = self._normalize_role(role)
        users = self._role_users(role)
        serializer = AccountSerializer(users, many=True, context={'role': role})
        return Response(serializer.data)

    def post(self, request, role):
        role = self._normalize_role(role)
        serializer = AccountSerializer(data=request.data, context={'role': role})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(AccountSerializer(user, context={'role': role}).data, status=status.HTTP_201_CREATED)

    def _normalize_role(self, role):
        return ROLE_TERAPEUTA if role in ('terapeutas', 'terapeuta') else ROLE_PACIENTE

    def _role_users(self, role):
        if role == ROLE_TERAPEUTA:
            ids = set(TerapeutaProfile.objects.values_list('usuario_id', flat=True))
            ids.update(User.objects.filter(groups__name__iexact='Terapeuta').values_list('id', flat=True))
            ids.update(Conversation.objects.values_list('terapeuta_id', flat=True))
        else:
            ids = set(PacienteProfile.objects.values_list('usuario_id', flat=True))
            ids.update(User.objects.filter(groups__name__iexact='Paciente').values_list('id', flat=True))
            ids.update(Conversation.objects.values_list('paciente_id', flat=True))

        return User.objects.filter(id__in=ids).order_by('first_name', 'username').distinct()


class RoleAccountDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, role, pk):
        role = self._normalize_role(role)
        user = self._get_user(role, pk)
        return Response(AccountSerializer(user, context={'role': role}).data)

    def patch(self, request, role, pk):
        role = self._normalize_role(role)
        user = self._get_user(role, pk)
        serializer = AccountSerializer(user, data=request.data, partial=True, context={'role': role})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(AccountSerializer(user, context={'role': role}).data)

    def delete(self, request, role, pk):
        user = self._get_user(self._normalize_role(role), pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _normalize_role(self, role):
        return ROLE_TERAPEUTA if role in ('terapeutas', 'terapeuta') else ROLE_PACIENTE

    def _get_user(self, role, pk):
        queryset = User.objects.all()
        if role == ROLE_TERAPEUTA:
            queryset = queryset.filter(
                Q(groups__name__iexact='Terapeuta') |
                Q(perfil_terapeuta__isnull=False) |
                Q(conversaciones_como_terapeuta__isnull=False)
            )
        else:
            queryset = queryset.filter(
                Q(groups__name__iexact='Paciente') |
                Q(perfil_paciente__isnull=False) |
                Q(conversaciones_como_paciente__isnull=False)
            )
        return get_object_or_404(queryset.distinct(), pk=pk)
