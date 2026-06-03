from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.ReservationListView.as_view(), name="list"),
    path("create/", views.ReservationCreateView.as_view(), name="create"),
    path("<uuid:id>/", views.ReservationDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", views.ReservationEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", views.ReservationDeleteView.as_view(), name="delete"),
]
