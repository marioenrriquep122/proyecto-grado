from .models import Actividad

def registrar_actividad(
    tipo, descripcion, fecha=None, nombre=None, equipo=None, marca=None, cantidad=None, 
    valor=None, valor_total=None, numero_factura=None, nombre_cliente=None
):
    """
    Función para registrar actividades.
    :param tipo: Tipo de actividad (categoría, producto, factura, etc.)
    :param descripcion: Mensaje descriptivo de la actividad
    :param fecha: Fecha de la actividad
    :param nombre: Nombre asociado (solo para categorías)
    :param equipo: Nombre del equipo o producto relacionado con la actividad
    :param marca: Marca del equipo o producto
    :param cantidad: Cantidad relacionada con la actividad
    :param valor: Valor unitario
    :param valor_total: Valor total
    :param numero_factura: Número de la factura
    :param nombre_cliente: Nombre del cliente asociado
    """
    Actividad.objects.create(
        tipo=tipo,
        descripcion=descripcion,
        fecha=fecha,
        nombre=nombre if tipo == 'categoria' else None,
        equipo=equipo if tipo in ['producto', 'factura', 'mantenimiento'] else None,  # Asegurarse de incluir 'mantenimiento'
        marca=marca if tipo in ['producto', 'factura'] else None,
        cantidad=cantidad if tipo in ['producto', 'factura'] else None,
        valor=valor if tipo in ['producto', 'factura'] else None,
        valor_total=valor_total if tipo == 'factura' else None,
        numero_factura=numero_factura if tipo == 'factura' else None,
        nombre_cliente=nombre_cliente if tipo == 'factura' else None
    )



