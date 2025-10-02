from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def api_homepage(request):
    return Response({"message": "Welcome to the E-commerce API!"})


@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"})
