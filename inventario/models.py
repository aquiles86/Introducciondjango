from django.db import models
from decimal import Decimal

class Insumo(models.Model):
    UNIDADES = (
        ('un', 'Unidades'),
        ('m', 'Metros'),
        ('kg', 'Kilogramos'),
        ('l', 'Litros'),
        ('p2', 'Pies Tablares'),
        ('par', 'Pares (Correderas)'),
        ('m2', 'Metros Cuadrados'),
    )
    nombre = models.CharField(max_length=100)
    unidad_medida = models.CharField(max_length=5, choices=UNIDADES, default='un')
    precio_referencia = models.DecimalField(max_digits=12, decimal_places=0)

    def __str__(self):
        return f"{self.nombre} ({self.get_unidad_medida_display()})"

class Mueble(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=0)
    
    # Datos de la Placa Base
    costo_placa_entera = models.DecimalField(max_digits=12, decimal_places=0)
    ancho_placa_cm = models.FloatField(default=183)
    largo_placa_cm = models.FloatField(default=260)
    
    imagen = models.ImageField(upload_to='muebles/', null=True, blank=True)
    stock_disponible = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre

    # --- PROPIEDADES DE CÁLCULO ---

    @property
    def area_total_utilizada(self):
        """Suma el área de todas las piezas (cm2)"""
        return sum(p.largo * p.ancho * p.cantidad for p in self.pieza_set.all())

    @property
    def porcentaje_ocupacion(self):
        """Calcula qué % de la placa ocupa este mueble"""
        area_placa = self.ancho_placa_cm * self.largo_placa_cm
        if area_placa == 0: return 0
        return (self.area_total_utilizada / area_placa) * 100

    @property
    def area_libre_cm2(self):
        """Calcula cuánto sobra de la placa (cm2)"""
        area_placa = self.ancho_placa_cm * self.largo_placa_cm
        return area_placa - self.area_total_utilizada

    @property
    def costo_madera(self):
        """Costo proporcional según el área utilizada"""
        area_placa = self.ancho_placa_cm * self.largo_placa_cm
        if area_placa > 0:
            porcentaje_uso = self.area_total_utilizada / area_placa
            return Decimal(porcentaje_uso) * self.costo_placa_entera
        return Decimal(0)

    @property
    def costo_insumos(self):
        return sum(Decimal(ri.cantidad) * ri.insumo.precio_referencia for ri in self.receta_set.all())

    @property
    def costo_total_produccion(self):
        return self.costo_madera + self.costo_insumos

class Pieza(models.Model):
    mueble = models.ForeignKey(Mueble, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    largo = models.FloatField(help_text="Sentido de la veta (cm)")
    ancho = models.FloatField(help_text="Ancho (cm)")
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.nombre} ({self.largo}x{self.ancho})"

class Receta(models.Model):
    mueble = models.ForeignKey(Mueble, on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT)
    cantidad = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.cantidad} de {self.insumo.nombre}"

class Pedido(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_corte', 'En Corte'),
        ('en_armado', 'En Taller'),
        ('listo', 'Listo para Entrega'),
        ('entregado', 'Entregado'),
    )
    TIPOS = (
        ('cliente', 'Venta Directa'),
        ('stock', 'Producción de Sobrante (Stock)'),
    )
    cliente = models.CharField(max_length=200)
    mueble = models.ForeignKey(Mueble, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    tipo_pedido = models.CharField(max_length=20, choices=TIPOS, default='cliente')
    fecha = models.DateTimeField(auto_now_add=True)