import csv
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe # Agregado para mark_safe
from django.http import HttpResponse
from .models import Insumo as ModeloInsumo, Mueble, Pieza, Receta, Cliente, Pedido, Tarea

# ==============================================================================
# --- 1. PANEL DEL CARPINTERO (TAREAS) ---
# ==============================================================================
@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    # Definimos qué columnas ver en la lista de tareas
    list_display = ('nombre_con_color', 'mostrar_mueble', 'pedido', 'terminado', 'fecha_fin')
    list_filter = ('terminado', 'nombre', 'pedido__mueble__nombre')
    list_editable = ('terminado',) # Permite marcar como terminado desde la lista
    search_fields = ('pedido__cliente__nombre', 'pedido__mueble__nombre', 'nombre')
    ordering = ('pedido', 'id') 

    # Función 1: Muestra el nombre de la tarea con iconos y colores según el estado
    def nombre_con_color(self, obj):
        etiqueta = obj.get_nombre_display()
        if obj.terminado:
            return format_html('<span style="color: #2ecc71; font-weight: bold;">✅ {}</span>', etiqueta)
        return format_html('<span style="color: #e67e22; font-weight: bold;">⏳ {}</span>', etiqueta)
    nombre_con_color.admin_order_field = 'id' # Permite ordenar por ID usando esta columna
    nombre_con_color.short_description = 'ESTADO DE TAREA'

    # Función 2: Muestra el nombre del mueble asociado a la tarea en azul y mayúsculas
    def mostrar_mueble(self, obj):
        # Esta función busca el nombre del mueble a través del pedido
        return format_html('<b style="color: #3498db; text-transform: uppercase;">{}</b>', obj.pedido.mueble.nombre)
    mostrar_mueble.short_description = 'MUEBLE'

# ==============================================================================
# --- 2. CONFIGURACIÓN DE TABLAS HIJAS (INLINES) ---
# ==============================================================================
# Estas clases permiten editar las tablas hijas dentro del formulario de la tabla padre

class TareaInline(admin.TabularInline):
    model = Tarea
    extra = 0 # No mostrar filas vacías por defecto
    can_delete = False # No permitir borrar tareas desde el pedido
    fields = ('nombre', 'terminado', 'fecha_fin', 'tiempo') # Campos visibles

class PiezaInline(admin.TabularInline):
    model = Pieza
    extra = 1 # Mostrar 1 fila vacía para agregar una pieza nueva

class RecetaInline(admin.TabularInline):
    model = Receta
    extra = 1 # Mostrar 1 fila vacía para agregar un insumo nuevo

# ==============================================================================
# --- 3. PANEL DE MUEBLES ---
# ==============================================================================
@admin.register(Mueble)
class MuebleAdmin(admin.ModelAdmin):
    # Definimos qué columnas ver en la lista de muebles, incluyendo el STOCK DISPONIBLE
    list_display = ('nombre', 'codigo', 'mostrar_porcentaje_uso', 'stock_disponible', 'precio_gs')
    inlines = [PiezaInline, RecetaInline] # Permite editar piezas e insumos desde aquí
    search_fields = ('nombre', 'codigo')
    
    # Función: Muestra el porcentaje de ocupación de la placa en verde
    def mostrar_porcentaje_uso(self, obj):
        valor = round(obj.porcentaje_ocupacion, 1)
        return format_html('<b style="color: #27ae60;">{}% de la placa</b>', valor)
    mostrar_porcentaje_uso.short_description = "% USO PLACA"

    # Función: Muestra el precio formateado en Guaraníes
    def precio_gs(self, obj):
        valor = "{:,.0f}".format(obj.precio_venta).replace(",", ".")
        return "Gs. %s" % valor
    precio_gs.short_description = "PRECIO VENTA"

