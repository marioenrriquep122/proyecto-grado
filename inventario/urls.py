from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ActividadViewSet,
    CategoriaViewSet,
    EquipoMaterialViewSet,
    ReporteViewSet,
    FacturaViewSet,
    ResumenView
)

# Configuración del enrutador de DRF
router = DefaultRouter()
router.register('categorias', CategoriaViewSet, basename='categorias')
router.register('productos', EquipoMaterialViewSet, basename='productos')
router.register('reportes', ReporteViewSet, basename='reportes')
router.register('facturas', FacturaViewSet, basename='facturas')
router.register('actividades', ActividadViewSet, basename='actividades')

# Agregar rutas personalizadas
urlpatterns = [
    path('', include(router.urls)),  # Incluye todas las rutas generadas por el router
    path('resumen/', ResumenView.as_view(), name='resumen'),  # Ruta personalizada para el resumen
]
