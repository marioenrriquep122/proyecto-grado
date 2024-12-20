# Generated by Django 5.1.4 on 2024-12-20 01:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0002_factura_numero_factura'),
    ]

    operations = [
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('venta', 'Venta realizada'), ('actualizacion', 'Producto actualizado'), ('factura', 'Factura emitida'), ('otro', 'Otro tipo de actividad')], max_length=50, verbose_name='Tipo de Actividad')),
                ('descripcion', models.TextField(verbose_name='Descripción de la Actividad')),
                ('fecha', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de la Actividad')),
            ],
        ),
    ]