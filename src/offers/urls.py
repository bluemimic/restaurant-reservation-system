from django.urls import path

from . import views

app_name = "offers"

urlpatterns = [
    path("", views.OfferListView.as_view(), name="list"),
    path("create/", views.OfferCreateView.as_view(), name="create"),
    path("<uuid:id>/", views.OfferDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", views.OfferEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", views.OfferDeleteView.as_view(), name="delete"),
]
