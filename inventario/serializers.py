from rest_framework import serializers
from .models import Categoria, EquipoMaterial, Factura, Reporte


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class EquipoMaterialSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model = EquipoMaterial
        fields = '__all__'




class ReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = '__all__'
        
        
        
        




from rest_framework import serializers
from .models import Factura

class FacturaSerializer(serializers.ModelSerializer):
    # Campos calculados
    total = serializers.SerializerMethodField(help_text="Total calculado basado en la cantidad y el valor unitario")
    stock_restante = serializers.SerializerMethodField(help_text="Stock restante del producto después de la factura")

    # Campos relacionados con el producto
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
            'total',  # Campo calculado
            'stock_restante'  # Campo calculado
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
        producto = instance.producto  # Producto relacionado con la factura
        nueva_cantidad = validated_data.get('cantidad', instance.cantidad)
        cantidad_anterior = instance.cantidad  # Cantidad antes de actualizar

        # Calcula la diferencia de stock
        diferencia = nueva_cantidad - cantidad_anterior

        if diferencia > 0:  # Si se aumenta la cantidad, verificamos el stock
            if producto.cantidad < diferencia:
                raise serializers.ValidationError("No hay suficiente stock disponible para esta cantidad.")
            producto.cantidad -= diferencia  # Reducimos el stock

        elif diferencia < 0:  # Si se reduce la cantidad, devolvemos stock
            producto.cantidad += abs(diferencia)

        producto.save()  # Guardar cambios en el stock

        # Actualizamos los datos de la factura
        instance.cantidad = nueva_cantidad
        instance.fecha_salida = validated_data.get('fecha_salida', instance.fecha_salida)
        instance.save()

        return instance
