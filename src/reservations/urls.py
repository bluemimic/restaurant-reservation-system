from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.ReservationListView.as_view(), name="list"),
    path("create/", views.ReservationCreateView.as_view(), name="create"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/checkout/", views.CartCheckoutView.as_view(), name="cart_checkout"),
    path("cart/add/<uuid:id>/", views.CartAddView.as_view(), name="cart_add"),
    path("cart/remove/<uuid:id>/", views.CartRemoveView.as_view(), name="cart_remove"),
    path("cart/update/<uuid:id>/", views.CartUpdateView.as_view(), name="cart_update"),
    path("<uuid:id>/", views.ReservationDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", views.ReservationEditView.as_view(), name="edit"),
    path("<uuid:id>/status/", views.ReservationStatusView.as_view(), name="status"),
    path("<uuid:id>/delete/", views.ReservationDeleteView.as_view(), name="delete"),
]
