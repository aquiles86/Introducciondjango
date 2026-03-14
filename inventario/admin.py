from django.contrib import admin
from .models import Insumo, Mueble, Pieza, Receta, Pedido

class PiezaInline(admin.TabularInline):
    model = Pieza
    extra = 1

class RecetaInline(admin.TabularInline):
    model = Receta
    extra = 1

@admin.register(Mueble)
class MuebleAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'precio_venta', 'stock_disponible')
    inlines = [PiezaInline, RecetaInline]

admin.site.register(Insumo)
admin.site.register(Pedido)