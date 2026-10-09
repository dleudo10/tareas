from django.db import models


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "task_categories"
        ordering = ["name"]
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.name


class CategoryRole(models.Model):
    """
    Relaciona una categoría con los roles de TaskFlow
    autorizados para utilizarla.

    role_code corresponde al código estable del rol
    configurado en OLIMPO para TaskFlow.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )

    role_code = models.SlugField(
        max_length=50,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "task_category_roles"

        constraints = [
            models.UniqueConstraint(
                fields=["category", "role_code"],
                name="unique_category_role",
            ),
        ]

        verbose_name = "Rol de categoría"
        verbose_name_plural = "Roles de categorías"

    def __str__(self):
        return f"{self.category.name} - {self.role_code}"


class Task(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En progreso"
        COMPLETED = "COMPLETED", "Completada"

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tasks",
    )

    # Identidad del propietario procedente de OLIMPO.
    # No es un ID proporcionado por el formulario.
    owner_sub = models.CharField(
        max_length=255,
        db_index=True,
    )

    owner_username = models.CharField(
        max_length=150,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"

        indexes = [
            models.Index(
                fields=["owner_sub", "status"],
                name="task_owner_status_idx",
            ),
        ]

    def __str__(self):
        return self.title