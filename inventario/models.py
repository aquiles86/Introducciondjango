from django.db import models

class Insumo(models.Model):
    UNIDADES = (
        ('un', 'Unidades (Global)'),
        ('m', 'Metros'),
        ('kg', 'Kilogramos'),
    )
    nombre = models.CharField(max_length=100)
    unidad_medida = models.CharField(max_length=5, choices=UNIDADES, default='un')
    precio_referencia = models.DecimalField(max_digits=12, decimal_places=0)

    def __str__(self):
        return f"{self.nombre} ({self.unidad_medida})"

class Mueble(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=0)
    
    # Datos de la Placa
    costo_placa_madera = models.DecimalField(max_digits=12, decimal_places=0)
    ancho_total_madera = models.FloatField(help_text="Ancho necesario en cm")
    largo_total_madera = models.FloatField(help_text="Largo necesario en cm")
    
    imagen = models.ImageField(upload_to='muebles/', null=True, blank=True)
    stock_disponible = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre

    @property
    def costo_total_produccion(self):
        total_insumos = sum(ri.cantidad * ri.insumo.precio_referencia for ri in self.receta_set.all())
        return self.costo_placa_madera + total_insumos

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
        ('cancelado', 'Cancelado'),
    )
    cliente = models.CharField(max_length=200)
    mueble = models.ForeignKey(Mueble, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha = models.DateTimeField(auto_now_add=True)
