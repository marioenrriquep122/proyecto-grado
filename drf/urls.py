from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Rutas para el panel de administración
    path('api/usuarios/', include('usuarios.urls')),  # Rutas de la aplicación "usuarios"
    path('api/inventario/', include('inventario.urls')),  # Rutas de la aplicación "inventario"
]
