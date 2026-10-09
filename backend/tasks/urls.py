from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryListView, TaskViewSet


router = DefaultRouter()

router.register(
    "tasks",
    TaskViewSet,
    basename="task",
)


urlpatterns = [
    path(
        "categories/",
        CategoryListView.as_view(),
        name="category-list",
    ),

    path(
        "",
        include(router.urls),
    ),
]