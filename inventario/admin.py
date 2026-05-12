from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from .models import Insumo, Mueble, FotoMueble, Pieza, Receta, Cliente, Pedido, Personal, OrdenTrabajo, Factura
from django.contrib import admin, messages
# =============================================================
# --- CONFIGURACIONES INLINE (PARA EDICIÓN RÁPIDA) ---
# =============================================================
class FotoMuebleInline(admin.TabularInline):
    model = FotoMueble
    extra = 1

class PiezaInline(admin.TabularInline):
    model = Pieza
    extra = 1

class RecetaInline(admin.TabularInline):
    model = Receta
    extra = 1

# =============================================================
# --- ADMINISTRACIÓN DE MODELOS ---
# =============================================================

@admin.register(Mueble)
class MuebleAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'stock_disponible', 'precio_venta', 'costo_total_produccion')
    search_fields = ('nombre', 'codigo')
    inlines = [FotoMuebleInline, PiezaInline, RecetaInline]

@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'unidad_medida', 'precio_referencia')
    search_fields = ('nombre',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    # Mostramos la property 'identificacion' en la lista
    list_display = ('nombre', 'apellido', 'identificacion', 'telefono', 'ciudad', 'barrio')
    # Permitimos buscar por cualquiera de los dos documentos
    search_fields = ('nombre', 'apellido', 'cedula', 'ruc', 'ciudad')
    list_filter = ('ciudad', 'barrio')

    fieldsets = (
        ('Datos Personales', {
            'fields': ('nombre', 'apellido', 'cedula', 'ruc', 'telefono')
        }),
        ('Dirección de Entrega', {
            'fields': ('ciudad', 'barrio', 'calle_principal', 'numero_casa', 'calle_lateral_1', 'calle_lateral_2')
        }),
        ('Ayudas para Logística', {
            'fields': ('referencia_ubicacion', 'geolocalizacion'),
        }),
    )

@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'identificacion', 'especialidad', 'user')
    search_fields = ('nombre', 'apellido', 'cedula', 'ruc', 'especialidad')
    list_filter = ('especialidad',)
    
    fieldsets = (
        ('Identificación', {
            'fields': ('user', 'nombre', 'apellido', 'cedula', 'ruc')
        }),
        ('Contacto y Cargo', {
            'fields': ('especialidad', 'telefono', 'email', 'direccion')
        }),
    )

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # 1. Configuración de la lista
    list_display = ('id', 'cliente', 'ver_documento', 'mueble', 'fecha_pedido', 'fecha_fin', 'colorear_estado')
    list_filter = ('fecha_pedido', 'estado', 'fecha_fin')
    search_fields = ('cliente__nombre', 'cliente__cedula', 'cliente__ruc', 'mueble__nombre')
    readonly_fields = ('estado', 'fecha_fin')

    # 2. Agregar la Acción de Facturación
    actions = ['generar_factura_accion']

    def generar_factura_accion(self, request, queryset):
        facturadas = 0
        errores = 0

        for pedido in queryset:
            # Regla de negocio: Solo facturar pedidos FINALIZADOS que no tengan factura aún
            if pedido.estado == 'finalizado':
                if not hasattr(pedido, 'factura'):
                    # Generamos un número correlativo simple: 001-001-XXXXXX
                    conteo = Factura.objects.count() + 1
                    nro = f"001-001-{conteo:06d}"
                    
                    Factura.objects.create(
                        pedido=pedido,
                        nro_factura=nro,
                        condicion_venta='contado'
                    )
                    facturadas += 1
                else:
                    # Ya tiene factura
                    errores += 1
            else:
                # No está terminado en el taller
                errores += 1

        # Mensajes de retroalimentación
        if facturadas > 0:
            self.message_user(request, f"✅ ¡Éxito! Se han generado {facturadas} factura(s).", messages.SUCCESS)
        if errores > 0:
            self.message_user(request, f"⚠️ Atención: {errores} pedido(s) fueron ignorados (ya tienen factura o no están TERMINADOS).", messages.WARNING)

    generar_factura_accion.short_description = "🧾 Generar Factura de los pedidos seleccionados"

    # 3. Funciones de visualización
    def ver_documento(self, obj):
        return obj.cliente.identificacion if hasattr(obj.cliente, 'identificacion') else "N/A"
    ver_documento.short_description = 'CI / RUC'

    def colorear_estado(self, obj):
        if obj.estado == 'finalizado':
            color = '#28a745' # Verde
            texto = 'TERMINADO'
        else:
            color = '#fd7e14' # Naranja
            texto = 'PENDIENTE'
        return format_html(
            '<b style="color: {};">{}</b>',
            color,
            texto,
        )
    colorear_estado.short_description = 'Estado del Pedido'

