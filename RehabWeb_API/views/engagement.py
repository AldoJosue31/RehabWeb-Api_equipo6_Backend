from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from RehabWeb_API.models import Alert, ExerciseSession, MotivationProfile, PatientBadge, WeeklySummary
from RehabWeb_API.permissions import HasSelectedRole
from RehabWeb_API.roles import ROLE_PACIENTE, ROLE_TERAPEUTA, get_request_role
from RehabWeb_API.serializers import (
    AlertSerializer,
    ExerciseSessionSerializer,
    LeaderboardEntrySerializer,
    MotivationProfileSerializer,
    PatientBadgeSerializer,
    WeeklySummarySerializer,
)
from RehabWeb_API.services import build_weekly_summary, detect_inactivity_alerts, leaderboard_top10


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get_queryset(self):
        user = self.request.user
        selected_role = get_request_role(self.request)
        queryset = Alert.objects.select_related('paciente', 'terapeuta', 'source_session')
        if selected_role == ROLE_PACIENTE:
            return queryset.filter(paciente=user)
        if selected_role == ROLE_TERAPEUTA:
            return queryset.filter(terapeuta=user)
        return queryset.filter(Q(paciente=user) | Q(terapeuta=user))

    @action(detail=True, methods=['patch'])
    def marcar_revisada(self, request, pk=None):
        alert = self.get_object()
        alert.status = Alert.STATUS_REVIEWED
        alert.reviewed_at = timezone.now()
        alert.save(update_fields=['status', 'reviewed_at'])
        return Response(self.get_serializer(alert).data)

    @action(detail=True, methods=['patch'])
    def resolver(self, request, pk=None):
        alert = self.get_object()
        alert.status = Alert.STATUS_RESOLVED
        alert.resolved_at = timezone.now()
        if not alert.reviewed_at:
            alert.reviewed_at = alert.resolved_at
        alert.save(update_fields=['status', 'reviewed_at', 'resolved_at'])
        return Response(self.get_serializer(alert).data)

    @action(detail=False, methods=['post'])
    def generar_inactividad(self, request):
        selected_role = get_request_role(request)
        if selected_role != ROLE_TERAPEUTA and not request.user.is_staff:
            return Response(
                {'error': 'Solo terapeutas pueden ejecutar la deteccion de inactividad.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        generated = detect_inactivity_alerts()
        return Response({'generadas': generated})


class ExerciseSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSessionSerializer
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get_queryset(self):
        user = self.request.user
        selected_role = get_request_role(self.request)
        queryset = ExerciseSession.objects.select_related('paciente', 'terapeuta')
        if selected_role == ROLE_PACIENTE:
            return queryset.filter(paciente=user)
        if selected_role == ROLE_TERAPEUTA:
            return queryset.filter(terapeuta=user)
        return queryset.filter(Q(paciente=user) | Q(terapeuta=user))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['role'] = get_request_role(self.request)
        return context


class MotivationProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get_object(self, request):
        profile, _ = MotivationProfile.objects.get_or_create(usuario=request.user)
        return profile

    def get(self, request):
        serializer = MotivationProfileSerializer(self.get_object(request))
        return Response(serializer.data)

    def patch(self, request):
        serializer = MotivationProfileSerializer(
            self.get_object(request),
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PatientBadgeListView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get(self, request):
        selected_role = get_request_role(request)
        user_id = request.query_params.get('paciente')
        user = request.user
        if selected_role == ROLE_TERAPEUTA and user_id:
            user = get_object_or_404(ExerciseSession.objects.filter(terapeuta=request.user), paciente_id=user_id).paciente
        badges = PatientBadge.objects.filter(usuario=user)
        return Response(PatientBadgeSerializer(badges, many=True).data)


class WeeklySummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get(self, request):
        selected_role = get_request_role(request)
        patient = request.user
        patient_id = request.query_params.get('paciente')
        if selected_role == ROLE_TERAPEUTA and patient_id:
            session = get_object_or_404(ExerciseSession.objects.filter(terapeuta=request.user), paciente_id=patient_id)
            patient = session.paciente

        summary = build_weekly_summary(patient)
        return Response(WeeklySummarySerializer(summary).data)


class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasSelectedRole]

    def get(self, request):
        entries = leaderboard_top10()
        return Response(LeaderboardEntrySerializer(entries, many=True).data)
