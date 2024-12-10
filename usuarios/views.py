from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny ,IsAuthenticated
from rest_framework import serializers

from .models import Usuario
from .serializers import (
    UsuarioSerializer,
    ObtenerTokenPersonalizadoSerializer,
    CambiarContrasenaSerializer,
    DetalleUsuarioSerializer
)


class RegistroUsuarioVista(generics.CreateAPIView):
    """
    Vista para registrar usuarios.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]  # Permitir registro sin autenticación


class InicioSesionVista(TokenObtainPairView):
    """
    Vista para iniciar sesión y obtener el token JWT.
    """
    serializer_class = ObtenerTokenPersonalizadoSerializer
    permission_classes = [AllowAny]  # Permitir el inicio de sesión sin autenticación
    #permission_classes = [IsAuthenticated]

class CambiarContrasenaVista(APIView):
    """
    Vista para cambiar la contraseña de un usuario.
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación

    def post(self, request, *args, **kwargs):
        # Obtener el usuario desde el modelo
        usuario = Usuario.objects.get(username=request.data.get('username'))
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
    Vista para obtener detalles de un usuario.
    para que te muestre el detalle manda la info ?id=1
    """
    serializer_class = DetalleUsuarioSerializer
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación

    def get_object(self):
        """
        Retorna un usuario basado en el parámetro 'id' proporcionado en la solicitud.
        """
        user_id = self.request.query_params.get('id')  # Obtener el 'id' desde los parámetros de la consulta
        if not user_id:
            raise serializers.ValidationError({"detalle": "El parámetro 'id' es requerido."})
        try:
            return Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({"detalle": "El usuario con este 'id' no existe."})




class ListaUsuariosVista(generics.ListAPIView):
    """
    Vista para listar todos los usuarios.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación

    def get_queryset(self):
        """
        Retorna todos los usuarios.
        """
        return super().get_queryset()
