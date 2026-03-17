from django.contrib import admin
from django.utils.html import format_html
from .models import Insumo, Mueble, Pieza, Receta, Pedido

# --- CONFIGURACIÓN DE MUEBLES ---

class PiezaInline(admin.TabularInline):
    model = Pieza
    extra = 1

class RecetaInline(admin.TabularInline):
    model = Receta
    extra = 1

@admin.register(Mueble)
class MuebleAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'mostrar_ocupacion', 'precio_venta', 'mostrar_costo', 'mostrar_utilidad')
    inlines = [PiezaInline, RecetaInline]
    search_fields = ('nombre', 'codigo')

    def mostrar_ocupacion(self, obj):
        porcentaje = obj.porcentaje_ocupacion
        color = "green" if porcentaje < 50 else "orange" if porcentaje < 85 else "red"
        porcentaje_formateado = "{:.2f}".format(porcentaje)
        return format_html(
            '<b style="color: {};">{}% de la placa</b>',
            color, porcentaje_formateado
        )
    mostrar_ocupacion.short_description = '% Uso Placa'

    def mostrar_costo(self, obj):
        return f"Gs. {obj.costo_total_produccion:,.0f}"
    mostrar_costo.short_description = 'Costo Total'

    def mostrar_utilidad(self, obj):
        utilidad = obj.precio_venta - obj.costo_total_produccion
        return f"Gs. {utilidad:,.0f}"
    mostrar_utilidad.short_description = 'Ganancia'

# --- CONFIGURACIÓN DE PEDIDOS (La herramienta de combinación) ---

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('mueble', 'cliente', 'tipo_pedido', 'estado', 'mostrar_costo_pedido', 'fecha')
    list_filter = ('estado', 'tipo_pedido')
    actions = ['generar_lista_corte_consolidada']

    def mostrar_costo_pedido(self, obj):
        total = obj.mueble.costo_total_produccion * obj.cantidad
        return f"Gs. {total:,.0f}"
    mostrar_costo_pedido.short_description = 'Costo Total'

    @admin.action(description="🚀 Combinar pedidos y generar lista de corte")
    def generar_lista_corte_consolidada(self, request, queryset):
        from django.http import HttpResponse
        
        texto = "LISTA DE CORTE PARA MADERERA (COMBINADA)\n"
        texto += "========================================\n\n"
        
        area_total_acumulada = 0
        for pedido in queryset:
            texto += f"MUEBLE: {pedido.mueble.nombre} | Cantidad: {pedido.cantidad}\n"
            piezas = Pieza.objects.filter(mueble=pedido.mueble)
            
            for p in piezas:
                total_piezas = p.cantidad * pedido.cantidad
                texto += f" - {p.nombre}: {p.largo} x {p.ancho} cm (Cant: {total_piezas})\n"
            
            # Calculamos la ocupación de este pedido específico
            area_total_acumulada += pedido.mueble.porcentaje_ocupacion * pedido.cantidad
            texto += "----------------------------------------\n"
        
        texto += f"\nOCUPACIÓN ESTIMADA TOTAL: {area_total_acumulada:.2f}% de una placa base."
        texto += f"\nEQUIVALENTE A: {(area_total_acumulada/100):.1f} placas aprox."
        
        response = HttpResponse(texto, content_type="text/plain; charset=utf-8")
        response['Content-Disposition'] = 'attachment; filename="lista_corte_combinada.txt"'
        return response

# --- OTROS REGISTROS ---
admin.site.register(Insumo)