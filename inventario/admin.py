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
    list_display = ('mueble', 'cliente', 'tipo_pedido', 'mostrar_estado', 'mostrar_costo_pedido', 'fecha')
    list_filter = ('estado', 'tipo_pedido')
    actions = ['generar_lista_corte_consolidada']

    def mostrar_estado(self, obj):
        # 1. Obtenemos el nombre exacto que ves en el menú (el "label")
        # Esto soluciona el problema de "Listo para Entrega"
        nombre_estado = obj.get_estado_display()
        
        colores = {
            'Pendiente': '#e74c3c',           # Rojo
            'En Corte': '#3498db',            # Azul
            'En Taller': '#f1c40f',           # Amarillo
            'En Armado': '#9b59b6',           # Violeta
            'Listo para Entrega': '#2ecc71',  # Verde claro
            'Entregado': '#27ae60',           # Verde oscuro
        }
        
        # 2. Buscamos el color. Si no coincide exacto, ponemos un Gris (#7f8c8d)
        color_fondo = colores.get(nombre_estado, '#7f8c8d')
        
        # 3. El secreto: pasamos el COLOR y el NOMBRE para que el óvalo no salga vacío
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 15px; font-weight: bold; text-transform: uppercase; font-size: 10px; display: inline-block; min-width: 110px; text-align: center;">{}</span>',
            color_fondo, nombre_estado
        )
    mostrar_estado.short_description = 'Estado'

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
            from .models import Pieza 
            piezas = Pieza.objects.filter(mueble=pedido.mueble)
            for p in piezas:
                total_piezas = p.cantidad * pedido.cantidad
                texto += f" - {p.nombre}: {p.largo} x {p.ancho} cm (Cant: {total_piezas})\n"
            area_total_acumulada += pedido.mueble.porcentaje_ocupacion * pedido.cantidad
            texto += "----------------------------------------\n"
        texto += f"\nOCUPACIÓN ESTIMADA TOTAL: {area_total_acumulada:.2f}% de una placa base."
        texto += f"\nEQUIVALENTE A: {(area_total_acumulada/100):.1f} placas aprox."
        response = HttpResponse(texto, content_type="text/plain; charset=utf-8")
        response['Content-Disposition'] = 'attachment; filename="lista_corte_consolidada.txt"'
        return response

# --- OTROS REGISTROS ---
admin.site.register(Insumo)