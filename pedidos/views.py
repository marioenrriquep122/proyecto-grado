from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from pedidos.serializers import PedidoSerializer
from .models import Pedido
import json

from rest_framework.response import Response  # Maneja respuestas personalizadas
from rest_framework.viewsets import ModelViewSet  # Maneja operaciones CRUD
from rest_framework import status  # Códigos de estado HTTP
from .models import Pedido
from .serializers import PedidoSerializer



class PedidoViewSet(ModelViewSet):
    """
    ViewSet para gestionar las operaciones CRUD de los pedidos.
    """
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer

    def list(self, request, *args, **kwargs):
        pedidos = Pedido.objects.all()
        serializer = self.get_serializer(pedidos, many=True)
        return Response(serializer.data)
    
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Pedido creado exitosamente.",
                "pedido": serializer.data  
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def retrieve(self, request, pk=None, *args, **kwargs):
        pedido = self.get_object()
        serializer = self.get_serializer(pedido)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        pedido = self.get_object()
        serializer = self.get_serializer(pedido, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Pedido actualizado exitosamente.",
            "pedido": serializer.data  # Incluye los datos actualizados del pedido
        },
        status=status.HTTP_200_OK
    )

    def destroy(self, request, pk=None, *args, **kwargs):
        pedido = self.get_object()
        self.perform_destroy(pedido)
        return Response({"message": "Pedido eliminado exitosamente."}, status=status.HTTP_200_OK)



# Vista para listar todos los pedidos
# def listar_pedidos(request):
#     pedidos = Pedido.objects.all()
#     data = [
#         {
#             "id": pedido.id,
#             "nombre": pedido.nombre,
#             "telefono": pedido.telefono,
#             "correo": pedido.correo,
#             "direccion": pedido.direccion,
#             "tipo_reserva": pedido.tipo_reserva,
#             "descripcion_reserva": pedido.descripcion_reserva,
#             "fecha_reserva": pedido.fecha_reserva,
#             "fecha_inicio": pedido.fecha_inicio,
#             "fecha_fin": pedido.fecha_fin,
            
#         }
#         for pedido in pedidos
#     ]
#     return JsonResponse(data, safe=False)

# # Vista para obtener detalles de un pedido
# def detalle_pedido(request, pedido_id):
#     pedido = get_object_or_404(Pedido, id=pedido_id)
#     data = {
#         "id": pedido.id,
#         "nombre": pedido.nombre,
#         "telefono": pedido.telefono,
#         "correo": pedido.correo,
#         "direccion": pedido.direccion,
#         "tipo_reserva": pedido.tipo_reserva,
#         "descripcion_reserva": pedido.descripcion_reserva,
#         "fecha_reserva": pedido.fecha_reserva,
#         "fecha_inicio": pedido.fecha_inicio,
#         "fecha_fin": pedido.fecha_fin,
#     }
#     return JsonResponse(data)

# # Vista para crear un pedido (requiere POST con datos JSON)
# @csrf_exempt
# def crear_pedido(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         pedido = Pedido.objects.create(
#             nombre=data.get('nombre'),
#             telefono=data.get('telefono'),
#             correo=data.get('correo'),
#             direccion=data.get('direccion'),
#             tipo_reserva=data.get('tipo_reserva'),
#             descripcion_reserva=data.get('descripcion_reserva'),
#             fecha_reserva=data.get('fecha_reserva'),
#             fecha_inicio=data.get('fecha_inicio'),
#             fecha_fin=data.get('fecha_fin')
            
#         )
#         return JsonResponse({"id": pedido.id, "message": "Pedido creado exitosamente."}, status=201)
#     return JsonResponse({"error": "Método no permitido"}, status=405)

# # Vista para actualizar un pedido
# @csrf_exempt
# def actualizar_pedido(request, pedido_id):
#     pedido = get_object_or_404(Pedido, id=pedido_id)
#     if request.method == 'PUT':
#         data = json.loads(request.body)
#         pedido.nombre = data.get('nombre', pedido.nombre)
#         pedido.telefono = data.get('telefono', pedido.telefono)
#         pedido.correo = data.get('correo', pedido.correo)
#         pedido.direccion = data.get('direccion', pedido.direccion)
#         pedido.tipo_reserva = data.get('tipo_reserva', pedido.tipo_reserva)
#         pedido.descripcion_reserva = data.get('descripcion_reserva', pedido.descripcion_reserva)
#         pedido.fecha_reserva = data.get('fecha_reserva', pedido.fecha_reserva)
#         pedido.fecha_inicio = data.get('fecha_inicio', pedido.fecha_inicio),
#         pedido.fecha_fin = data.get('fecha_fin', pedido.fecha_fin)
#         pedido.save()
#         return JsonResponse({"id": pedido.id, "message": "Pedido actualizado exitosamente."}, status=200)
#     return JsonResponse({"error": "Método no permitido"}, status=405)

# # Vista para eliminar un pedido
# @csrf_exempt
# def eliminar_pedido(request, pedido_id):
#     pedido = get_object_or_404(Pedido, id=pedido_id)
#     if request.method == 'DELETE':
#         pedido.delete()
#         return JsonResponse({"message": "Pedido eliminado exitosamente."}, status=200)
#     return JsonResponse({"error": "Método no permitido"}, status=405)