# ==============================================================================
# --- 4. PANEL DE PEDIDOS (CON AVANCE DE FABRICACIÓN Y FILTRADO COMERCIAL) ---
# ==============================================================================
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # Definimos qué columnas ver, incluyendo la NUEVA COLUMNA INFORMATIVA
    list_display = ('id', 'cliente', 'mueble', 'cantidad', 'mostrar_placa', 'status_color', 'mostrar_avance_fabricacion')
    readonly_fields = ('estado',) # El estado se controla solo mediante acciones
    inlines = [TareaInline] # Permite ver el progreso de las tareas desde el pedido
    search_fields = ('cliente__nombre', 'mueble__nombre')

    # --- AQUÍ DEFINIMOS LAS ACCIONES DEL MENÚ DESPLEGABLE ---
    # ¡Las tres acciones fundamentales deben estar listadas aquí!
    actions = [
        'descargar_despiece_txt', 
        'marcar_como_entregado_y_cobrar', # Acción Comercial 1 (con cobro automático)
        'cancelar_pedido_simplemente' # Acción Comercial 2 (Lógica Comercial)
    ]

    # --- NUEVA COLUMNA INFORMATIVA: AVANCE FABRICACIÓN (Solo Lectura) ---
    def mostrar_avance_fabricacion(self, obj):
        # Usamos Tarea.objects.filter para evitar AttributeError y coordinar con related_name
        # He confirmado que 'tareas' es el related_name técnico en tu models.py
        ultima_tarea_terminada = obj.tareas.filter(terminado=True).last()
        
        # Si no hay tareas terminadas, mostramos 'Aún sin registrar'
        if not ultima_tarea_terminada:
            return mark_safe('<span style="color: #95a5a6;">⚪ Aún sin registrar</span>')
        
        # Obtenemos el nombre legible de la última tarea terminada
        etiqueta_tarea = ultima_tarea_terminada.get_nombre_display()
        
        return format_html(
            '<span style="color: white; background-color: #34495e; padding: 3px 10px; border-radius: 10px; font-weight: bold; display: inline-block;">🛠️ {}</span>',
            etiqueta_tarea
        )
    mostrar_avance_fabricacion.short_description = 'AVANCE FABRICACIÓN'

    # Función: Filtra la lista para mostrar solo lo comercial y lo listo para cobrar
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # PARA QUE NO APAREZCA EN NINGUNA OTRA PARTE, filtramos visualmente:
        # He ajustado este filtro para incluir también 'listo'
        return qs.filter(estado__in=['pendiente', 'listo', 'entregado'])

    # Función: Muestra el porcentaje total de ocupación de placas para el pedido
    def mostrar_placa(self, obj):
        # Cálculo: (% ocupación del mueble) x (cantidad de muebles del pedido)
        valor_total = round(obj.mueble.porcentaje_ocupacion * obj.cantidad, 1)
        return format_html('<b style="color: #27ae60;">{}% de la placa</b>', valor_total)
    mostrar_placa.short_description = "% USO PLACA"

    # Función: Muestra el estado del pedido con una etiqueta de color (Simplificado)
    def status_color(self, obj):
        # Mapa de colores para cada estado comercial
        colores = {
            'pendiente': '#e67e22',   # Naranja
            'listo': '#2ecc71',        # Verde claro (¡Agregado!)
            'entregado': '#27ae60',    # Verde oscuro
        }
        color = colores.get(obj.estado, '#95a5a6') # Gris por defecto
        texto = obj.get_estado_display() # Obtiene el nombre legible del estado
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 10px; font-weight: bold; display: inline-block;">{}</span>',
            color, texto
        )
    status_color.short_description = 'ESTADO'

    # ----------------------------------------------------------------------
    # --- ACCIÓN 1: GENERAR LISTA DE CORTE (TXT) ---
    # ----------------------------------------------------------------------
    def descargar_despiece_txt(self, request, queryset):
        # Crear la respuesta con el tipo de contenido para texto plano (.txt)
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="lista_corte_maderera.txt"'

        # Crear el contenido del archivo de texto, ordenado y alineado
        contenido = "ORDEN DE CORTE - LISTA DE PIEZAS\n"
        contenido += "="*35 + "\n\n"

        for pedido in queryset:
            contenido += f"Pedido ID: {pedido.id}\n"
            contenido += f"Cliente: {pedido.cliente.nombre}\n"
            contenido += f"Mueble: {pedido.mueble.nombre}\n"
            contenido += f"Cantidad de Muebles: {pedido.cantidad}\n"
            contenido += "-"*35 + "\n"
            # Encabezados de la tabla alineados
            contenido += f"{'Pieza':<20} | {'Largo':<6} | {'Ancho':<6} | {'Cant.'}\n"
            contenido += "-"*35 + "\n"
            
            # Recorrer las piezas del mueble asociado al pedido
            for p in pedido.mueble.pieza_set.all():
                # Cálculo automático: (piezas por mueble) x (cantidad de muebles)
                total = p.cantidad * pedido.cantidad
                # Usar formateo f-string para alinear las columnas
                contenido += f"{p.nombre:<20} | {p.largo:<6.1f} | {p.ancho:<6.1f} | {total}\n"
            
            contenido += "="*35 + "\n\n"

        # Escribir todo el contenido generado en la respuesta
        response.write(contenido)
        return response
    descargar_despiece_txt.short_description = "Generar Lista para Maderera (TXT)"

    # ----------------------------------------------------------------------
    # --- ACCIÓN COMERCIAL 1: MARCAR COMO ENTREGADO Y COBRAR (CON DESCUENTO DE STOCK OBLIGATORIO) ---
    # ----------------------------------------------------------------------
    def marcar_como_entregado_y_cobrar(self, request, queryset):
        # Esta función actualiza el stock y el estado
        
        for pedido in queryset:
            # Primero descontamos el stock del mueble
            mueble = pedido.mueble
            cantidad_pedido = pedido.cantidad
            # Restamos la cantidad del pedido del stock disponible del mueble
            mueble.stock_disponible -= cantidad_pedido
            mueble.save() # Guardamos el cambio de stock en la base de datos

            # Luego actualizamos el estado del pedido a 'entregado'
            # (Asumimos que la lógica de cobro ya está manejada externamente oimplícita en el acto comercial)
            pedido.estado = 'entregado'
            pedido.save() # Guardamos el cambio de estado del pedido

        self.message_user(request, "Los pedidos seleccionados se marcaron como Entregados y se descontó el stock de muebles correctamente.")
    marcar_como_entregado_y_cobrar.short_description = "✅ Marcar como Entregado y Cobrar"

    # ----------------------------------------------------------------------
    # --- ACCIÓN COMERCIAL 2: CANCELAR PEDIDO SIMPLEMENTE (LÓGICA COMERCIAL) ---
    # ----------------------------------------------------------------------
    def cancelar_pedido_simplemente(self, request, queryset):
        # Esta acción solo cambia el estado a 'Cancelado'.
        # Lógica de si suma o no stock se maneja automáticamente por el flujo en models.py:
        # - Al terminar la última tarea, el stock se sumará (+1) y el estado pasará a "Listo para Entrega".
        
        for pedido in queryset:
            # Actualizamos el estado del pedido a 'cancelado'
            pedido.estado = 'cancelado'
            pedido.save() # Guardamos el cambio de estado del pedido

        self.message_user(request, "Los pedidos seleccionados se marcaron como Cancelados correctamente. El carpintero puede seguir registrando avances.")
    cancelar_pedido_simplemente.short_description = "❌ Cancelar Pedido (Lógica Comercial)"
    # -----------------------------------------------------------------

# ==============================================================================
# --- 5. REGISTRO DE OTRAS TABLAS SIMPLES ---
# ==============================================================================
admin.site.register(ModeloInsumo) # Panel para gestionar tornillos, bisagras, etc.
admin.site.register(Cliente)      # Panel para gestionar los datos de los clientes