from django.db import models
from decimal import Decimal
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

# --- 1. MODELO DE INSUMOS ---
class Insumo(models.Model):
    UNIDADES = (
        ('un', 'Unidades'), ('m', 'Metros'), ('kg', 'Kilogramos'),
        ('l', 'Litros'), ('p2', 'Pies Tablares'), ('par', 'Pares'), ('m2', 'Metros Cuadrados'),
    )
    nombre = models.CharField(max_length=100)
    unidad_medida = models.CharField(max_length=5, choices=UNIDADES, default='un')
    precio_referencia = models.DecimalField(max_digits=12, decimal_places=0)

    def __str__(self):
        return f"{self.nombre} ({self.get_unidad_medida_display()})"

# --- 2. MODELO DE MUEBLES ---
class Mueble(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=0)
    costo_placa_entera = models.DecimalField(max_digits=12, decimal_places=0)
    ancho_placa_cm = models.FloatField(default=183)
    largo_placa_cm = models.FloatField(default=260)
    imagen = models.ImageField(upload_to='muebles/', null=True, blank=True)
    stock_disponible = models.PositiveIntegerField(default=0)

    def __str__(self): return self.nombre

    @property
    def area_total_utilizada(self):
        return sum(p.largo * p.ancho * p.cantidad for p in self.pieza_set.all())

    @property
    def porcentaje_ocupacion(self):
        area_placa = self.ancho_placa_cm * self.largo_placa_cm
        if area_placa == 0: return 0
        return (self.area_total_utilizada / area_placa) * 100

    @property
    def costo_madera(self):
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

# --- 3. PIEZAS Y RECETAS ---
class Pieza(models.Model):
    mueble = models.ForeignKey(Mueble, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    largo = models.FloatField(help_text="Sentido de la veta (cm)")
    ancho = models.FloatField(help_text="Ancho (cm)")
    cantidad = models.PositiveIntegerField(default=1)

class Receta(models.Model):
    mueble = models.ForeignKey(Mueble, on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT)
    cantidad = models.FloatField(default=1.0)

# --- 4. CLIENTES Y PEDIDOS ---
class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    ruc_cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    def __str__(self): return self.nombre

class Pedido(models.Model):
    ESTADOS = (
        ('pendiente', '1. Pendiente'),
        ('produccion', '2. En Producción'),
        ('listo', '3. Listo para Entrega'),
        ('entregado', '4. Entregado'),
        ('cancelado', '5. Cancelado'),
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    mueble = models.ForeignKey(Mueble, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Pedido {self.id} - {self.cliente.nombre}"

# --- 5. MODELO DE TAREAS (9 PASOS) ---
class Tarea(models.Model):
    OPCIONES_TAREA = [
        ('1_DISENO', '1. Diseño y Despiece'),
        ('2_PRESUPUESTO', '2. Aprobación de Presupuesto'),
        ('3_PEDIDO_CORTE', '3. Pago y Pedido a Maderera'),
        ('4_PROCESO_MADERERA', '4. Corte y Canteado Externo'),
        ('5_RECEPCION', '5. Recepción de Piezas en Taller'),
        ('6_ARMADO', '6. Ensamblado y Herrajes'),
        ('7_INSTALACION', '7. Instalación en Obra'),
        ('8_LIMPIEZA', '8. Limpieza y Ajuste Final'),
        ('9_LISTO', '9. Finalizado para Entrega'),
    ]
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='tareas')
    nombre = models.CharField(max_length=50, choices=OPCIONES_TAREA, default='1_DISENO')
    terminado = models.BooleanField(default=False, verbose_name="¿Terminado?")
    fecha_fin = models.DateField(default=timezone.now)
    tiempo = models.DurationField(null=True, blank=True) # CORREGIDO para evitar IntegrityError

    def __str__(self): return self.get_nombre_display()

# --- 6. LOS ROBOTS (SEÑALES AUTOMÁTICAS) ---

def recalcular_stock(mueble):
    fabricados = Pedido.objects.filter(mueble=mueble, tareas__nombre='9_LISTO', tareas__terminado=True).distinct().aggregate(total=Sum('cantidad'))['total'] or 0
    entregados = Pedido.objects.filter(mueble=mueble, estado='entregado').aggregate(total=Sum('cantidad'))['total'] or 0
    Mueble.objects.filter(pk=mueble.pk).update(stock_disponible=max(0, fabricados - entregados))

@receiver(post_save, sender=Pedido)
def disparar_tareas(sender, instance, created, **kwargs):
    if created:
        for cod, nombre in Tarea.OPCIONES_TAREA:
            Tarea.objects.get_or_create(pedido=instance, nombre=cod)
    recalcular_stock(instance.mueble)

@receiver(post_save, sender=Tarea)
def actualizar_desde_tarea(sender, instance, **kwargs):
    pedido = instance.pedido
    if pedido.estado in ['cancelado', 'entregado']:
        return

    # Si se termina el diseño, pasa a Producción
    if instance.nombre == '1_DISENO' and instance.terminado:
        if pedido.estado == 'pendiente':
            pedido.estado = 'produccion'
            pedido.save(update_fields=['estado'])
    
    # Si se termina el último paso, pasa a Listo
    elif instance.nombre == '9_LISTO' and instance.terminado:
        pedido.estado = 'listo'
        pedido.save(update_fields=['estado'])
    
    recalcular_stock(pedido.mueble)

@receiver(post_delete, sender=Pedido)
def al_eliminar(sender, instance, **kwargs):
    recalcular_stock(instance.mueble)