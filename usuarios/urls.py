from django.urls import path, include
from .views import (
    UsuarioViewSet,
    UsuarioRegistroVista,
    UsuarioLoginVista,
    UsuarioCambiarContrasenaVista,
    UsuarioDetalleVista,
)
from .routers import CustomRouter  


router = CustomRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')


urlpatterns = [
    path('', include(router.urls)),  
    path('registro/', UsuarioRegistroVista.as_view(), name='usuario-registro'),  
    path('login/', UsuarioLoginVista.as_view(), name='usuario-login'),  
    path('cambiar-contrasena/', UsuarioCambiarContrasenaVista.as_view(), name='usuario-cambiar-contrasena'),  
    path('perfil/<int:pk>/', UsuarioDetalleVista.as_view(), name='usuario-detalle'),  
]
