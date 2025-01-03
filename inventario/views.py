

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
        
        if reporte.fecha_inicio and reporte.fecha_fin and reporte.fecha_inicio > reporte.fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin.")

        
        datos = self.generar_datos(reporte.filtro, reporte.fecha_inicio, reporte.fecha_fin)

        if not datos:
            datos = [
                {
                    "mensaje": f"No se encontraron datos para el filtro '{reporte.filtro}' "
                               f"entre {reporte.fecha_inicio} y {reporte.fecha_fin}."
                }
            ]

        
        response_data = serializer.data
        response_data["datos"] = datos
        return Response(response_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        Recuperar un reporte e incluir los datos generados dinámicamente.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        datos = self.generar_datos(instance.filtro, instance.fecha_inicio, instance.fecha_fin)

        if not datos:
            datos = [
                {
                    "mensaje": f"No se encontraron datos para el filtro '{instance.filtro}' "
                               f"entre {instance.fecha_inicio} y {instance.fecha_fin}."
                }
            ]

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

        
        if instance.fecha_inicio and instance.fecha_fin and instance.fecha_inicio > instance.fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin.")

        
        datos = self.generar_datos(instance.filtro, instance.fecha_inicio, instance.fecha_fin)

        if not datos:
            datos = [
                {
                    "mensaje": f"No se encontraron datos para el filtro '{instance.filtro}' "
                               f"entre {instance.fecha_inicio} y {instance.fecha_fin}."
                }
            ]

        
        response_data = serializer.data
        response_data["datos"] = datos
        return Response(response_data)

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
            usuarios = Usuario.objects.all()  
            if fecha_inicio and fecha_fin:
                usuarios = usuarios.filter(fecha_creacion__range=[fecha_inicio, fecha_fin])
            return list(usuarios.values("id", "username", "email", "telefono", "rol", "is_active", "fecha_creacion"))
        elif filtro == "mantenimientos":
            mantenimientos = Mantenimiento.objects.all()
            if fecha_inicio and fecha_fin:
                
                mantenimientos = mantenimientos.filter(fecha_inicio__gte=fecha_inicio, fecha_fin__lte=fecha_fin)
            return list(mantenimientos.values("id", "producto__equipo", "estado", "fecha_inicio", "fecha_fin"))


        elif filtro == "actividades":
            actividades = Actividad.objects.all()
            if fecha_inicio and fecha_fin:
                actividades = actividades.filter(fecha__range=[fecha_inicio, fecha_fin])  
            return list(actividades.values("id", "descripcion", "fecha"))  

            
            

        return []

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



from datetime import date
from django.db.models import Sum, F, Q
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from .models import Resumen
from .serializers import ResumenSerializer

class ResumenViewSet(ModelViewSet):
    queryset = Resumen.objects.all()
    serializer_class = ResumenSerializer

    def create(self, request, *args, **kwargs):
        # Crear el objeto Resumen
        instance = Resumen.objects.create()

        # Utilizar la fecha actual para calcular los datos dinámicos
        hoy = date.today()
        resumen_datos = self._calcular_datos(hoy)

        # Si no hay datos, devolver un mensaje
        if not resumen_datos:
            return Response(
                {"message": "No se encontraron datos para la fecha actual."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "id": instance.id,
            "fecha_actual": str(hoy),
            "datos": resumen_datos
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Utilizar la fecha actual para calcular los datos dinámicos
        hoy = date.today()
        resumen_datos = self._calcular_datos(hoy)

        if not resumen_datos:
            return Response(
                {"message": "No se encontraron datos para la fecha actual."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "id": instance.id,
            "fecha_actual": str(hoy),
            "datos": resumen_datos
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Utilizar la fecha actual para calcular los datos dinámicos
        hoy = date.today()
        resumen_datos = self._calcular_datos(hoy)

        # Si no hay datos, devolver un mensaje
        if not resumen_datos:
            return Response(
                {"message": "No se encontraron datos para la fecha actual."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "id": instance.id,
            "fecha_actual": str(hoy),
            "datos": resumen_datos
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Resumen eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)

    def _calcular_datos(self, fecha):
        # Validar que la fecha sea válida
        if not fecha:
            return []

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
        facturas_del_dia = Factura.objects.filter(fecha_salida=fecha)

        # Calcular ventas del día dinámicamente
        total_del_dia = facturas_del_dia.aggregate(
            total_dia=Sum(F('cantidad') * F('producto__valor'))
        )['total_dia'] or 0

        # Filtrar actividades del día por fecha
        actividades_del_dia = Actividad.objects.filter(fecha__date=fecha)

        # Filtrar mantenimientos activos
        mantenimientos_activos = Mantenimiento.objects.filter(
            Q(fecha_inicio__lte=fecha) & Q(fecha_fin__gte=fecha)
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


