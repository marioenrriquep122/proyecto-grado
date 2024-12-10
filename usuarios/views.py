from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Usuario
from .serializers import (
    UsuarioSerializer,
    ObtenerTokenPersonalizadoSerializer,
    CambiarContrasenaSerializer
)


class RegistroUsuarioVista(generics.CreateAPIView):
    """
    Vista para registrar usuarios.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer


class InicioSesionVista(TokenObtainPairView):
    """
    Vista para iniciar sesión y obtener el token JWT.
    """
    serializer_class = ObtenerTokenPersonalizadoSerializer


class CambiarContrasenaVista(APIView):
    """
    Vista para cambiar la contraseña de un usuario autenticado.
    """
    def post(self, request, *args, **kwargs):
        usuario = request.user
        serializer = CambiarContrasenaSerializer(data=request.data)
        if serializer.is_valid():
            # Verifica la contraseña actual
            if not usuario.check_password(serializer.validated_data['contrasena_actual']):
                return Response(
                    {"detalle": "Contraseña actual incorrecta"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Cambia la contraseña
            usuario.set_password(serializer.validated_data['nueva_contrasena'])
            usuario.save()
            return Response(
                {"detalle": "Contraseña actualizada correctamente"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DetalleUsuarioVista(generics.RetrieveAPIView):
    """
    Vista para obtener detalles de un usuario autenticado.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_object(self):
        """
        Retorna el usuario autenticado.
        """
        return self.request.user


class ListaUsuariosVista(generics.ListAPIView):
    """
    Vista para listar todos los usuarios (Solo para administradores).
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
