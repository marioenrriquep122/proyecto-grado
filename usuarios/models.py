from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):

    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=False, null=False)
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('usuario', 'Usuario'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='cliente')
    is_active = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.rol})"
