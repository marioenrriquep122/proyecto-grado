from django.db import models
from django.conf import settings
import random



# Modelo para Categoría
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la categoría")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.nombre


# Modelo para Productos que se llama equipo material
class EquipoMaterial(models.Model):
    ESTADO_CHOICES = (
        ('disponible', 'Disponible'),
        ('prestado', 'Prestado'),
        ('en_mantenimiento', 'En Mantenimiento'),
        ('retirado', 'Retirado'),
    )

    equipo = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nombre del equipo")
    referencia = models.CharField(max_length=150, blank=True, null=True, verbose_name="Referencia del equipo")
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca del equipo")
    serial = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Número de serie")
    cantidad = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="Cantidad en inventario")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name="Categoría"
    )
    fecha_entrada = models.DateField(verbose_name="Fecha de entrada", null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor", null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        blank=True,
        null=True,
        default='disponible',
        verbose_name="Estado del equipo"
    )

    def __str__(self):
        return f"{self.equipo or 'Sin nombre'} ({self.referencia or 'Sin referencia'}) - {self.estado or 'Sin estado'}"




# Modelo para Reporte
class Reporte(models.Model):
    TIPO_REPORTE_CHOICES = [
        ('general', 'Reporte General'),
        ('personalizado', 'Reporte Personalizado'),
        ('estadistico', 'Reporte Estadístico'),
        ('operativo', 'Reporte Operativo'),
        ('financiero', 'Reporte Financiero'),
            
    ]

    FILTRO_CHOICES = [
        ('facturas', 'Facturas'),
        ('productos', 'Productos'),
        ('categorias', 'Categorías'),
        ('usuarios', 'Usuarios'),
    ]

    tipo = models.CharField(
        max_length=50, 
        choices=TIPO_REPORTE_CHOICES, 
        default='general', 
        verbose_name="Tipo de Reporte"
    )
    filtro = models.CharField(
        max_length=50, 
        choices=FILTRO_CHOICES, 
        verbose_name="Filtro de Datos"
    )
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de Fin")
    datos = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.get_filtro_display()}"

#modelo de factura 
class Factura(models.Model):
    producto = models.ForeignKey('EquipoMaterial', on_delete=models.CASCADE, related_name="facturas")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad", default=1)
    fecha_salida = models.DateField(verbose_name="Fecha de Salida", null=True, blank=True)
    numero_factura = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Número de Factura"
    )

    def save(self, *args, **kwargs):
        if not self.numero_factura:
            self.numero_factura = f"FAC-{random.randint(10000, 99999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Factura {self.numero_factura} - Producto: {self.producto.equipo}"





#modelo de factura

class Actividad(models.Model):
    TIPO_CHOICES = [
        ('venta', 'Venta realizada'),
        ('actualizacion', 'Producto actualizado'),
        ('factura', 'Factura emitida'),
        ('otro', 'Otro tipo de actividad'),
    ]

    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Actividad")
    factura = models.ForeignKey('Factura', on_delete=models.SET_NULL, null=True, blank=True, related_name='actividades', verbose_name="Factura relacionada")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción de la Actividad")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de la Actividad")

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.factura.numero_factura if self.factura else 'Sin factura'}"


   





