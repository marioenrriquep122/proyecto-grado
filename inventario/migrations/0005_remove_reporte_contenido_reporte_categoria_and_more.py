# Generated by Django 5.1.4 on 2024-12-22 13:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0004_actividad_factura_alter_actividad_descripcion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reporte',
            name='contenido',
        ),
        migrations.AddField(
            model_name='reporte',
            name='categoria',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventario.categoria'),
        ),
        migrations.AddField(
            model_name='reporte',
            name='producto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventario.equipomaterial', verbose_name='Producto relacionado'),
        ),
        migrations.AlterField(
            model_name='reporte',
            name='tipo',
            field=models.CharField(choices=[('general', 'Reporte General'), ('ventas', 'Reporte de Ventas'), ('inventario', 'Reporte de Inventario'), ('usuarios', 'Reporte de Usuarios'), ('mantenimiento', 'Reporte de Mantenimiento'), ('movimientos', 'Reporte de Movimientos')], default='2024-01-01', max_length=50),
            preserve_default=False,
        ),
    ]
