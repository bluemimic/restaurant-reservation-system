from django.urls import path

from src.users.views import (
    UserCreateView,
    UserDeleteView,
    UserDetailView,
    UserEditView,
    UserListView,
)

app_name = "users"

urlpatterns = [
    path("create/", UserCreateView.as_view(), name="create"),
    path("list/", UserListView.as_view(), name="list"),
    path("<uuid:id>/", UserDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", UserEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", UserDeleteView.as_view(), name="delete"),
]
