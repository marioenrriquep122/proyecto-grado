from django.urls import path
from .views import (
    listar_pedidos,
    detalle_pedido,
    crear_pedido,
    actualizar_pedido,
    eliminar_pedido,
)

urlpatterns = [
    path('listar_pedidos/', listar_pedidos, name='listar_pedidos'),
    path('detalle_pedido/<int:pedido_id>/', detalle_pedido, name='detalle_pedido'),
    path('crear_pedido/', crear_pedido, name='crear_pedido'),
    path('actualizar_pedido/<int:pedido_id>/', actualizar_pedido, name='actualizar_pedido'),
    path('eliminar_pedido/<int:pedido_id>/', eliminar_pedido, name='eliminar_pedido'),
]
