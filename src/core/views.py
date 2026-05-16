from django.shortcuts import render


def custom_404(request, exception):
    return render(request, "core/404.html", status=404)


def custom_500(request):
    return render(request, "core/500.html", status=500)


def custom_403(request, exception):
    return render(request, "core/403.html", status=403)
