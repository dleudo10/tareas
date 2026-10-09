from django.contrib import admin

from .models import Category, CategoryRole, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
    )

    list_filter = (
        "is_active",
    )


@admin.register(CategoryRole)
class CategoryRoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "category",
        "role_code",
        "created_at",
    )

    list_filter = (
        "category",
        "role_code",
    )

    search_fields = (
        "category__name",
        "role_code",
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "owner_username",
        "category",
        "status",
        "created_at",
    )

    search_fields = (
        "title",
        "owner_username",
        "owner_sub",
    )

    list_filter = (
        "status",
        "category",
    )

    readonly_fields = (
        "owner_sub",
        "owner_username",
        "created_at",
        "updated_at",
    )