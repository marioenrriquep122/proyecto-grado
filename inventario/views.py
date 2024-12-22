import datetime
import csv

from django.db import models  
from django.db.models import Count, Sum, F, Q
from django.http import HttpResponse
from django.utils.timezone import now

from usuarios.models import Usuario
from .models import Categoria, EquipoMaterial,  Reporte, Factura, Actividad, Factura
from .serializers import ActividadSerializer, CategoriaSerializer, EquipoMaterialSerializer, ReporteSerializer, FacturaSerializer

from rest_framework import viewsets,status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .serializers import ReporteSerializer



# --- Categoría ---
class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de Categorías.
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (puedes cambiar esto según necesidad)


# --- EquipoMaterial  que es producto---
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
    ViewSet para gestionar el CRUD de Reportes y generar datos dinámicos.
    """
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer

    def create(self, request, *args, **kwargs):
        """
        Crear un reporte y devolver los datos generados dinámicamente.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        reporte = serializer.instance

        # Generar los datos dinámicos basados en el filtro del reporte
        datos = self.generar_datos(reporte.filtro, reporte.fecha_inicio, reporte.fecha_fin)

        # Incluir los datos generados en la respuesta
        response_data = serializer.data
        response_data["datos"] = datos
        return Response(response_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        Recuperar un reporte e incluir los datos generados dinámicamente.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Generar datos dinámicos basados en el filtro
        datos = self.generar_datos(instance.filtro, instance.fecha_inicio, instance.fecha_fin)

        # Incluir los datos generados en la respuesta
        response_data = serializer.data
        response_data["datos"] = datos
        return Response(response_data)

    def update(self, request, *args, **kwargs):
        """
        Actualizar un reporte y regenerar los datos dinámicos.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Regenerar los datos dinámicos
        datos = self.generar_datos(instance.filtro, instance.fecha_inicio, instance.fecha_fin)

        # Incluir los datos generados en la respuesta
        response_data = serializer.data
        response_data["datos"] = datos
        return Response(response_data)

    def partial_update(self, request, *args, **kwargs):
        """
        Actualizar parcialmente un reporte y regenerar los datos dinámicos.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Personaliza la respuesta al eliminar un reporte.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": f"El reporte con ID {instance.id} fue eliminado exitosamente."},
            status=status.HTTP_200_OK
        )

    def generar_datos(self, filtro, fecha_inicio, fecha_fin):
        """
        Generar datos dinámicos según el filtro seleccionado.
        """
        if filtro == "facturas":
            facturas = Factura.objects.all()
            if fecha_inicio and fecha_fin:
                facturas = facturas.filter(fecha_salida__range=[fecha_inicio, fecha_fin])
            return list(facturas.values("id", "producto__equipo", "cantidad", "fecha_salida", "numero_factura"))

        elif filtro == "productos":
            productos = EquipoMaterial.objects.all()
            if fecha_inicio and fecha_fin:
                productos = productos.filter(fecha_entrada__range=[fecha_inicio, fecha_fin])
            return list(productos.values("id", "equipo", "marca", "serial", "cantidad", "estado", "categoria__nombre"))

        elif filtro == "categorias":
            categorias = Categoria.objects.all()
            return list(categorias.values("id", "nombre", "descripcion"))

        elif filtro == "usuarios":
            usuarios = Usuario.objects.all()  # Usa tu modelo personalizado
            if fecha_inicio and fecha_fin:
                usuarios = usuarios.filter(fecha_creacion__range=[fecha_inicio, fecha_fin])
            return list(usuarios.values("id", "username", "email", "telefono", "rol", "is_active", "fecha_creacion"))

        return []


# --- Factura ---
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






# --- Actividad ---
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
                    f"Se agrego una nueva factura con el numero : {factura.numero_factura}. "
                    
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
    
    
    





# --- Resumen ---
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

        total_categorias = Categoria.objects.count()
        total_productos = EquipoMaterial.objects.count()
        total_facturas = Factura.objects.count()
        total_actividades = Actividad.objects.count()
        stock_total = EquipoMaterial.objects.aggregate(total_stock=Sum('cantidad'))['total_stock'] or 0
        ventas_totales = Factura.objects.aggregate(
            total_ventas=Sum(F('cantidad') * F('producto__valor'))
        )['total_ventas'] or 0
        facturas_del_dia = Factura.objects.filter(fecha_salida=fecha_seleccionada).count()
        total_del_dia = Factura.objects.filter(fecha_salida=fecha_seleccionada).aggregate(
            total_dia=Sum(F('cantidad') * F('producto__valor'))
        )['total_dia'] or 0

       
        resumen = {
            "fecha_seleccionada": str(fecha_seleccionada),
            "total_categorias": total_categorias,
            "total_productos": total_productos,
            "total_facturas": total_facturas,
            "total_actividades": total_actividades,
            "stock_total_disponible": stock_total,
            "ventas_totales": ventas_totales,
            "facturas_del_dia": facturas_del_dia,
            "total_del_dia": total_del_dia,  
        }

        return Response(resumen)


