from rest_framework import serializers
from .models import Usuario
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Usuario con soporte para creación y actualización con encriptación de contraseñas.
    """
    contrasena = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'telefono', 'rol', 'is_active', 'fecha_creacion', 'contrasena']
        read_only_fields = ['id', 'fecha_creacion']  # Campos de solo lectura

    def create(self, datos_validados):
        """
        Crea un usuario con contraseña encriptada.
        """
        contrasena = datos_validados.pop('contrasena')
        usuario = Usuario(**datos_validados)
        usuario.set_password(contrasena)
        usuario.save()
        return usuario

    def update(self, instancia, datos_validados):
        """
        Actualiza los datos del usuario. Si se proporciona una nueva contraseña, se encripta.
        """
        contrasena = datos_validados.pop('contrasena', None)
        for attr, valor in datos_validados.items():
            setattr(instancia, attr, valor)
        if contrasena:
            instancia.set_password(contrasena)
        instancia.save()
        return instancia


class ObtenerTokenPersonalizadoSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para la obtención de tokens JWT con datos adicionales.
    """
    def validate(self, datos):
        datos_validados = super().validate(datos)
        datos_validados['rol'] = self.user.rol
        datos_validados['username'] = self.user.username
        datos_validados['email'] = self.user.email
        return datos_validados


class CambiarContrasenaSerializer(serializers.Serializer):
    """
    Serializer para cambiar la contraseña de un usuario.
    """
    contrasena_actual = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    nueva_contrasena = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})



class DetalleUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar detalles del usuario (lectura).
    """
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'telefono', 'rol', 'is_active', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']  # Aseguramos que sean solo de lectura
