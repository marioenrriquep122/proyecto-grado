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




class UsuarioRegistroVista(generics.CreateAPIView):
    """
    Vista para registrar nuevos usuarios.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]  


class UsuarioLoginVista(TokenObtainPairView):
    """
    Vista para obtener el token JWT (inicio de sesión).
    """
    serializer_class = ObtenerTokenPersonalizadoSerializer
    permission_classes = [AllowAny] 



from django.contrib.auth.models import User

class UsuarioCambiarContrasenaVista(APIView):
    """
    Vista para cambiar la contraseña de un usuario por ID.
    """
    permission_classes = [AllowAny]  

    def post(self, request):
        
        user_id = request.query_params.get('id')
        if not user_id:
            return Response(
                {"detalle": "El parámetro 'id' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

       
        try:
            usuario = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detalle": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

       
        serializer = CambiarContrasenaSerializer(data=request.data)
        if serializer.is_valid():
            
            if not request.user.check_password(serializer.validated_data['contrasena_actual']):
                return Response(
                    {"detalle": "Contraseña actual incorrecta."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            usuario.set_password(serializer.validated_data['nueva_contrasena'])
            usuario.save()
            return Response(
                {"detalle": "Contraseña actualizada correctamente."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioDetalleVista(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para obtener, actualizar o eliminar un usuario específico.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]


    
    
    
    
    

