"""
URL configuration for src project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import include, path

handler404 = "src.core.views.custom_404"
handler403 = "src.core.views.custom_403"
handler500 = "src.core.views.custom_500"

urlpatterns = i18n_patterns(
    path("", include(("src.home.urls", "home"), namespace="home")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("auth/", include(("src.authentication.urls", "authentication"), namespace="authentication")),
    path("offers/", include(("src.offers.urls", "offers"), namespace="offers")),
    path("reservations/", include(("src.reservations.urls", "reservations"), namespace="reservations")),
    path("users/", include(("src.users.urls", "users"), namespace="users")),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
