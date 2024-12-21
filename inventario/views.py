import datetime
from django.db import models  # Import necesario para usar F en las consultas dinámicas
from rest_framework import viewsets,status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
import csv


from django.db.models import Count, Sum, F, Q
from rest_framework.views import APIView

from .models import Categoria, EquipoMaterial,  Reporte, Factura, Actividad
from .serializers import ActividadSerializer, CategoriaSerializer, EquipoMaterialSerializer, ReporteSerializer, FacturaSerializer


# --- Categoría ---
class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de Categorías.
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (puedes cambiar esto según necesidad)


# --- EquipoMaterial ---
class EquipoMaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de Equipos y Materiales.
    Incluye validaciones y funciones personalizadas.
    """
    queryset = EquipoMaterial.objects.all()
    serializer_class = EquipoMaterialSerializer
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (puedes ajustar esto)

    def create(self, request, *args, **kwargs):
        """
        Validación personalizada al crear un nuevo equipo/material.
        Verifica que el stock inicial no sea menor que el stock mínimo.
        """
        stock = request.data.get('stock')
        stock_minimo = request.data.get('stock_minimo')
        
        if stock and stock_minimo and int(stock) < int(stock_minimo):
            raise ValidationError("El stock inicial no puede ser menor que el stock mínimo.")

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def bajo_stock(self, request):
        """
        Retorna una lista de productos con stock menor o igual al stock mínimo.
        """
        items = self.queryset.filter(stock__lte=models.F('stock_minimo'))
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def reporte_bajo_stock(self, request):
        """
        Genera un reporte en CSV de productos con bajo stock.
        """
        items = self.queryset.filter(stock__lte=models.F('stock_minimo'))

        # Crear archivo CSV para la respuesta
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_bajo_stock.csv"'

        writer = csv.writer(response)
        writer.writerow(['Nombre', 'Descripción', 'Stock', 'Stock Mínimo'])
        for item in items:
            writer.writerow([item.nombre, item.descripcion, item.stock, item.stock_minimo])

        return response
    
    
    





# --- Reporte ---
class ReporteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de Reportes.
    """
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (puedes ajustar esto)








class FacturaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de facturas.
    """
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer

    def create(self, request, *args, **kwargs):
        """
        Al crear una factura, registra una actividad con una descripción detallada.
        """
        response = super().create(request, *args, **kwargs)
        factura = Factura.objects.get(id=response.data['id'])
        producto = factura.producto

        # Validar producto
        if not producto:
            raise ValidationError("La factura no tiene un producto asociado.")

        # Calcular total
        total = factura.cantidad * producto.valor

        # Generar descripción mejorada
        descripcion = (
            f"Factura {factura.numero_factura} creada para la venta de {producto.equipo}. "
            f"Cantidad: {factura.cantidad} unidades. Total: ${total:.2f}."
        )

        # Registrar actividad
        Actividad.objects.create(
            tipo='venta',
            factura=factura,
            descripcion=descripcion
        )
        return response

    def update(self, request, *args, **kwargs):
        """
        Al actualizar una factura, registra una actividad con una descripción detallada.
        """
        response = super().update(request, *args, **kwargs)
        factura = self.get_object()
        producto = factura.producto

        # Validar producto
        if not producto:
            raise ValidationError("La factura no tiene un producto asociado.")

        # Calcular total
        total = factura.cantidad * producto.valor

        # Generar descripción mejorada
        descripcion = (
            f"Factura {factura.numero_factura} actualizada. Producto: {producto.equipo}, "
            f"Cantidad: {factura.cantidad} unidades, Total: ${total:.2f}. "
            f"Estado actual: {producto.estado}."
        )

        # Registrar actividad
        Actividad.objects.create(
            tipo='factura',
            factura=factura,
            descripcion=descripcion
        )
        return response







class ActividadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de actividades.
    """
    queryset = Actividad.objects.all().order_by('-fecha')
    serializer_class = ActividadSerializer

    def create(self, request, *args, **kwargs):
        """
        Sobreescribe el método create para generar una descripción detallada si no se proporciona.
        """
        # Crear una copia mutable de los datos
        data = request.data.copy()

        # Obtener datos del request
        tipo = data.get('tipo', 'otro')
        factura_id = data.get('factura')
        descripcion = data.get('descripcion', '').strip()

        # Generar descripción mejorada automáticamente si está vacía
        if not descripcion:
            factura = Factura.objects.filter(id=factura_id).first()
            if factura:
                descripcion = (
                    f"Actividad de tipo '{tipo}' realizada. Factura: {factura.numero_factura}. "
                    f"Producto: {factura.producto.equipo}, Cantidad: {factura.cantidad} unidades, "
                    f"Total: ${factura.cantidad * factura.producto.valor:.2f}."
                )
            else:
                descripcion = f"Actividad de tipo '{tipo}' registrada sin una factura específica."

        # Actualizar la descripción en los datos
        data['descripcion'] = descripcion

        # Crear la actividad usando los datos modificados
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
    




from django.db.models import Count, Sum, F
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Categoria, EquipoMaterial, Factura, Actividad

class ResumenView(APIView):
    """
    Vista para consolidar las estadísticas del sistema.
    """
    def get(self, request, *args, **kwargs):
        # Obtener la fecha desde los parámetros o usar la fecha actual
        fecha_param = request.query_params.get('fecha', None)
        if fecha_param:
            try:
                fecha_seleccionada = datetime.strptime(fecha_param, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Fecha inválida. Use el formato YYYY-MM-DD."}, status=400)
        else:
            fecha_seleccionada = now().date()

        # 1. Total de categorías
        total_categorias = Categoria.objects.count()

        # 2. Total de productos
        total_productos = EquipoMaterial.objects.count()

        # 3. Total de facturas
        total_facturas = Factura.objects.count()

        # 4. Total de actividades
        total_actividades = Actividad.objects.count()

        # 5. Stock total disponible
        stock_total = EquipoMaterial.objects.aggregate(total_stock=Sum('cantidad'))['total_stock'] or 0

        # 6. Ventas totales (suma de cantidad * valor de todas las facturas)
        ventas_totales = Factura.objects.aggregate(
            total_ventas=Sum(F('cantidad') * F('producto__valor'))
        )['total_ventas'] or 0

        # 7. Facturas del día (filtrar por fecha seleccionada)
        facturas_del_dia = Factura.objects.filter(fecha_salida=fecha_seleccionada).count()

        # Construir la respuesta JSON
        resumen = {
            "fecha_seleccionada": str(fecha_seleccionada),
            "total_categorias": total_categorias,
            "total_productos": total_productos,
            "total_facturas": total_facturas,
            "total_actividades": total_actividades,
            "stock_total_disponible": stock_total,
            "ventas_totales": ventas_totales,
            "facturas_del_dia": facturas_del_dia,
        }

        return Response(resumen)


