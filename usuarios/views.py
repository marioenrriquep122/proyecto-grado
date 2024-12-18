from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from .models import Usuario
from .serializers import (
    UsuarioSerializer,
    ObtenerTokenPersonalizadoSerializer,
    CambiarContrasenaSerializer,
    DetalleUsuarioSerializer,
)

from django.urls import reverse

from rest_framework import viewsets
from .models import Usuario
from .serializers import UsuarioSerializer
from rest_framework.permissions import IsAuthenticated

class UsuarioViewSet(viewsets.ModelViewSet):
    """
    Vista para manejar todas las operaciones CRUD de usuarios.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]



# 1. Registro de usuarios (POST)
class UsuarioRegistroVista(generics.CreateAPIView):
    """
    Vista para registrar nuevos usuarios.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]  # Permite acceso sin autenticación

# 2. Inicio de sesión (Token JWT)
class UsuarioLoginVista(TokenObtainPairView):
    """
    Vista para obtener el token JWT (inicio de sesión).
    """
    serializer_class = ObtenerTokenPersonalizadoSerializer
    permission_classes = [AllowAny]  # Permite acceso sin autenticación

# 3. Cambiar contraseña (POST)
class UsuarioCambiarContrasenaVista(APIView):
    """
    Vista para cambiar la contraseña de un usuario.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        usuario = request.user
        serializer = CambiarContrasenaSerializer(data=request.data)
        if serializer.is_valid():
            if not usuario.check_password(serializer.validated_data['contrasena_actual']):
                return Response(
                    {"detalle": "Contraseña actual incorrecta"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            usuario.set_password(serializer.validated_data['nueva_contrasena'])
            usuario.save()
            return Response(
                {"detalle": "Contraseña actualizada correctamente"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 4. Detalle de usuario por parámetro de URL (GET, PUT, PATCH, DELETE)
class UsuarioDetalleVista(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para obtener, actualizar o eliminar un usuario específico.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]


    
    
    
    
    

