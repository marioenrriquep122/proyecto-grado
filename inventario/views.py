

from django.db import models  
from django.db.models import Count, Sum, F, Q
from django.http import HttpResponse
from django.utils.timezone import now

from inventario.utils import registrar_actividad
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
from rest_framework.response import Response
from rest_framework import status
from .models import Categoria, Actividad

class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de Categorías.
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]  # Cambia según tu necesidad

    def create(self, request, *args, **kwargs):
        """
        Sobrescribe para validar si el nombre ya existe antes de crear.
        Registra una actividad después de la creación.
        """
        nombre = request.data.get('nombre', '').strip()
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            return Response(
                {"error": "Ya existe una categoría con este nombre."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Llama al método original para realizar la creación
        response = super().create(request, *args, **kwargs)

        # Registra la actividad después de la creación
        if response.status_code == 201:  # Solo si se creó correctamente
            registrar_actividad(
                tipo='categoria',  # Tipo de actividad
                descripcion="Se ha creado una categoría.",  # Descripción genérica
                nombre=response.data.get('nombre')  # Pasar el nombre de la categoría
            )
        return response

    def update(self, request, *args, **kwargs):
        """
        Sobrescribe para validar si el nombre ya existe al actualizar.
        Registra una actividad después de la actualización.
        """
        instance = self.get_object()
        nombre = request.data.get('nombre', '').strip()
        if Categoria.objects.filter(nombre__iexact=nombre).exclude(id=instance.id).exists():
            return Response(
                {"error": "Ya existe otra categoría con este nombre."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Llama al método original para realizar la actualización
        response = super().update(request, *args, **kwargs)

        # Registra la actividad después de la actualización
        if response.status_code == 200:  # Solo si se actualizó correctamente
            registrar_actividad(
                tipo='categoria',  # Tipo de actividad
                descripcion="Se ha actualizado una categoría.",  # Descripción genérica
                nombre=response.data.get('nombre')  # Pasar el nombre actualizado de la categoría
            )
        return response




# --- EquipoMaterial  que es producto---
from rest_framework.exceptions import ValidationError
from .utils import registrar_actividad  # Asegúrate de que esta función esté correctamente importada

class EquipoMaterialViewSet(viewsets.ModelViewSet):
    queryset = EquipoMaterial.objects.all()
    serializer_class = EquipoMaterialSerializer
    permission_classes = [AllowAny]  # Cambia según necesidad

    def create(self, request, *args, **kwargs):
        """
        Crear un producto y registrar una actividad.
        """
        # Hacer una copia mutable de request.data
        mutable_data = request.data.copy()

        categoria_id = mutable_data.get('categoria')
        if not categoria_id:
            raise ValidationError("El producto debe pertenecer a una categoría.")

        if not Categoria.objects.filter(id=categoria_id).exists():
            raise ValidationError("La categoría especificada no existe.")

        serial = mutable_data.get('serial')
        if EquipoMaterial.objects.filter(serial=serial).exists():
            raise ValidationError(f"El número de serie ya está en uso: {serial}.")

        stock = mutable_data.get('cantidad', 0)
        if int(stock) > 0:
            mutable_data['estado'] = 'disponible'
        else:
            mutable_data['estado'] = 'retirado'

        # Reemplaza el data original con el mutable antes de pasar al super
        request._full_data = mutable_data
        response = super().create(request, *args, **kwargs)

        # Registrar la actividad después de la creación
        if response.status_code == 201:
            producto = EquipoMaterial.objects.get(id=response.data['id'])
            registrar_actividad(
                tipo='producto',
                descripcion="Producto creado.",
                equipo=producto.equipo,
                marca=producto.marca,
                cantidad=producto.cantidad,
                valor=producto.valor
            )
        return response

    def update(self, request, *args, **kwargs):
        """
        Actualizar un producto y registrar una actividad.
        """
        # Hacer una copia mutable de request.data
        mutable_data = request.data.copy()

        instance = self.get_object()
        serial = mutable_data.get('serial')
        if serial and EquipoMaterial.objects.filter(serial=serial).exclude(id=instance.id).exists():
            raise ValidationError(f"El número de serie ya está en uso: {serial}.")

        # Reemplaza el data original con el mutable antes de pasar al super
        request._full_data = mutable_data
        response = super().update(request, *args, **kwargs)

        # Registrar la actividad después de la actualización
        if response.status_code == 200:
            producto = EquipoMaterial.objects.get(id=response.data['id'])
            registrar_actividad(
                tipo='producto',
                descripcion="Producto actualizado.",
                equipo=producto.equipo,
                marca=producto.marca,
                cantidad=producto.cantidad,
                valor=producto.valor
            )
        return response


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
            datos = {"mensaje": "Tipo de reporte no válido."}

        # Guardar los datos generados en el reporte
        reporte.datos = datos
        reporte.save()

        # Registrar la actividad con el tipo de reporte en la descripción
        registrar_actividad(
            tipo='reporte',
            descripcion=f"Se ha generado un reporte de tipo '{reporte.tipo}'."
        )

        # Respuesta con los datos generados
        response_data = serializer.data
        response_data["datos"] = datos
        return Response(response_data, status=status.HTTP_201_CREATED)



    
    def update(self, request, *args, **kwargs):
        """
        Actualizar un reporte y regenerar los datos dinámicamente.
        """
        partial = kwargs.pop('partial', False)  # Permitir actualizaciones parciales (PATCH)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Validar fechas
        if instance.fecha_inicio and instance.fecha_fin and instance.fecha_inicio > instance.fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin.")

        # Regenerar los datos según el tipo
        if instance.tipo == "general":
            datos = self._generar_resumen(instance.fecha_inicio, instance.fecha_fin)
        elif instance.tipo == "stock":
            datos = self._obtener_stock(instance.fecha_inicio, instance.fecha_fin)
        elif instance.tipo == "factura":
            datos = self._obtener_facturas(instance.fecha_inicio, instance.fecha_fin)
        elif instance.tipo == "actividades":
            datos = self._obtener_actividades(instance.fecha_inicio, instance.fecha_fin)
        else:
            datos = []

        # Guardar los datos actualizados
        instance.datos = datos
        instance.save()

        # Registrar la actividad
        registrar_actividad(
            tipo='reporte',
            descripcion=(
                f"Reporte actualizado: {instance.tipo}, "
                f"fechas: {instance.fecha_inicio} - {instance.fecha_fin}."
            )
        )

        # Incluir los datos actualizados en la respuesta
        response_data = serializer.data
        response_data["datos"] = datos
        return Response(response_data, status=status.HTTP_200_OK)

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
                "valor": float(factura.producto.valor),  # Convertir Decimal a float
                "total": float(factura.cantidad * factura.producto.valor),  # Convertir total a float
                "stock_restante": factura.producto.cantidad,  # Stock restante después de la factura
            }
            for factura in facturas
        ]
        
    from datetime import datetime

    def _obtener_actividades(self, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene las actividades en el rango de fechas, si se especifican.
        """
        actividades = Actividad.objects.all()

        # Validar y convertir fechas de string a datetime
        try:
            if fecha_inicio:
                fecha_inicio = datetime.strptime(str(fecha_inicio), "%Y-%m-%d")
            if fecha_fin:
                fecha_fin = datetime.strptime(str(fecha_fin), "%Y-%m-%d")
        except ValueError:
            return {"mensaje": "Formato de fecha inválido. Usa el formato YYYY-MM-DD."}

        # Filtrar por rango de fechas si se proporcionan
        if fecha_inicio and fecha_fin:
            actividades = actividades.filter(fecha__date__range=[fecha_inicio, fecha_fin])

        if not actividades.exists():
            return {"mensaje": "No se encontraron actividades en el rango de fechas proporcionado."}

        # Convertir actividades a un formato serializable
        return [
            {
                "id": actividad.id,
                "tipo": actividad.tipo,
                "descripcion": actividad.descripcion,
                "fecha": actividad.fecha.isoformat(),
            }
            for actividad in actividades
        ]


        

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

        if fecha_inicio and fecha_fin:
            facturas = Factura.objects.filter(fecha_salida__range=[fecha_inicio, fecha_fin])
            actividades = Actividad.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        else:
            facturas = Factura.objects.all()
            actividades = Actividad.objects.all()

        if not facturas.exists() and not actividades.exists():
            return {
                "mensaje": "No se encontraron datos para el rango de fechas proporcionado.",
                "total_categorias": categorias_totales,
                "total_productos": productos_totales,
                "total_facturas": 0,
                "total_actividades": 0,
                "total_mantenimientos": 0,
                "stock_total_disponible": 0.0,
                "ventas_totales": 0.0,
            }

        mantenimientos_totales = Mantenimiento.objects.count()
        stock_total_disponible = EquipoMaterial.objects.aggregate(total_stock=Sum('cantidad'))['total_stock'] or 0
        ventas_totales = facturas.aggregate(
            total_ventas=Sum(F('cantidad') * F('producto__valor'))
        )['total_ventas'] or 0

        return {
            "total_categorias": categorias_totales,
            "total_productos": productos_totales,
            "total_facturas": facturas.count(),
            "total_actividades": actividades.count(),
            "total_mantenimientos": mantenimientos_totales,
            "stock_total_disponible": float(stock_total_disponible),
            "ventas_totales": float(ventas_totales),
        }
        
        
    def _obtener_stock(self, fecha_inicio=None, fecha_fin=None):
        productos = EquipoMaterial.objects.all()
        if fecha_inicio and fecha_fin:
            productos = productos.filter(fecha_entrada__range=[fecha_inicio, fecha_fin])

        if not productos.exists():
            return {"mensaje": "No se encontraron productos de stock en el rango de fechas proporcionado."}

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
        facturas = Factura.objects.all()
        if fecha_inicio and fecha_fin:
            facturas = facturas.filter(fecha_salida__range=[fecha_inicio, fecha_fin])

        if not facturas.exists():
            return {"mensaje": "No se encontraron facturas en el rango de fechas proporcionado."}

        return [
            {
                "id": factura.id,
                "producto": factura.producto.equipo,
                "cantidad": factura.cantidad,
                "fecha_salida": factura.fecha_salida.isoformat(),
                "numero_factura": factura.numero_factura,
                "valor": float(factura.producto.valor),
                "total": float(factura.cantidad * factura.producto.valor),
                "stock_restante": factura.producto.cantidad,
            }
            for factura in facturas
        ]
    def _obtener_actividades(self, fecha_inicio=None, fecha_fin=None):
        actividades = Actividad.objects.all()
        if fecha_inicio and fecha_fin:
            actividades = actividades.filter(fecha__range=[fecha_inicio, fecha_fin])

        if not actividades.exists():
            return {"mensaje": "No se encontraron actividades en el rango de fechas proporcionado."}

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
from .models import Actividad
from .utils import registrar_actividad

class FacturaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el CRUD de facturas.
    """
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer

    def create(self, request, *args, **kwargs):
        """
        Valida el stock del producto y registra una actividad al crear una factura.
        """
        producto_id = request.data.get('producto')
        cantidad = int(request.data.get('cantidad', 0))

        # Validar si el producto existe
        try:
            producto = EquipoMaterial.objects.get(id=producto_id)
        except EquipoMaterial.DoesNotExist:
            raise ValidationError("El producto especificado no existe.")

        # Validar el estado y el stock del producto
        if producto.estado != 'disponible':
            raise ValidationError(f"El producto '{producto.equipo}' no está disponible (Estado actual: {producto.estado}).")

        if producto.cantidad < cantidad:
            raise ValidationError(f"No hay suficiente stock para el producto '{producto.equipo}'. Stock disponible: {producto.cantidad}, solicitado: {cantidad}.")

        # Ajustar el stock del producto
        producto.cantidad -= cantidad
        if producto.cantidad == 0:
            producto.estado = 'retirado'
        producto.save()

        # Crear la factura
        response = super().create(request, *args, **kwargs)
        factura = Factura.objects.get(id=response.data['id'])

        # Calcular el valor total
        valor_total = cantidad * producto.valor

        # Registrar la actividad
        registrar_actividad(
            tipo='factura',
            descripcion="Factura generada.",
            numero_factura=factura.numero_factura,
            nombre_cliente=factura.nombre_cliente,
            equipo=producto.equipo,
            cantidad=cantidad,
            valor=producto.valor,
            valor_total=valor_total
        )

        return response

    def update(self, request, *args, **kwargs):
        """
        Ajusta el stock del producto y registra una actividad al actualizar una factura.
        """
        factura = self.get_object()
        producto = factura.producto
        nueva_cantidad = int(request.data.get('cantidad', factura.cantidad))

        # Revertir el stock anterior
        producto.cantidad += factura.cantidad

        # Validar el nuevo stock
        if producto.cantidad < nueva_cantidad:
            raise ValidationError(f"No hay suficiente stock para actualizar esta factura. Stock disponible: {producto.cantidad}, solicitado: {nueva_cantidad}.")

        # Ajustar el stock con la nueva cantidad
        producto.cantidad -= nueva_cantidad
        if producto.cantidad == 0:
            producto.estado = 'retirado'
        elif producto.estado == 'retirado':
            producto.estado = 'disponible'
        producto.save()

        # Actualizar la factura
        factura.nombre_cliente = request.data.get('nombre_cliente', factura.nombre_cliente)
        factura.compania_cliente = request.data.get('compania_cliente', factura.compania_cliente)
        factura.direccion = request.data.get('direccion', factura.direccion)
        factura.barrio = request.data.get('barrio', factura.barrio)
        factura.telefono = request.data.get('telefono', factura.telefono)
        factura.save()

        # Calcular el nuevo valor total
        valor_total = nueva_cantidad * producto.valor

        # Registrar la actividad
        registrar_actividad(
            tipo='factura',
            descripcion="Factura actualizada.",
            numero_factura=factura.numero_factura,
            nombre_cliente=factura.nombre_cliente,
            equipo=producto.equipo,
            cantidad=nueva_cantidad,
            valor=producto.valor,
            valor_total=valor_total
        )

        return super().update(request, *args, **kwargs)


    def destroy(self, request, *args, **kwargs):
        """
        Restablece el stock del producto al eliminar una factura.
        """
        factura = self.get_object()
        producto = factura.producto

        # Revertir el stock
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
        Valida el tipo y permite crear actividades solo si se proporciona la información correcta.
        """
        data = request.data.copy()

        # Validar el tipo
        tipo = data.get('tipo')
        if tipo not in dict(Actividad.TIPO_CHOICES).keys():
            raise ValidationError(f"Tipo de actividad no válido: {tipo}")

        # Validar que la descripción no esté vacía
        descripcion = data.get('descripcion', '').strip()
        if not descripcion:
            raise ValidationError("La descripción no puede estar vacía.")

        # Validar `valor_total` solo si aplica
        if tipo in ['factura', 'pedido']:
            valor_total = data.get('valor_total')
            if valor_total is None:
                raise ValidationError("El campo `valor_total` es obligatorio para facturas y pedidos.")

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    
    
    




from rest_framework.viewsets import ModelViewSet
from datetime import date, datetime

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
        """
        Crear un registro de mantenimiento y registrar la actividad.
        """
        producto_id = request.data.get('producto')
        try:
            producto = EquipoMaterial.objects.get(id=producto_id)
        except EquipoMaterial.DoesNotExist:
            raise ValidationError("El producto especificado no existe.")

        if producto.estado != 'disponible':
            raise ValidationError(f"El producto '{producto.equipo}' no está disponible y no puede ser puesto en mantenimiento.")

        # Cambiar el estado del producto a "En mantenimiento"
        producto.estado = 'mantenimiento'
        producto.save()

        # Crear el registro de mantenimiento
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            mantenimiento = Mantenimiento.objects.get(id=response.data['id'])

            # Registrar la actividad con el nombre del producto
            registrar_actividad(
                tipo='mantenimiento',
                descripcion="Se ha ingresado un producto a mantenimiento.",
                equipo=producto.equipo  # Nombre del producto
            )

        return response



    def update(self, request, *args, **kwargs):
        """
        Actualizar el mantenimiento y registrar una actividad si el estado cambia a 'completado'.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Si el estado cambia a "completado", registrar actividad
        if instance.estado == 'completado':
            registrar_actividad(
                tipo='mantenimiento',
                descripcion=f"El producto '{instance.producto.equipo}' ha finalizado su mantenimiento.",
                equipo=instance.producto.equipo,
                marca=instance.producto.marca
            )

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




from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from .models import Pedido, EquipoMaterial
from .serializers import PedidoSerializer
from inventario.models import Categoria  # Asegúrate de importar tus modelos

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from .models import Pedido, EquipoMaterial, Categoria
from .serializers import PedidoSerializer, EquipoMaterialSerializer

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer

    def create(self, request, *args, **kwargs):
        """
        Crear un pedido, asegurando que la categoría y el producto sean válidos.
        """
        mutable_data = request.data.copy()

        # Validar categoría y producto
        categoria_id = mutable_data.get('categoria')
        producto_id = mutable_data.get('producto')

        if not categoria_id or not producto_id:
            raise ValidationError("Debe seleccionar una categoría y un producto.")

        # Validar si la categoría existe
        try:
            categoria = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            raise ValidationError("La categoría especificada no existe.")

        # Obtener productos asociados a la categoría
        productos_asociados = EquipoMaterial.objects.filter(categoria=categoria)
        if not productos_asociados.exists():
            raise ValidationError("La categoría seleccionada no tiene productos asociados.")

        # Validar si el producto pertenece a la categoría
        try:
            producto = productos_asociados.get(id=producto_id)
        except EquipoMaterial.DoesNotExist:
            raise ValidationError("El producto especificado no pertenece a la categoría seleccionada.")

        # Validar stock del producto
        cantidad = int(mutable_data.get('cantidad', 0))
        if producto.cantidad < cantidad:
            mutable_data['estado'] = 'no_disponible'
        else:
            producto.cantidad -= cantidad
            producto.save()
            mutable_data['estado'] = 'disponible'

        # Crear el pedido
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Respuesta con nombres en lugar de IDs
        response_data = serializer.data
        response_data['categoria'] = categoria.nombre
        response_data['producto'] = producto.equipo

        return Response({"success": True, "message": "Pedido creado exitosamente.", "data": response_data})


    def update(self, request, *args, **kwargs):
        """
        Actualizar un pedido y ajustar el stock del producto asociado.
        """
        pedido = self.get_object()
        producto = pedido.producto

        # Crear una copia mutable de los datos del request
        mutable_data = request.data.copy()
        nueva_cantidad = int(mutable_data.get('cantidad', pedido.cantidad))

        # Revertir el stock anterior
        producto.cantidad += pedido.cantidad

        # Validar el nuevo stock
        if producto.cantidad < nueva_cantidad:
            mutable_data['estado'] = 'no_disponible'
        else:
            producto.cantidad -= nueva_cantidad
            producto.save()
            mutable_data['estado'] = 'disponible'

        # Validar categoría
        categoria_id = mutable_data.get('categoria')
        try:
            categoria = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            raise ValidationError("La categoría especificada no existe.")

        # Validar producto
        producto_id = mutable_data.get('producto')
        try:
            producto = EquipoMaterial.objects.get(id=producto_id)
        except EquipoMaterial.DoesNotExist:
            raise ValidationError("El producto especificado no existe.")

        # Actualizar el pedido
        serializer = self.get_serializer(pedido, data=mutable_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Respuesta personalizada con nombres de categoría y producto
        response_data = serializer.data
        response_data['categoria'] = categoria.nombre
        response_data['producto'] = producto.equipo

        return Response({"success": True, "message": "Pedido actualizado correctamente.", "data": response_data})

    def destroy(self, request, *args, **kwargs):
        """
        Elimina un pedido y ajusta el stock del producto asociado.
        """
        pedido = self.get_object()
        producto = pedido.producto

        # Revertir el stock del producto
        producto.cantidad += pedido.cantidad
        producto.save()

        # Eliminar el pedido
        self.perform_destroy(pedido)

        return Response({"success": True, "message": "Pedido eliminado correctamente."})

    @action(detail=False, methods=['get'], url_path='productos-por-categoria/(?P<categoria_id>[^/.]+)')
    def productos_por_categoria(self, request, categoria_id=None):
        """
        Obtener productos relacionados con una categoría.
        """
        try:
            categoria = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            return Response(
                {"success": False, "message": "La categoría especificada no existe."},
                status=404
            )

        productos = EquipoMaterial.objects.filter(categoria=categoria)
        serializer = EquipoMaterialSerializer(productos, many=True)
        return Response(
            {"success": True, "categoria": categoria.nombre, "productos": serializer.data}
        )

