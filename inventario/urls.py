from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, EquipoMaterialViewSet, ReporteViewSet,FacturaViewSet

# Configuración del enrutador de DRF
router = DefaultRouter()
router.register('categorias', CategoriaViewSet, basename='categorias')
router.register('productos', EquipoMaterialViewSet, basename='productos')
router.register('reportes', ReporteViewSet, basename='reportes')
router.register('facturas', FacturaViewSet, basename='facturas')

urlpatterns = [
    path('', include(router.urls)),  # Incluye todas las rutas generadas por el router
]
