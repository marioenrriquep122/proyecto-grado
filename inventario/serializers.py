from rest_framework import serializers
from .models import Actividad, Categoria, EquipoMaterial, Factura, Mantenimiento, Reporte, Resumen
from .models import Factura

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class EquipoMaterialSerializer(serializers.ModelSerializer):
    esta_en_mantenimiento = serializers.SerializerMethodField()
    fecha_salida = serializers.SerializerMethodField()

    class Meta:
        model = EquipoMaterial
        fields = '__all__'

    def get_esta_en_mantenimiento(self, obj):
        return obj.esta_en_mantenimiento

    def get_fecha_salida(self, obj):
        # Asegúrate de que obj.factura no sea None antes de acceder
        return obj.factura.fecha_salida if obj.factura else None





class ReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = ['id', 'tipo', 'fecha_inicio', 'fecha_fin', 'datos']
        read_only_fields = ['datos']

        
        

class FacturaSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField(help_text="Total calculado basado en la cantidad y el valor unitario")
    stock_restante = serializers.SerializerMethodField(help_text="Stock restante del equipo después de la factura")

    productos = EquipoMaterialSerializer(many=True, read_only=True)  # Productos relacionados

    # Campos relacionados con el equipo (EquipoMaterial)
    equipo = serializers.SerializerMethodField()
    referencia = serializers.SerializerMethodField()
    marca = serializers.SerializerMethodField()
    serial = serializers.SerializerMethodField()
    descripcion = serializers.SerializerMethodField()
    fecha_entrada = serializers.SerializerMethodField()
    valor = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()
    observaciones = serializers.SerializerMethodField()

    nombre_cliente = serializers.CharField(max_length=100)
    compania_cliente = serializers.CharField(max_length=100, required=False, allow_blank=True)
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True)
    barrio = serializers.CharField(max_length=100, required=False, allow_blank=True)
    telefono = serializers.CharField(max_length=15, required=False, allow_blank=True)

    class Meta:
        model = Factura
        fields = [
            'id',
            'numero_factura',
            'productos',  # Lista de productos anidados (opcional en creación)
            'equipo',
            'referencia',
            'marca',
            'serial',
            'cantidad',
            'descripcion',
            'fecha_entrada',
            'fecha_salida',
            'estado',
            'observaciones',
            'valor',
            'total',
            'stock_restante',
            'nombre_cliente',
            'compania_cliente',
            'direccion',
            'barrio',
            'telefono',
        ]

    def get_equipo(self, obj):
        return ", ".join([producto.equipo for producto in obj.productos.all()])

    def get_referencia(self, obj):
        return ", ".join([producto.referencia for producto in obj.productos.all()])

    def get_marca(self, obj):
        return ", ".join([producto.marca for producto in obj.productos.all()])

    def get_serial(self, obj):
        return ", ".join([producto.serial for producto in obj.productos.all()])

    def get_descripcion(self, obj):
        return ", ".join([producto.descripcion for producto in obj.productos.all()])

    def get_fecha_entrada(self, obj):
        return ", ".join([str(producto.fecha_entrada) for producto in obj.productos.all()])

    def get_valor(self, obj):
        return sum([producto.valor for producto in obj.productos.all()])

    def get_estado(self, obj):
        return ", ".join([producto.estado for producto in obj.productos.all()])

    def get_observaciones(self, obj):
        return ", ".join([producto.observaciones for producto in obj.productos.all()])

    def get_total(self, obj):
        """Calcula el total basado en los productos asociados."""
        return sum(producto.cantidad * producto.valor for producto in obj.productos.all())

    def get_stock_restante(self, obj):
        """Calcula el stock restante para los productos asociados."""
        return sum(producto.cantidad for producto in obj.productos.all())

    def validate(self, data):
        """Valida que haya suficiente stock para los productos en la factura."""
        productos = data.get('productos', [])  # Productos son opcionales
        cantidad = data.get('cantidad', 0)

        for producto in productos:
            if producto.cantidad < cantidad:
                raise serializers.ValidationError(
                    f"No hay suficiente stock disponible para el producto {producto.equipo}."
                )
        return data

    def create(self, validated_data):
        """Crea una factura, incluso si no hay productos asociados inicialmente."""
        productos = validated_data.pop('productos', [])  # Productos son opcionales
        factura = Factura.objects.create(**validated_data)

        # Asociar productos si se incluyen
        if productos:
            for producto in productos:
                if producto.cantidad < validated_data.get('cantidad', 0):
                    raise serializers.ValidationError(
                        f"No hay suficiente stock disponible para el producto {producto.equipo}."
                    )
                producto.cantidad -= validated_data.get('cantidad', 0)
                producto.save()
            factura.productos.set(productos)

        return factura

    def update(self, instance, validated_data):
        """Actualiza la factura y ajusta el stock de los productos."""
        productos = validated_data.pop('productos', [])
        nueva_cantidad = validated_data.get('cantidad', instance.cantidad)
        cantidad_anterior = instance.cantidad

        diferencia = nueva_cantidad - cantidad_anterior

        # Ajustar stock de los productos asociados
        for producto in productos:
            if diferencia > 0:  # Incrementa la cantidad
                if producto.cantidad < diferencia:
                    raise serializers.ValidationError(
                        f"No hay suficiente stock disponible para el producto {producto.equipo}."
                    )
                producto.cantidad -= diferencia
            elif diferencia < 0:  # Reduce la cantidad
                producto.cantidad += abs(diferencia)
            producto.save()

        # Actualizar los productos asociados
        if productos:
            instance.productos.set(productos)

        # Actualizar otros campos de la factura
        instance.cantidad = nueva_cantidad
        instance.fecha_salida = validated_data.get('fecha_salida', instance.fecha_salida)
        instance.nombre_cliente = validated_data.get('nombre_cliente', instance.nombre_cliente)
        instance.compania_cliente = validated_data.get('compania_cliente', instance.compania_cliente)
        instance.direccion = validated_data.get('direccion', instance.direccion)
        instance.barrio = validated_data.get('barrio', instance.barrio)
        instance.telefono = validated_data.get('telefono', instance.telefono)
        instance.save()

        return instance

    

class ActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actividad
        fields = [
            'id', 'tipo', 'descripcion', 'fecha', 'nombre', 'equipo', 'marca', 'cantidad',
            'valor', 'valor_total', 'numero_factura', 'nombre_cliente'
        ]

    def to_representation(self, instance):
        """
        Mostrar campos específicos según el tipo de actividad.
        """
        data = super().to_representation(instance)

        if instance.tipo == 'categoria':
            # Solo mostrar datos relevantes para categorías
            return {
                'id': data['id'],
                'tipo': data['tipo'],
                'descripcion': data['descripcion'],
                'fecha': data['fecha'],
                'nombre': data.get('nombre'),
            }

        elif instance.tipo == 'producto':
            # Solo mostrar datos relevantes para productos
            return {
                'id': data['id'],
                'tipo': data['tipo'],
                'descripcion': data['descripcion'],
                'fecha': data['fecha'],
                'equipo': data.get('equipo'),
                'marca': data.get('marca'),
                'cantidad': data.get('cantidad'),
                'valor': data.get('valor'),
            }

        elif instance.tipo == 'factura':
            # Solo mostrar datos relevantes para facturas
            return {
                'id': data['id'],
                'tipo': data['tipo'],
                'descripcion': data['descripcion'],
                'fecha': data['fecha'],
                'numero_factura': data.get('numero_factura'),
                'nombre_cliente': data.get('nombre_cliente'),
                'cantidad': data.get('cantidad'),
                'valor': data.get('valor'),
                'valor_total': data.get('valor_total'),
            }

        elif instance.tipo == 'mantenimiento':
            # Solo mostrar datos relevantes para mantenimiento
            return {
                'id': data['id'],
                'tipo': data['tipo'],
                'descripcion': data['descripcion'],
                'fecha': data['fecha'],
                'equipo': data.get('equipo'),
            }
            
        elif instance.tipo == 'reporte':
            # Solo mostrar campos relevantes para reportes
            return {
                'id': data['id'],
                'tipo': data['tipo'],
                'descripcion': "Se ha generado un reporte.",
                'fecha': data['fecha'],
            }

        # Devolver todos los datos para tipos no especificados
        return data





        
      

class MantenimientoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.equipo', read_only=True)

    class Meta:
        model = Mantenimiento
        fields = [
            'id',
            'producto',
            'producto_nombre',
            'descripcion',
            'fecha_inicio',
            'fecha_fin',
            'estado',
            'costo',
        ]

    def validate(self, data):
        # Validar que el estado "completado" solo se puede asignar si corresponde
        producto = self.instance.producto if self.instance else data.get('producto')
        estado = data.get('estado', self.instance.estado if self.instance else None)

        if estado == 'completado' and producto.estado != 'en_mantenimiento':
            raise serializers.ValidationError(
                f"El producto '{producto.equipo}' no está en mantenimiento y no puede marcarse como completado."
            )

        return data


    




from rest_framework import serializers
from .models import Resumen

class ResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resumen
        fields = ['id']



from rest_framework import serializers
from .models import Pedido

class PedidoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    producto_nombre = serializers.CharField(source='producto.equipo', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'nombre_cliente', 'telefono', 'correo', 'direccion', 'barrio', 
            'nombre_compania', 'descripcion', 'fecha_reserva', 'fecha_inicio', 
            'fecha_fin', 'cantidad', 'estado', 'categoria', 'producto', 
            'categoria_nombre', 'producto_nombre'
        ]








