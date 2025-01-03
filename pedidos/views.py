from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import Pedido
import json

# Vista para listar todos los pedidos
def listar_pedidos(request):
    pedidos = Pedido.objects.all()
    data = [
        {
            "id": pedido.id,
            "nombre": pedido.nombre,
            "telefono": pedido.telefono,
            "correo": pedido.correo,
            "direccion": pedido.direccion,
            "tipo_reserva": pedido.tipo_reserva,
            "descripcion_reserva": pedido.descripcion_reserva,
            "fecha_reserva": pedido.fecha_reserva,
            "fecha_inicio": pedido.fecha_inicio,
            "fecha_fin": pedido.fecha_fin,
            
        }
        for pedido in pedidos
    ]
    return JsonResponse(data, safe=False)

# Vista para obtener detalles de un pedido
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    data = {
        "id": pedido.id,
        "nombre": pedido.nombre,
        "telefono": pedido.telefono,
        "correo": pedido.correo,
        "direccion": pedido.direccion,
        "tipo_reserva": pedido.tipo_reserva,
        "descripcion_reserva": pedido.descripcion_reserva,
        "fecha_reserva": pedido.fecha_reserva,
        "fecha_inicio": pedido.fecha_inicio,
        "fecha_fin": pedido.fecha_fin,
    }
    return JsonResponse(data)

# Vista para crear un pedido (requiere POST con datos JSON)
@csrf_exempt
def crear_pedido(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        pedido = Pedido.objects.create(
            nombre=data.get('nombre'),
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            direccion=data.get('direccion'),
            tipo_reserva=data.get('tipo_reserva'),
            descripcion_reserva=data.get('descripcion_reserva'),
            fecha_reserva=data.get('fecha_reserva'),
            fecha_inicio=data.get('fecha_inicio'),
            fecha_fin=data.get('fecha_fin')
            
        )
        return JsonResponse({"id": pedido.id, "message": "Pedido creado exitosamente."}, status=201)
    return JsonResponse({"error": "Método no permitido"}, status=405)

# Vista para actualizar un pedido
@csrf_exempt
def actualizar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'PUT':
        data = json.loads(request.body)
        pedido.nombre = data.get('nombre', pedido.nombre)
        pedido.telefono = data.get('telefono', pedido.telefono)
        pedido.correo = data.get('correo', pedido.correo)
        pedido.direccion = data.get('direccion', pedido.direccion)
        pedido.tipo_reserva = data.get('tipo_reserva', pedido.tipo_reserva)
        pedido.descripcion_reserva = data.get('descripcion_reserva', pedido.descripcion_reserva)
        pedido.fecha_reserva = data.get('fecha_reserva', pedido.fecha_reserva)
        pedido.fecha_inicio = data.get('fecha_inicio', pedido.fecha_inicio),
        pedido.fecha_fin = data.get('fecha_fin', pedido.fecha_fin)
        pedido.save()
        return JsonResponse({"id": pedido.id, "message": "Pedido actualizado exitosamente."}, status=200)
    return JsonResponse({"error": "Método no permitido"}, status=405)

# Vista para eliminar un pedido
@csrf_exempt
def eliminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'DELETE':
        pedido.delete()
        return JsonResponse({"message": "Pedido eliminado exitosamente."}, status=200)
    return JsonResponse({"error": "Método no permitido"}, status=405)
