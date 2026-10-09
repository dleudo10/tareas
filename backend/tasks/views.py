from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView

from .authentication import OIDCIntrospectionAuthentication
from .models import Category, Task
from .permissions import get_role_codes, is_task_admin
from .serializers import CategorySerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD de tareas.

    Administrador: consulta todas las tareas.
    Usuario normal: consulta únicamente sus tareas.
    """

    serializer_class = TaskSerializer

    authentication_classes = [
        OIDCIntrospectionAuthentication,
    ]

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = Task.objects.select_related("category")

        if is_task_admin(self.request.auth):
            return queryset

        return queryset.filter(
            owner_sub=self.request.user.id,
        )

    def perform_create(self, serializer):
        user = self.request.user

        serializer.save(
            owner_sub=user.id,
            owner_username=user.username,
        )


class CategoryListView(ListAPIView):
    """
    Devuelve las categorías que el usuario puede utilizar.
    El administrador puede consultar todas las categorías activas.
    """

    serializer_class = CategorySerializer

    authentication_classes = [
        OIDCIntrospectionAuthentication,
    ]

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = Category.objects.filter(
            is_active=True,
        )

        if is_task_admin(self.request.auth):
            return queryset

        role_codes = get_role_codes(self.request.auth)

        return queryset.filter(
            role_assignments__role_code__in=role_codes,
        ).distinct()