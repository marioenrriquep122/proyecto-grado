

from django.db import models  
from django.db.models import Count, Sum, F, Q
from django.http import HttpResponse
from django.utils.timezone import now

from usuarios.models import Usuario
from .models import Categoria, EquipoMaterial, Mantenimiento,  Reporte, Factura, Actividad, Factura, Resumen
from .serializers import ActividadSerializer, CategoriaSerializer, EquipoMaterialSerializer, MantenimientoSerializer, ReporteSerializer, FacturaSerializer, ResumenSerializer

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
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (puedes cambiar esto)

    def create(self, request, *args, **kwargs):
        """
        Sobrescribir para validar si el nombre ya existe antes de crear.
        """
        nombre = request.data.get('nombre', '').strip()
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            return Response(
                {"error": "Ya existe una categoría con este nombre."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Sobrescribir para validar si el nombre ya existe al actualizar.
        """
        instance = self.get_object()
        nombre = request.data.get('nombre', '').strip()
        if Categoria.objects.filter(nombre__iexact=nombre).exclude(id=instance.id).exists():
            return Response(
                {"error": "Ya existe otra categoría con este nombre."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)


# --- EquipoMaterial  que es producto---
class EquipoMaterialViewSet(viewsets.ModelViewSet):
    queryset = EquipoMaterial.objects.all()
    serializer_class = EquipoMaterialSerializer
    permission_classes = [AllowAny]  # Cambia según necesidad

    def create(self, request, *args, **kwargs):
       
        categoria_id = request.data.get('categoria')
        if not categoria_id:
            raise ValidationError("El producto debe pertenecer a una categoría.")

        if not Categoria.objects.filter(id=categoria_id).exists():
            raise ValidationError("La categoría especificada no existe.")

        
        serial = request.data.get('serial')
        if EquipoMaterial.objects.filter(serial=serial).exists():
            raise ValidationError(f"El número de serie ya está en uso: {serial}.")

        
        stock = request.data.get('cantidad', 0)
        if int(stock) > 0:
            request.data['estado'] = 'disponible'
        else:
            request.data['estado'] = 'retirado'

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serial = request.data.get('serial')
        if serial and EquipoMaterial.objects.filter(serial=serial).exclude(id=instance.id).exists():
            raise ValidationError(f"El número de serie ya está en uso: {serial}.")

        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def bajo_stock(self, request):
        """
        Listar equipos con cantidad menor o igual al stock mínimo.
        """
        stock_minimo = request.query_params.get('stock_minimo', 1)
        items = self.queryset.filter(cantidad__lte=stock_minimo)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def en_mantenimiento(self, request):
        """
        Listar equipos en mantenimiento.
        """
        items = self.queryset.filter(estado='en_mantenimiento')
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

   


# --- Reporte ---

class ReporteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la generación de reportes.
    """
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer

    def create(self, request, *args, **kwargs):
        """
        Crear un reporte basado en el tipo y las fechas.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        reporte = serializer.instance

        # Validación de rango de fechas
        if reporte.fecha_inicio and reporte.fecha_fin and reporte.fecha_inicio > reporte.fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin.")

        # Generar datos según el tipo
        if reporte.tipo == "general":
            datos = self._generar_resumen(reporte.fecha_inicio, reporte.fecha_fin)
        elif reporte.tipo == "stock":
            datos = self._obtener_stock(reporte.fecha_inicio, reporte.fecha_fin)
        elif reporte.tipo == "factura":
            datos = self._obtener_facturas(reporte.fecha_inicio, reporte.fecha_fin)
        elif reporte.tipo == "actividades":
            datos = self._obtener_actividades(reporte.fecha_inicio, reporte.fecha_fin)
        else:
            datos = []

        # Guardar los datos generados en el reporte
        reporte.datos = datos
        reporte.save()

        # Respuesta con los datos generados
        response_data = serializer.data
        response_data["datos"] = datos
        return Response(response_data, status=status.HTTP_201_CREATED)

    def _generar_resumen(self, fecha_inicio=None, fecha_fin=None):
        """
        Genera los datos del resumen general.
        """
        resumen, created = Resumen.objects.get_or_create()

        # Calcular los datos del resumen general
        resumen_datos = self._calcular_datos_resumen(fecha_inicio, fecha_fin)

        return {
            "id": resumen.id,
            "datos": resumen_datos
        }

    def _calcular_datos_resumen(self, fecha_inicio=None, fecha_fin=None):
        """
        Calcula los datos del resumen general, filtrando por fechas si son proporcionadas.
        """
        categorias_totales = Categoria.objects.count()
        productos_totales = EquipoMaterial.objects.count()

        # Filtrar facturas y actividades por fechas si son proporcionadas
        if fecha_inicio and fecha_fin:
            facturas = Factura.objects.filter(fecha_salida__range=[fecha_inicio, fecha_fin])
            actividades = Actividad.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        else:
            facturas = Factura.objects.all()
            actividades = Actividad.objects.all()

        mantenimientos_totales = Mantenimiento.objects.count()
        stock_total_disponible = EquipoMaterial.objects.aggregate(total_stock=Sum('cantidad'))['total_stock'] or 0
        ventas_totales = facturas.aggregate(total_ventas=Sum(F('cantidad') * F('producto__valor')))['total_ventas'] or 0

        return {
            "total_categorias": categorias_totales,
            "total_productos": productos_totales,
            "total_facturas": facturas.count(),
            "total_actividades": actividades.count(),
            "total_mantenimientos": mantenimientos_totales,
            "stock_total_disponible": stock_total_disponible,
            "ventas_totales": ventas_totales,
        }

    def _obtener_stock(self, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene los productos (stock) en el rango de fechas, si se especifican.
        """
        productos = EquipoMaterial.objects.all()
        if fecha_inicio and fecha_fin:
            productos = productos.filter(fecha_entrada__range=[fecha_inicio, fecha_fin])

        # Convertir productos a un formato serializable
        return [
            {
                "id": producto.id,
                "equipo": producto.equipo,
                "marca": producto.marca,
                "cantidad": producto.cantidad,
                "estado": producto.estado,
            }
            for producto in productos
        ]

    def _obtener_facturas(self, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene las facturas en el rango de fechas, si se especifican.
        """
        facturas = Factura.objects.all()
        if fecha_inicio and fecha_fin:
            facturas = facturas.filter(fecha_salida__range=[fecha_inicio, fecha_fin])

        # Convertir facturas a un formato serializable
        return [
            {
                "id": factura.id,
                "producto": factura.producto.equipo,
                "cantidad": factura.cantidad,
                "fecha_salida": factura.fecha_salida.isoformat(),
                "numero_factura": factura.numero_factura,
            }
            for factura in facturas
        ]

    def _obtener_actividades(self, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene las actividades en el rango de fechas, si se especifican.
        """
        actividades = Actividad.objects.all()
        if fecha_inicio and fecha_fin:
            actividades = actividades.filter(fecha__range=[fecha_inicio, fecha_fin])

        # Convertir actividades a un formato serializable
        return [
            {
                "id": actividad.id,
                "tipo": actividad.get_tipo_display(),
                "descripcion": actividad.descripcion,
                "fecha": actividad.fecha.isoformat(),
                "factura": actividad.factura.numero_factura if actividad.factura else None,
            }
            for actividad in actividades
        ]




# --- Factura ---
class FacturaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de facturas.
    """
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer

    def create(self, request, *args, **kwargs):
        """
        Valida que el producto esté disponible y ajusta el stock al crear una factura.
        """
        producto_id = request.data.get('producto')
        cantidad = int(request.data.get('cantidad', 0))
        try:
            producto = EquipoMaterial.objects.get(id=producto_id)
        except EquipoMaterial.DoesNotExist:
            raise ValidationError("El producto especificado no existe.")

        
        if producto.estado != 'disponible':
            raise ValidationError(f"No se puede crear la factura porque el producto '{producto.equipo}' no está disponible (Estado actual: {producto.estado}).")

        
        if producto.cantidad < cantidad:
            raise ValidationError(f"No hay suficiente stock del producto '{producto.equipo}'. Stock disponible: {producto.cantidad}, solicitado: {cantidad}.")

        
        producto.cantidad -= cantidad
        if producto.cantidad == 0:
            producto.estado = 'retirado'  
        producto.save()

        
        response = super().create(request, *args, **kwargs)
        factura = Factura.objects.get(id=response.data['id'])

        
        descripcion = (
            f"Factura {factura.numero_factura} creada para la venta de {producto.equipo}. "
            f"Cantidad: {factura.cantidad} unidades. Total: ${factura.cantidad * producto.valor:.2f}."
        )
        Actividad.objects.create(
            tipo='venta',
            factura=factura,
            descripcion=descripcion
        )

        return response

    def update(self, request, *args, **kwargs):
        """
        Ajusta el stock del producto al actualizar una factura.
        """
        factura = self.get_object()
        producto = factura.producto
        nueva_cantidad = int(request.data.get('cantidad', factura.cantidad))

        
        producto.cantidad += factura.cantidad

        
        if producto.cantidad < nueva_cantidad:
            raise ValidationError(f"No hay suficiente stock para actualizar esta factura. Stock disponible: {producto.cantidad}, solicitado: {nueva_cantidad}.")

        producto.cantidad -= nueva_cantidad
        if producto.cantidad == 0:
            producto.estado = 'retirado'  
        elif producto.estado == 'retirado':
            producto.estado = 'disponible' 
        producto.save()

        
        descripcion = (
            f"Factura {factura.numero_factura} actualizada. Producto: {producto.equipo}, "
            f"Cantidad: {nueva_cantidad} unidades, Total: ${nueva_cantidad * producto.valor:.2f}."
        )
        Actividad.objects.create(
            tipo='factura',
            factura=factura,
            descripcion=descripcion
        )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Restablece el stock del producto al eliminar una factura.
        """
        factura = self.get_object()
        producto = factura.producto

        
        producto.cantidad += factura.cantidad
        if producto.estado == 'retirado':  
            producto.estado = 'disponible'
        producto.save()

        return super().destroy(request, *args, **kwargs)







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
        data = request.data.copy()

        
        tipo = data.get('tipo', 'otro')
        if tipo not in dict(Actividad.TIPO_CHOICES).keys():
            raise ValidationError(f"Tipo de actividad no válido: {tipo}")

        
        factura_id = data.get('factura')
        descripcion = data.get('descripcion', '').strip()

        
        if not descripcion:
            factura = Factura.objects.filter(id=factura_id).first()
            if factura:
                descripcion = f"Actividad de tipo '{tipo}' registrada para la factura #{factura.numero_factura}."
            else:
                descripcion = f"Actividad de tipo '{tipo}' registrada sin factura específica."

        data['descripcion'] = descripcion

        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Sobreescribe el método update para validar y actualizar actividades.
        """
        instance = self.get_object()
        data = request.data.copy()

        
        tipo = data.get('tipo', instance.tipo)
        if tipo not in dict(Actividad.TIPO_CHOICES).keys():
            raise ValidationError(f"Tipo de actividad no válido: {tipo}")

        
        descripcion = data.get('descripcion', '').strip()
        if not descripcion:
            factura = Factura.objects.filter(id=instance.factura.id).first() if instance.factura else None
            if factura:
                descripcion = f"Actividad de tipo '{tipo}' actualizada para la factura #{factura.numero_factura}."
            else:
                descripcion = f"Actividad de tipo '{tipo}' actualizada sin factura específica."
        data['descripcion'] = descripcion

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Sobreescribe el método destroy para manejar la eliminación de actividades.
        """
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Actividad eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)

    
    
    




from rest_framework.viewsets import ModelViewSet
from datetime import date

# --- Resumen ---




from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from django.db.models import Sum, F, Q
from .models import Resumen
from datetime import date

class ResumenViewSet(ViewSet):
    def list(self, request, *args, **kwargs):
        # Asegurarse de que existe un único resumen
        resumen, created = Resumen.objects.get_or_create()

        # Calcular dinámicamente los datos consolidados
        resumen_datos = self._calcular_datos()

        return Response({
            "id": resumen.id,
            "datos": resumen_datos
        })

    def _calcular_datos(self):
        # Calcular totales generales
        categorias_totales = Categoria.objects.count()
        productos_totales = EquipoMaterial.objects.count()
        facturas_totales = Factura.objects.count()
        actividades_totales = Actividad.objects.count()
        mantenimientos_totales = Mantenimiento.objects.count()
        stock_total_disponible = EquipoMaterial.objects.aggregate(total_stock=Sum('cantidad'))['total_stock'] or 0

        # Calcular ventas totales dinámicamente
        ventas_totales = Factura.objects.aggregate(
            total_ventas=Sum(F('cantidad') * F('producto__valor'))
        )['total_ventas'] or 0

        # Filtrar facturas del día por `fecha_salida`
        hoy = date.today()
        facturas_del_dia = Factura.objects.filter(fecha_salida=hoy)

        # Calcular ventas del día dinámicamente
        total_del_dia = facturas_del_dia.aggregate(
            total_dia=Sum(F('cantidad') * F('producto__valor'))
        )['total_dia'] or 0

        # Filtrar actividades del día por fecha
        actividades_del_dia = Actividad.objects.filter(fecha__date=hoy)

        # Filtrar mantenimientos activos
        mantenimientos_activos = Mantenimiento.objects.filter(
            Q(fecha_inicio__lte=hoy) & Q(fecha_fin__gte=hoy)
        )

        # Consolidar los datos
        resumen_datos = {
            "total_categorias": categorias_totales,
            "total_productos": productos_totales,
            "total_facturas": facturas_totales,
            "total_actividades": actividades_totales,
            "total_mantenimientos": mantenimientos_totales,
            "stock_total_disponible": stock_total_disponible,
            "ventas_totales": ventas_totales,  # Suma total de todas las facturas
            "facturas_del_dia": facturas_del_dia.count(),
            "actividades_del_dia": actividades_del_dia.count(),
            "mantenimientos_activos": mantenimientos_activos.count(),
            "total_del_dia": total_del_dia,  # Suma total de las facturas del día
        }

        return resumen_datos



    
class MantenimientoViewSet(viewsets.ModelViewSet):
    queryset = Mantenimiento.objects.all()
    serializer_class = MantenimientoSerializer

    def create(self, request, *args, **kwargs):
        producto_id = request.data.get('producto')
        try:
            producto = EquipoMaterial.objects.get(id=producto_id)
        except EquipoMaterial.DoesNotExist:
            raise ValidationError("El producto especificado no existe.")

        if producto.estado != 'disponible':
            raise ValidationError(f"El producto '{producto.equipo}' no está disponible y no puede ser puesto en mantenimiento.")
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """
        Permitir la actualización del estado del mantenimiento y reflejarlo en el producto.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        mantenimientos = self.queryset.filter(estado='pendiente')
        serializer = self.get_serializer(mantenimientos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completados(self, request):
        mantenimientos = self.queryset.filter(estado='completado')
        serializer = self.get_serializer(mantenimientos, many=True)
        return Response(serializer.data)


