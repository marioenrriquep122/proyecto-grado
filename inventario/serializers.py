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
        
        
        
        




class FacturaSerializer(serializers.ModelSerializer):
    # Detalles del producto relacionados
    equipo = serializers.ReadOnlyField(source="producto.equipo", help_text="Nombre del equipo")
    referencia = serializers.ReadOnlyField(source="producto.referencia", help_text="Referencia del equipo")
    marca = serializers.ReadOnlyField(source="producto.marca", help_text="Marca del equipo")
    serial = serializers.ReadOnlyField(source="producto.serial", help_text="Número de serie del equipo")
    descripcion = serializers.ReadOnlyField(source="producto.descripcion", help_text="Descripción del equipo")
    fecha_entrada = serializers.ReadOnlyField(source="producto.fecha_entrada", help_text="Fecha de entrada al inventario")
    valor = serializers.ReadOnlyField(source="producto.valor", help_text="Valor unitario del equipo")
    estado = serializers.ReadOnlyField(source="producto.estado", help_text="Estado del equipo")
    observaciones = serializers.ReadOnlyField(source="producto.observaciones", help_text="Observaciones del equipo")
    
    # Detalles específicos de la factura
    total = serializers.SerializerMethodField(help_text="Total calculado basado en la cantidad y el valor unitario")

    class Meta:
        model = Factura
        fields = [
            'id',  
            'numero_factura',  # Campo agregado
            'equipo', 
            'producto',
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
            'total'
        ]
        read_only_fields = [
            'numero_factura',  # Solo lectura
            'equipo', 
            'referencia', 
            'marca', 
            'serial', 
            'descripcion', 
            'fecha_entrada', 
            'estado', 
            'observaciones', 
            'valor'
        ]

    def get_total(self, obj):
        return obj.cantidad * float(obj.producto.valor)



