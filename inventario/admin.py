from django.contrib import admin
from django.utils.html import format_html
# Importamos con alias para evitar el conflicto de nombres en 'inventario'
from .models import Insumo as ModeloInsumo, Mueble, Pieza, Receta, Cliente, Pedido, Tarea

class TareaInline(admin.TabularInline):
    model = Tarea
    extra = 0

class PiezaInline(admin.TabularInline):
    model = Pieza
    extra = 1

class RecetaInline(admin.TabularInline):
    model = Receta
    extra = 1

@admin.register(Mueble)
class MuebleAdmin(admin.ModelAdmin):
    # Lista de Muebles corregida
    list_display = ('nombre', 'codigo', 'mostrar_porcentaje_uso', 'stock_disponible', 'precio_gs')
    inlines = [PiezaInline, RecetaInline]
    
    def mostrar_porcentaje_uso(self, obj):
        # Simplificamos el formato para evitar el ValueError de la foto
        porc = round(obj.porcentaje_ocupacion, 2)
        return format_html('<b style="color: #27ae60;">{}% de la placa</b>', porc)
    mostrar_porcentaje_uso.short_description = "% USO PLACA"

    def precio_gs(self, obj):
        valor = "{:,.0f}".format(obj.precio_venta).replace(",", ".")
        return "Gs. %s" % valor
    precio_gs.short_description = "PRECIO VENTA"

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # Lista de Pedidos con el % de placa recuperado y estado bloqueado
    list_display = ('id', 'cliente', 'mueble', 'cantidad', 'mostrar_placa', 'status_color')
    readonly_fields = ('estado',) 
    inlines = [TareaInline]
    
    def mostrar_placa(self, obj):
        # Calculamos el uso total según la cantidad pedida
        total_porc = round(obj.mueble.porcentaje_ocupacion * obj.cantidad, 2)
        return format_html('<b style="color: #27ae60;">{}% de la placa</b>', total_porc)
    mostrar_placa.short_description = "% USO PLACA"

    def status_color(self, obj):
        colores = {
            'pendiente': '#e67e22', 
            'produccion': '#3498db', 
            'listo': '#2ecc71', 
            'entregado': '#27ae60'
        }
        color = colores.get(obj.estado, '#95a5a6')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 10px; font-weight: bold; display: inline-block;">{}</span>',
            color, 
            obj.get_estado_display()
        )
    status_color.short_description = 'ESTADO'

# Registro de modelos (Usando el alias ModeloInsumo para evitar errores)
admin.site.register(ModeloInsumo) 
admin.site.register(Cliente)