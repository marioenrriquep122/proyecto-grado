from datetime import date
from django.db import models
from django.conf import settings
import random

from django.forms import ValidationError



# Modelo para Categoría---
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la categoría")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.nombre


# Modelo para Productos que se llama equipo material
class EquipoMaterial(models.Model):
    ESTADO_CHOICES = (
        ('disponible', 'Disponible'),
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
        'Categoria',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='productos',
        verbose_name="Categoría"
    )
    fecha_entrada = models.DateField(verbose_name="Fecha de entrada", null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor", null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    fac = models.CharField(max_length=50, blank=True, null=True, verbose_name="Factura")  # Nuevo campo
    valor_factura = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor de la factura", null=True, blank=True)  # Nuevo campo
    poliza = models.BooleanField(default=False, verbose_name="¿Tiene póliza?")  # Nuevo campo
    fecha_salidas = models.DateField(verbose_name="Fecha de salidas", null=True, blank=True)  # Nuevo campo
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='disponible',
        verbose_name="Estado del equipo"
    )

    @property
    def esta_en_mantenimiento(self):
        """
        Verifica si el producto está marcado como en mantenimiento.
        """
        return self.estado == 'en_mantenimiento'

    def save(self, *args, **kwargs):
        if self.esta_en_mantenimiento and self.estado != 'en_mantenimiento':
            raise ValueError("El producto no puede estar marcado como en mantenimiento si su estado no es 'en_mantenimiento'.")
        if self.cantidad == 0:
            self.estado = 'retirado'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.equipo} - {self.marca} ({self.serial})"



# Modelo para Reporte
class Reporte(models.Model):
    TIPO_REPORTE_CHOICES = [
        ('general', 'Reporte General'),
        ('stock', 'Reporte de Stock'),
        ('factura', 'Reporte de Facturas'),
        ('actividades', 'Reporte de Actividades'),
    ]

    tipo = models.CharField(
        max_length=50,
        choices=TIPO_REPORTE_CHOICES,
        verbose_name="Tipo de Reporte"
    )
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de Fin")
    datos = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_inicio} a {self.fecha_fin}"

    
    
    

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
    nombre_cliente = models.CharField(max_length=100, verbose_name="Nombre del Cliente")
    compania_cliente = models.CharField(max_length=100, verbose_name="Compañía del Cliente", blank=True, null=True)
    direccion = models.CharField(max_length=255, verbose_name="Dirección", blank=True, null=True)
    barrio = models.CharField(max_length=100, verbose_name="Barrio", blank=True, null=True)
    telefono = models.CharField(max_length=15, verbose_name="Teléfono", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.numero_factura:
            self.numero_factura = f"FAC-{random.randint(10000, 99999)}"
        super().save(*args, **kwargs)

    def get_producto(self):
        """Devuelve el producto relacionado o un mensaje indicando que no está asignado."""
        try:
            return self.producto
        except self.producto.RelatedObjectDoesNotExist:
            return None

    def __str__(self):
        producto = self.get_producto()
        if producto:
            return f"Factura {self.numero_factura} - Producto: {producto.equipo}"
        return f"Factura {self.numero_factura} - Producto: No asignado"







#modelo de actividad

class Actividad(models.Model):
    TIPO_CHOICES = [
        ('categoria', 'Categoría'),
        ('producto', 'Producto'),
        ('factura', 'Factura'),
        ('pedido', 'Pedido'),
        ('mantenimiento', 'Mantenimiento'),
        ('resumen', 'Resumen'),
        ('reporte', 'Reporte'),
    ]

    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Actividad")
    descripcion = models.TextField(verbose_name="Descripción de la Actividad")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de la Actividad")
    nombre = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nombre Asociado")  
    equipo = models.CharField(max_length=255, null=True, blank=True, verbose_name="Equipo")  
    marca = models.CharField(max_length=255, null=True, blank=True, verbose_name="Marca")    
    cantidad = models.IntegerField(null=True, blank=True, verbose_name="Cantidad")          
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Total")
    numero_factura = models.CharField(max_length=50, null=True, blank=True, verbose_name="Número de Factura")
    nombre_cliente = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nombre del Cliente")

    

    def __str__(self):
        return f"[{self.tipo}] {self.descripcion[:30]} ({self.fecha})"




    
    
    #mantenimiento 
class Mantenimiento(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
    ]

    producto = models.ForeignKey(
        'EquipoMaterial',
        on_delete=models.CASCADE,
        related_name='mantenimientos',
        verbose_name="Producto"
    )
    descripcion = models.TextField(verbose_name="Descripción del Mantenimiento")
    fecha_inicio = models.DateField(auto_now_add=True, verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(blank=True, null=True, verbose_name="Fecha de Fin")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name="Estado"
    )
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Costo del Mantenimiento"
    )

    def save(self, *args, **kwargs):
        
        if self.estado == 'completado':
            self.producto.estado = 'disponible'
        elif self.estado in ['pendiente', 'en_proceso']:
            self.producto.estado = 'en_mantenimiento'
        self.producto.save()  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mantenimiento: {self.producto.equipo} - {self.get_estado_display()}"

#nada




class Resumen(models.Model):
    def __str__(self):
        return "Resumen único del sistema"
    
    


class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('no_disponible', 'No Disponible'),
        ('en_proceso', 'En Proceso'),
        ('terminado', 'Terminado'),
    ]
    nombre_cliente = models.CharField(max_length=255, verbose_name="Nombre del Cliente")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    correo = models.EmailField(verbose_name="Correo Electrónico")
    direccion = models.TextField(verbose_name="Dirección")
    barrio = models.CharField(max_length=255, verbose_name="Barrio")
    nombre_compania = models.CharField(max_length=255, verbose_name="Nombre de la Compañía")

    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.CASCADE,
        related_name='pedidos',
        verbose_name="Categoría"
    )
    producto = models.ForeignKey(
        'EquipoMaterial',
        on_delete=models.CASCADE,
        related_name='pedidos',
        verbose_name="Producto"
    )

    
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_reserva = models.DateField(verbose_name="Fecha de Reserva")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='disponible',
        verbose_name="Estado del Pedido"
    )

    def __str__(self):
        return f"Pedido de {self.nombre_cliente} ({self.estado})"





from django.db import models

class Compra(models.Model):
    factura = models.CharField(max_length=50, blank=True, null=True, verbose_name="Factura")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción de la Compra")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    def __str__(self):
        return f"Compra {self.factura or 'Sin Factura'}"

class ProductoCompra(models.Model):
    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name="productos",
        verbose_name="Compra"
    )
    equipo = models.CharField(max_length=150, verbose_name="Nombre del equipo")
    referencia = models.CharField(max_length=150, blank=True, null=True, verbose_name="Referencia del equipo")
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca del equipo")
    serial = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de serie")
    cantidad = models.PositiveIntegerField(blank=True, null=True, verbose_name="Cantidad")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_entrada = models.DateField(blank=True, null=True, verbose_name="Fecha de Entrada")
    fecha_salida = models.DateField(blank=True, null=True, verbose_name="Fecha de Salida")
    estado = models.CharField(max_length=50, blank=True, null=True, verbose_name="Estado")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    poliza = models.BooleanField(default=False, verbose_name="¿Tiene Póliza?")
    valor = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Valor")

    def __str__(self):
        return f"{self.equipo or 'Sin Equipo'} ({self.compra.factura or 'Sin Factura'})"





















   





