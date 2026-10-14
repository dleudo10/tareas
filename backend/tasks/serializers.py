from rest_framework import serializers
from .permissions import is_task_admin 
from .models import Category, Task


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
        ]


class TaskSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    owner_username = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "category",
            "category_name",
            "owner_username",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "owner_username",
            "created_at",
            "updated_at",
        ]

    def validate_category(self, category):
        claims = self.context["request"].auth

        if is_task_admin(claims):
            return category

        roles = claims.get("roles", [])
        if isinstance(roles, str):
            roles = [roles]

        permitted = category.role_assignments.filter(role_code__in=roles).exists()
        if not permitted:
            raise serializers.ValidationError(
                "No tienes permiso para utilizar esta categoría."
            )
        return category