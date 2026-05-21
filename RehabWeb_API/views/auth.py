from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework import status

from RehabWeb_API.roles import get_user_roles, normalize_role


class AuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        roles = sorted(get_user_roles(user))
        requested_role = normalize_role(request.data.get('role') or request.data.get('rol'))

        if requested_role and requested_role not in roles:
            return Response({
                'detail': 'El usuario no tiene permiso para acceder con ese rol.',
                'roles_disponibles': roles,
            }, status=status.HTTP_403_FORBIDDEN)

        token, _ = Token.objects.get_or_create(user=user)
        selected_role = requested_role or (roles[0] if len(roles) == 1 else None)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.get_username(),
            'role': selected_role,
            'roles': roles,
        })
