from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout 
from .models import OrdenTrabajo, Personal
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404
from .models import Factura
# ==============================================================================
# --- 1. PANEL DE TAREAS DEL TALLER ---
# ==============================================================================
@login_required(login_url='/inventario/login/')
def lista_tareas_personal(request):
    """
    Muestra las órdenes de trabajo pendientes asignadas al operario logueado.
    """
    try:
        # Buscamos el perfil de Personal vinculado al usuario de Django
        operario = Personal.objects.get(user=request.user)
        # Filtramos las órdenes donde este operario está asignado y no han finalizado
        ordenes = OrdenTrabajo.objects.filter(
            personal_asignado=operario, 
            finalizado=False
        ).order_by('-fecha_inicio').distinct()
    except Personal.DoesNotExist:
        # Si el usuario es un administrador o no tiene perfil de Personal, ve todas las pendientes
        ordenes = OrdenTrabajo.objects.filter(finalizado=False).order_by('-fecha_inicio')

    return render(request, 'inventario/tareas_operario.html', {'ordenes': ordenes})

# ==============================================================================
# --- 2. ACCIÓN DE MARCAR TAREAS ---
# ==============================================================================


@login_required(login_url='/inventario/login/')
def marcar_tarea(request, ot_id, tarea):
    ot = get_object_or_404(OrdenTrabajo, id=ot_id)
    
    # 1. Intentamos marcar como completado
    setattr(ot, tarea, True)
    
    try:
        # 2. Al llamar a save(), se ejecuta el clean() que pusimos en el modelo
        ot.save()
        messages.success(request, f"¡{tarea.capitalize()} registrado con éxito!")
    except ValidationError as e:
        # Extraemos solo el mensaje de texto, eliminando los símbolos de diccionario
        if hasattr(e, 'message_dict'):
            # Si el error viene como diccionario, tomamos el primer mensaje
            mensaje = e.message_dict.get('__all__', [str(e)])[0]
        else:
            # Si viene como lista o string, lo limpiamos
            mensaje = str(e).strip("[]'{}")
        
        messages.error(request, mensaje)
    except Exception as e:
        messages.error(request, "Error al actualizar la tarea.")

    return redirect('lista_tareas') # Asegúrate que este sea el nombre de tu URL del panel

# ==============================================================================
# --- 3. GESTIÓN DE CIERRE DE SESIÓN ---
# ==============================================================================
def salir_limpio(request):
    """
    Cierra la sesión del operario y lo redirige al login del taller.
    """
    logout(request)
    return redirect('/inventario/login/')

def factura_detalle_view(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    return render(request, 'inventario/factura_detalle.html', {'factura': factura})