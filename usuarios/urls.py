from django.urls import path, include
from .views import (
    UsuarioViewSet,
    UsuarioRegistroVista,
    UsuarioLoginVista,
    UsuarioCambiarContrasenaVista,
    UsuarioDetalleVista,
)
from .routers import CustomRouter  # Importa el router personalizado

# Instancia del router personalizado
router = CustomRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')

# Configuración de las URLs
urlpatterns = [
    path('', include(router.urls)),  # Incluye las rutas generadas automáticamente y la vista raíz personalizada
    path('registro/', UsuarioRegistroVista.as_view(), name='usuario-registro'),  # Registro de usuarios
    path('login/', UsuarioLoginVista.as_view(), name='usuario-login'),  # Inicio de sesión
    path('cambiar-contrasena/', UsuarioCambiarContrasenaVista.as_view(), name='usuario-cambiar-contrasena'),  # Cambio de contraseña
    path('perfil/<int:pk>/', UsuarioDetalleVista.as_view(), name='usuario-detalle'),  # Detalle de un usuario específico
]
