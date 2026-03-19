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
    list_display = ('nombre', 'codigo', 'mostrar_ocupacion','mostrar_stock','precio_venta', 'mostrar_costo', 'mostrar_utilidad')
    inlines = [PiezaInline, RecetaInline]
    search_fields = ('nombre', 'codigo')
    @property
    def porcentaje_placa(self):
        # Multiplica el porcentaje del mueble por la cantidad pedida
        return self.mueble.porcentaje_ocupacion * self.cantidad

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
    def mostrar_stock(self, obj):
        # Si no hay stock, rojo. Si hay, verde.
        color = "red" if obj.stock_disponible <= 0 else "green"
        return format_html(
            '<b style="color: {};">{} un.</b>',
            color, obj.stock_disponible
        )
    mostrar_stock.short_description = 'Stock'

# --- CONFIGURACIÓN DE PEDIDOS (La herramienta de combinación) ---

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('mueble', 'cliente', 'tipo_pedido', 'mostrar_estado','mostrar_porcentaje_placa', 'mostrar_costo_pedido', 'fecha')
    list_filter = ('estado', 'tipo_pedido')
    actions = ['generar_lista_corte_consolidada']

    def mostrar_estado(self, obj):
        # 1. Usamos las claves exactas de tu modelo (en minúsculas)
        colores = {
            'pendiente': '#e74c3c',   # Rojo
            'en_corte': '#3498db',    # Azul
            'en_taller': '#f1c40f',   # Amarillo
            'en_armado': '#9b59b6',   # Violeta
            'listo': '#2ecc71',       # Verde claro
            'entregado': '#27ae60',   # Verde oscuro
            'cancelado': '#34495e',   # Gris oscuro
        }
        
        # 2. Buscamos el color usando la clave 'obj.estado'
        color_fondo = colores.get(obj.estado, '#7f8c8d')
        
        # 3. get_estado_display() nos da el nombre bonito (ej: "Listo para Entrega")
        texto_bonito = obj.get_estado_display()
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 15px; '
            'font-weight: bold; text-transform: uppercase; font-size: 10px; display: inline-block; '
            'min-width: 110px; text-align: center;">{}</span>',
            color_fondo, texto_bonito
        )
    mostrar_estado.short_description = 'Estado'

    def mostrar_costo_pedido(self, obj):
        total = obj.mueble.costo_total_produccion * obj.cantidad
        return f"Gs. {total:,.0f}"
    mostrar_costo_pedido.short_description = 'Costo Total'

# Dentro de la clase PedidoAdmin en admin.py
    actions = ['calcular_placas_necesarias']

    @admin.action(description="Calcular ocupación total de placa")
    def calcular_placas_necesarias(self, request, queryset):
        # Sumamos el porcentaje de todos los pedidos que tildaste
        total_porcentaje = sum(p.porcentaje_placa for p in queryset)
        
        # Calculamos cuántas placas son (cada 100% es una placa)
        placas_enteras = total_porcentaje / 100
        
        # Mostramos el mensaje arriba en la pantalla
        self.message_user(
            request, 
            f"📊 OPTIMIZACIÓN: Los pedidos seleccionados ocupan el {total_porcentaje:.2f}% de la placa. "
            f"Necesitás preparar {placas_enteras:.2f} placas aproximadamente."
        )
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
    def mostrar_porcentaje_placa(self, obj):
        # 1. Obtenemos el número (aseguramos que sea 0 si no existe)
        valor = obj.mueble.porcentaje_ocupacion or 0
        
        # 2. Lo convertimos a texto con 2 decimales ANTES de pasarlo al HTML
        texto_formateado = f"{valor:.2f}% de la placa"
        
        # 3. Lo mostramos con color
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">{}</span>',
            texto_formateado
        )
    
    mostrar_porcentaje_placa.short_description = '% Uso Placa'

# --- OTROS REGISTROS ---
admin.site.register(Insumo)