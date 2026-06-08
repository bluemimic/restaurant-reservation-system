from django.shortcuts import redirect
from django.views import View


class IndexView(View):
    def get(self, request, *args, **kwargs):
        return redirect("offers:list")
