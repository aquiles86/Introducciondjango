from django.contrib import admin
from .models import Insumo, Mueble, FotoMueble, Pieza, Receta, Cliente, Pedido, Personal, OrdenTrabajo

# Configuración para que las fotos aparezcan dentro del mueble
class FotoMuebleInline(admin.TabularInline):
    model = FotoMueble
    extra = 1  # Número de filas vacías que aparecen por defecto
    fields = ['imagen', 'descripcion']

# Configuración opcional para ver piezas y recetas también en la misma pantalla
class PiezaInline(admin.TabularInline):
    model = Pieza
    extra = 1

class RecetaInline(admin.TabularInline):
    model = Receta
    extra = 1

@admin.register(Mueble)
class MuebleAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'stock_disponible', 'precio_venta', 'costo_total_produccion')
    search_fields = ('nombre', 'codigo')
    # Añadimos todos los inlines para una gestión centralizada
    inlines = [FotoMuebleInline, PiezaInline, RecetaInline]

@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'unidad_medida', 'precio_referencia')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    # Columnas que verás en la lista principal
    list_display = ('nombre', 'apellido', 'ruc_cedula', 'telefono', 'ciudad', 'barrio')
    search_fields = ('nombre', 'apellido', 'ruc_cedula', 'ciudad')
    list_filter = ('ciudad', 'barrio') # Filtros laterales rápidos

    # Organización del formulario de carga
    fieldsets = (
        ('Datos Personales', {
            'fields': ('nombre', 'apellido', 'ruc_cedula', 'telefono')
        }),
        ('Dirección de Entrega', {
            'fields': (
                'ciudad', 'barrio', 'calle_principal', 'numero_casa', 
                'calle_lateral_1', 'calle_lateral_2'
            )
        }),
        ('Geolocalización y Ayudas', {
            'fields': ('referencia_ubicacion', 'geolocalizacion'),
            'description': 'Información extra para que el transportista encuentre la casa.'
        }),
    )
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # Columnas que verás al entrar a "Pedidos"
    list_display = ('cliente','ruc_cedula', 'fecha_pedido', 'mueble')
    # Buscador por nombre de cliente o mueble
    search_fields = ('cliente__nombre', 'mueble__nombre','cliente__ruc_cedula')
    # Filtro lateral por fecha
    list_filter = ('fecha_pedido',)
    def ruc_cedula(self, obj):
                # Entra al cliente relacionado y trae su ruc_cedula
                return obj.cliente.ruc_cedula
@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido','user', 'ruc_cedula', 'especialidad', 'telefono')
    search_fields = ('nombre', 'apellido', 'ruc_cedula', 'especialidad')
    list_filter = ('especialidad',)
    
    fieldsets = (
        ('Identificación', {
            'fields': ('user', 'nombre', 'apellido', 'ruc_cedula')
        }),
        ('Contacto y Especialidad', {
            'fields': ('especialidad', 'telefono', 'email', 'direccion')
        }),
    )
@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    # 1. Columnas en la lista principal
    list_display = (
        'pedido', 
        'fecha_inicio', 
        'fecha_fin', 
        'finalizado', 
        'corte', 
        'canteado', 
        'armado', 
        'limpieza', 
        'empaquetado'
    )
    
    # 2. Filtros laterales
    list_filter = ('fecha_inicio', 'personal_asignado', 'finalizado')
    filter_horizontal = ('personal_asignado',)

    # 3. BUSCADOR (Lo nuevo): Permite buscar por cliente, mueble o RUC
    # Usamos el doble guion bajo (__) para navegar entre las tablas relacionadas
    search_fields = (
        'pedido__cliente__nombre',    # Busca en el nombre del cliente
        'pedido__cliente__ruc_cedula',# Busca en el RUC del cliente
        'pedido__mueble__nombre',      # Busca en el nombre del mueble
    )

    # 4. Campos de solo lectura
    readonly_fields = ('fecha_inicio',)

    # 5. Organización del formulario de edición
    fieldsets = (
        ('Registro de Tiempo', {
            'fields': ('fecha_inicio',) 
        }),
        ('Asignación de Trabajo', {
            'fields': ('pedido', 'personal_asignado')
        }),
        ('Estado de Tareas', {
            'fields': (
                'corte', 
                'canteado', 
                'armado', 
                'limpieza', 
                'empaquetado', 
                'finalizado', 
                'fecha_fin'
            )
        }),
    )