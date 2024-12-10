from django.urls import path
from usuarios.views import (
    RegistroUsuarioVista,
    InicioSesionVista,
    CambiarContrasenaVista,
    DetalleUsuarioVista,
    ListaUsuariosVista,
)


urlpatterns = [
    path('registro/', RegistroUsuarioVista.as_view(), name='registro-usuario'),
    path('login/', InicioSesionVista.as_view(), name='inicio-sesion'),
    path('cambiar-contrasena/', CambiarContrasenaVista.as_view(), name='cambiar-contrasena'),
    path('perfil/', DetalleUsuarioVista.as_view(), name='detalle-usuario'),
    path('usuarios/', ListaUsuariosVista.as_view(), name='lista-usuarios'),
]
