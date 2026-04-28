from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout 
from .models import OrdenTrabajo, Personal

# --- VISTA DE TAREAS ---
# Si no hay sesión, rebota al login de operarios (NO al admin)
@login_required(login_url='/inventario/login/')
def lista_tareas_personal(request):
    try:
        operario = Personal.objects.get(user=request.user)
        ordenes = OrdenTrabajo.objects.filter(personal_asignado=operario, finalizado=False).order_by('-fecha_inicio')
    except Personal.DoesNotExist:
        ordenes = OrdenTrabajo.objects.all().order_by('-fecha_inicio')

    return render(request, 'inventario/tareas_operario.html', {'ordenes': ordenes})

# --- VISTA PARA MARCAR TAREAS ---
@login_required(login_url='/inventario/login/')
def marcar_tarea(request, ot_id, tarea):
    ot = get_object_or_404(OrdenTrabajo, id=ot_id)
    
    valor_actual = getattr(ot, tarea)
    setattr(ot, tarea, not valor_actual)
    
    if ot.corte and ot.canteado and ot.armado and ot.limpieza and ot.empaquetado:
        ot.finalizado = True
        if not ot.fecha_fin:
            ot.fecha_fin = timezone.now()
    else:
        ot.finalizado = False
        ot.fecha_fin = None
        
    ot.save()
    return redirect('lista_tareas')

# --- VISTA DE SALIDA (Para asegurar el redireccionamiento) ---
def salir_limpio(request):
    logout(request)
    return redirect('/inventario/login/')