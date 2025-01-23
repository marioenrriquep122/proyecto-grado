from rest_framework import serializers
from .models import Actividad, Categoria, EquipoMaterial, Factura, Mantenimiento, Reporte, Resumen, Pedido, ProductoCompra, Compra
from .models import Factura

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class EquipoMaterialSerializer(serializers.ModelSerializer):
    esta_en_mantenimiento = serializers.SerializerMethodField()
    # categoria = serializers.CharField(source='categoria.nombre', read_only=True)
    

    class Meta:
        model = EquipoMaterial
        fields = '__all__'

    def get_esta_en_mantenimiento(self, obj):
        return obj.esta_en_mantenimiento


class ReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = ['id', 'tipo', 'fecha_inicio', 'fecha_fin', 'datos']
        read_only_fields = ['datos']

        
        

class FacturaSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField(help_text="Total calculado basado en la cantidad y el valor unitario")
    stock_restante = serializers.SerializerMethodField(help_text="Stock restante del producto después de la factura")
    numero_factura = serializers.ReadOnlyField()
    equipo = serializers.ReadOnlyField(source="producto.equipo")
    referencia = serializers.ReadOnlyField(source="producto.referencia")
    marca = serializers.ReadOnlyField(source="producto.marca")
    serial = serializers.ReadOnlyField(source="producto.serial")
    descripcion = serializers.ReadOnlyField(source="producto.descripcion")
    fecha_entrada = serializers.ReadOnlyField(source="producto.fecha_entrada")
    valor = serializers.ReadOnlyField(source="producto.valor")
    estado = serializers.ReadOnlyField(source="producto.estado")
    observaciones = serializers.ReadOnlyField(source="producto.observaciones")
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
            'producto',
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

    
    def get_total(self, obj):
        """Calcula el total basado en la cantidad y el valor unitario."""
        if obj.producto:
            return obj.cantidad * float(obj.producto.valor)
        return 0  

    def get_stock_restante(self, obj):
        """Devuelve el stock restante del producto."""
        if obj.producto:
            return obj.producto.cantidad
        return None  

   
    def validate(self, data):
        """
        Valida que el producto sea válido y que haya suficiente stock para la factura.
        """
        producto = data.get('producto')
        cantidad = data.get('cantidad', 0)
        
        if not producto:
            raise serializers.ValidationError("Debe especificar un producto válido para la factura.")

        
        if cantidad <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")

        
        if producto.estado != 'disponible':
            raise serializers.ValidationError(
                f"El producto '{producto.equipo}' no está disponible (Estado actual: {producto.estado})."
            )

        
        if producto.cantidad < cantidad:
            raise serializers.ValidationError(
                f"No hay suficiente stock disponible para el producto '{producto.equipo}'. "
                f"Stock disponible: {producto.cantidad}, cantidad solicitada: {cantidad}."
            )

        return data


    def create(self, validated_data):
        """
        Al crear la factura, reduce el stock del producto.
        """
        producto = validated_data['producto']
        cantidad = validated_data['cantidad']

        
        producto.cantidad -= cantidad
        if producto.cantidad == 0:
            producto.estado = 'retirado'
        producto.save()

       
        factura = Factura.objects.create(**validated_data)
        return factura

    def update(self, instance, validated_data):
        """
        Al actualizar una factura, ajusta el stock del producto.
        """
        producto = instance.producto  
        nueva_cantidad = validated_data.get('cantidad', instance.cantidad)
        cantidad_anterior = instance.cantidad

       
        diferencia = nueva_cantidad - cantidad_anterior

        
        if diferencia > 0:  
            if producto.cantidad < diferencia:
                raise serializers.ValidationError(
                    f"No hay suficiente stock disponible para aumentar la cantidad a {nueva_cantidad}."
                )
            producto.cantidad -= diferencia
        elif diferencia < 0:  
            producto.cantidad += abs(diferencia)

        producto.save()

        
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
            
            return {
                'id': data['id'],
                'tipo': data['tipo'],
                'descripcion': data['descripcion'],
                'fecha': data['fecha'],
                'nombre': data.get('nombre'),
            }

        elif instance.tipo == 'producto':
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
            return {
                'id': data['id'],
                'tipo': data['tipo'],
                'descripcion': data['descripcion'],
                'fecha': data['fecha'],
                'equipo': data.get('equipo'),
            }
            
        elif instance.tipo == 'reporte':
            return {
                'id': data['id'],
                'tipo': data['tipo'],
                'descripcion': "Se ha generado un reporte.",
                'fecha': data['fecha'],
            }
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
        producto = self.instance.producto if self.instance else data.get('producto')
        estado = data.get('estado', self.instance.estado if self.instance else None)

        if estado == 'completado' and producto.estado != 'en_mantenimiento':
            raise serializers.ValidationError(
                f"El producto '{producto.equipo}' no está en mantenimiento y no puede marcarse como completado."
            )

        return data


class ResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resumen
        fields = ['id']





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



class ProductoCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoCompra
        fields = [
            'id', 'compra', 'equipo', 'referencia', 'marca', 'serial', 
            'cantidad', 'descripcion', 'fecha_entrada', 'fecha_salida', 
            'estado', 'observaciones', 'poliza', 'valor'
        ]


from rest_framework import serializers
from .models import Compra, ProductoCompra

class CompraSerializer(serializers.ModelSerializer):
    productos = ProductoCompraSerializer(many=True, read_only=True)  # Productos anidados

    class Meta:
        model = Compra
        fields = ['id', 'factura', 'descripcion', 'fecha_creacion', 'productos']
        
        





