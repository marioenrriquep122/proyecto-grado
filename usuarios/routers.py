from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import reverse

class CustomRouter(DefaultRouter):
    """
    Router personalizado que agrega rutas adicionales a la vista raíz.
    """
    def get_api_root_view(self, api_urls=None):
        """
        Personaliza la vista raíz del API.
        """
        root_view = super().get_api_root_view(api_urls=api_urls)

        class CustomAPIRootView(APIView):
            """
            Vista raíz personalizada para incluir rutas adicionales.
            """
            def get(self, request, *args, **kwargs):
                # Incluye rutas del router automáticamente
                response_data = {
                    "usuarios": request.build_absolute_uri(reverse('usuario-list')),  # Del ViewSet
                    "registro": request.build_absolute_uri(reverse('usuario-registro')),
                    "login": request.build_absolute_uri(reverse('usuario-login')),
                    "cambiar_contrasena": request.build_absolute_uri(reverse('usuario-cambiar-contrasena')),
                }
                return Response(response_data)

        return CustomAPIRootView.as_view()
