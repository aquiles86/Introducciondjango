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
    
    # Datos de la Placa Base para calcular costo proporcional
    costo_placa_entera = models.DecimalField(max_digits=12, decimal_places=0, help_text="Precio de la placa completa")
    ancho_placa_cm = models.FloatField(default=183, help_text="Ancho de la placa (ej: 183)")
    largo_placa_cm = models.FloatField(default=260, help_text="Largo de la placa (ej: 260)")
    
    imagen = models.ImageField(upload_to='muebles/', null=True, blank=True)
    stock_disponible = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre

    @property
    def costo_madera(self):
        """Calcula el costo proporcional según el área de las piezas"""
        area_placa = self.ancho_placa_cm * self.largo_placa_cm
        area_utilizada = sum(p.largo * p.ancho * p.cantidad for p in self.pieza_set.all())
        
        if area_placa > 0:
            porcentaje_uso = area_utilizada / area_placa
            return Decimal(porcentaje_uso) * self.costo_placa_entera
        return Decimal(0)

    @property
    def costo_insumos(self):
        """Suma el costo de todos los insumos de la receta"""
        return sum(Decimal(ri.cantidad) * ri.insumo.precio_referencia for ri in self.receta_set.all())

    @property
    def costo_total_produccion(self):
        """Suma Madera + Insumos"""
        return self.costo_madera + self.costo_insumos

class Pieza(models.Model):
    """Aquí se carga el despiece del Cut List Optimizer"""
    mueble = models.ForeignKey(Mueble, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100, help_text="Ej: Lateral, Puerta...")
    largo = models.FloatField(help_text="Largo en cm")
    ancho = models.FloatField(help_text="Ancho en cm")
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.nombre} ({self.largo}x{self.ancho})"

class Receta(models.Model):
    mueble = models.ForeignKey(Mueble, on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT)
    cantidad = models.FloatField(default=1.0, help_text="Cantidad usada en este mueble")

    def __str__(self):
        return f"{self.cantidad} de {self.insumo.nombre}"

class Pedido(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_corte', 'En Corte'),
        ('en_armado', 'En Taller'),
        ('listo', 'Listo para Entrega'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    )
    cliente = models.CharField(max_length=200)
    mueble = models.ForeignKey(Mueble, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha = models.DateTimeField(auto_now_add=True)