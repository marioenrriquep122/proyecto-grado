from django.db import models

class Pedido(models.Model):
    TIPO_RESERVA_CHOICES = [
        ('camara', 'Camara'),
        ('sonido', 'Sonido'),
        ('audiovisual', 'Audiovisual'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    correo = models.EmailField(verbose_name="Correo Electrónico")
    direccion = models.TextField(verbose_name="Dirección")
    tipo_reserva = models.CharField(max_length=50, choices=TIPO_RESERVA_CHOICES, verbose_name="Tipo de Reserva")
    descripcion_reserva = models.TextField(verbose_name="Descripción de la Reserva")
    fecha_reserva = models.DateTimeField(verbose_name="Fecha de la Reserva")
    fecha_inicio = models.DateField(verbose_name="Entrega de equipos", null=True, blank=True)
    fecha_fin = models.DateField(verbose_name="Regreso de equipos", null=True, blank=True)
    
    

    def __str__(self):
        return f"Pedido de {self.nombre} ({self.tipo_reserva}) el {self.fecha_reserva.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_reserva']