@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    # 1. Configuración de la tabla
    list_display = (
        'pedido', 'fecha_inicio', 'fecha_fin', 'finalizado', 
        'corte', 'canteado', 'armado', 'limpieza', 'empaquetado'
    )
    
    readonly_fields = ('finalizado', 'fecha_inicio', 'fecha_fin')

    fieldsets = (
        ('Asignación', {
            'fields': ('pedido', 'personal_asignado')
        }),
        ('Progreso del Taller', {
            'fields': ('corte', 'canteado', 'armado', 'limpieza', 'empaquetado', 'finalizado')
        }),
        ('Registro de Tiempos', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
    )
    
    filter_horizontal = ('personal_asignado',)
    
    search_fields = (
        'pedido__cliente__nombre', 
        'pedido__cliente__cedula', 
        'pedido__cliente__ruc', 
        'pedido__mueble__nombre'
    )

    # 2. Lógica para sincronizar con Pedido al guardar en el Admin
    def save_model(self, request, obj, form, change):
        # Verificamos si todos los procesos técnicos están marcados
        procesos = [obj.corte, obj.canteado, obj.armado, obj.limpieza, obj.empaquetado]
        
        if all(procesos):
            # Si todo está marcado, finalizamos la orden
            obj.finalizado = True
            if not obj.fecha_fin:
                obj.fecha_fin = timezone.now()
            
            # ACTUALIZAMOS EL PEDIDO A FINALIZADO
            pedido = obj.pedido
            pedido.estado = 'finalizado'
            pedido.fecha_fin = obj.fecha_fin
            pedido.save()
        else:
            # Si falta algún paso, la orden y el pedido siguen pendientes
            obj.finalizado = False
            obj.fecha_fin = None
            
            pedido = obj.pedido
            pedido.estado = 'pendiente'
            # No borramos la fecha_fin del pedido si ya existía, o puedes ponerla None
            pedido.save()

        # Guardamos la Orden de Trabajo
        super().save_model(request, obj, form, change)

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    # Agregamos 'ver_factura' al listado para que aparezca el botón
    list_display = ('nro_factura', 'cliente_nombre', 'mueble_nombre', 'total', 'fecha_emision', 'ver_factura')
    
    list_filter = ('fecha_emision', 'condicion_venta')
    
    search_fields = ('nro_factura', 'cliente_nombre', 'cliente_ruc')
    
    # Todos estos campos se llenan solos al crear la factura desde el pedido
    readonly_fields = (
        'pedido', 'nro_factura', 'cliente_nombre', 'cliente_ruc', 
        'mueble_nombre', 'precio_unitario', 'iva_10', 'total', 'fecha_emision'
    )

    def ver_factura(self, obj):
        """
        Genera un botón que redirige a la vista personalizada de la factura
        'factura_detalle' es el nombre que definimos en urls.py
        """
        try:
            url = reverse('factura_detalle', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" target="_blank" '
                'style="background-color: #447e9b; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">'
                'Ver/Imprimir</a>', 
                url
            )
        except:
            return "Ruta no encontrada"

    # Título de la columna en el admin
    ver_factura.short_description = "Acción"
