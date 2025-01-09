from rest_framework import serializers
from .models import Actividad, Categoria, EquipoMaterial, Factura, Mantenimiento, Reporte, Resumen
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

    # Métodos para los campos calculados
    def get_total(self, obj):
        """Calcula el total basado en la cantidad y el valor unitario."""
        return obj.cantidad * float(obj.producto.valor)

    def get_stock_restante(self, obj):
        """Devuelve el stock restante del producto."""
        return obj.producto.cantidad

    # Validación personalizada
    def validate(self, data):
        producto = data['producto']
        cantidad = data['cantidad']

        if producto.cantidad < cantidad:
            raise serializers.ValidationError("No hay suficiente stock disponible para esta cantidad.")
        return data

    def create(self, validated_data):
        """
        Al crear la factura, reduce el stock del producto.
        """
        producto = validated_data['producto']
        cantidad = validated_data['cantidad']

        # Reducir el stock
        if producto.cantidad < cantidad:
            raise serializers.ValidationError("No hay suficiente stock disponible.")
        producto.cantidad -= cantidad
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
                raise serializers.ValidationError("No hay suficiente stock disponible para esta cantidad.")
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
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    factura_numero = serializers.CharField(source='factura.numero_factura', read_only=True)

    class Meta:
        model = Actividad
        fields = [
            'id',
            'tipo',           
            'tipo_display',   
            'factura',        
            'factura_numero',
            'descripcion',    
            'fecha',          
        ]
        
        
      

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







