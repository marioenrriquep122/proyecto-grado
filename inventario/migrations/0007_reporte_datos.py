# Generated by Django 5.1.4 on 2024-12-22 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0006_remove_reporte_categoria_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporte',
            name='datos',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]