from django.contrib import admin
from django.utils.html import format_html
from .models import Insumo, Mueble, FotoMueble, Pieza, Receta, Cliente, Pedido, Personal, OrdenTrabajo

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
    # Agregamos 'fecha_fin' al list_display para ver cuándo terminó
    list_display = ('id', 'cliente', 'ver_documento', 'mueble', 'fecha_pedido', 'fecha_fin', 'colorear_estado')
    
    # Filtro lateral actualizado con la fecha de finalización
    list_filter = ('fecha_pedido', 'estado', 'fecha_fin')
    
    search_fields = ('cliente__nombre', 'cliente__cedula', 'cliente__ruc', 'mueble__nombre')
    
    # Ahora 'estado' y 'fecha_fin' son de solo lectura (los controla el Taller)
    readonly_fields = ('estado', 'fecha_fin')

    def ver_documento(self, obj):
        # Asumiendo que 'identificacion' es una propiedad o campo en tu modelo Cliente
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
    # Agregamos 'fecha_fin' a la tabla de Órdenes de Trabajo
    list_display = (
        'pedido', 'fecha_inicio', 'fecha_fin', 'finalizado', 
        'corte', 'canteado', 'armado', 'limpieza', 'empaquetado'
    )
    
    # Mantenemos las fechas y el estado finalizado como solo lectura
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

