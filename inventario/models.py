from django.db import models

# Modelo para Categoría
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la categoría")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.nombre


# Modelo para EquipoMaterial
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
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    contenido = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Reporte {self.tipo or 'Sin tipo'} - {self.fecha_creacion}"





#modelo de factura 


import random
from django.db import models

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






