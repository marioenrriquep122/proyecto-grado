from django.db import models  # Import necesario para usar F en las consultas dinámicas
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
import csv

from .models import Categoria, EquipoMaterial,  Reporte, Factura
from .serializers import CategoriaSerializer, EquipoMaterialSerializer, ReporteSerializer, FacturaSerializer


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
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer