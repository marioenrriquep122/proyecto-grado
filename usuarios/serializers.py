from rest_framework import serializers
from .models import Usuario
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo de Usuario con encriptación de contraseñas.
    """
    contrasena = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'telefono', 'rol', 'is_active', 'contrasena']
        extra_kwargs = {
            'contrasena': {'write_only': True},  # Oculta la contraseña al leer los datos
        }

    def create(self, datos_validados):
        """
        Crea un usuario con contraseña encriptada.
        """
        contrasena = datos_validados.pop('contrasena')
        usuario = Usuario.objects.create(**datos_validados)
        usuario.set_password(contrasena)  # Encripta la contraseña antes de guardarla
        usuario.save()
        return usuario

    def update(self, instancia, datos_validados):
        """
        Actualiza los datos del usuario, encriptando la contraseña si es proporcionada.
        """
        contrasena = datos_validados.pop('contrasena', None)
        for attr, valor in datos_validados.items():
            setattr(instancia, attr, valor)
        if contrasena:
            instancia.set_password(contrasena)  # Encripta la nueva contraseña
        instancia.save()
        return instancia


class ObtenerTokenPersonalizadoSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para la obtención de tokens JWT con datos adicionales.
    """
    def validate(self, atributos):
        datos = super().validate(atributos)
        datos['rol'] = self.user.rol
        datos['username'] = self.user.username
        return datos


class CambiarContrasenaSerializer(serializers.Serializer):
    """
    Serializer para cambiar la contraseña de un usuario.
    """
    contrasena_actual = serializers.CharField(required=True)
    nueva_contrasena = serializers.CharField(required=True)


class DetalleUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar detalles del usuario (lectura).
    """
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'telefono', 'rol', 'is_active', 'fecha_creacion']
        
