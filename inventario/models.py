from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError 

# ==============================================================================
# --- 1. MODELO DE INSUMOS ---
# ==============================================================================
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

# ==============================================================================
# --- 2. MODELO DE MUEBLES (CON GALERÍA) ---
# ==============================================================================
class Mueble(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=0)
    costo_placa_entera = models.DecimalField(max_digits=12, decimal_places=0)
    ancho_placa_cm = models.FloatField(default=183)
    largo_placa_cm = models.FloatField(default=260)
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

# --- NUEVO: MODELO PARA MÚLTIPLES FOTOS ---
class FotoMueble(models.Model):
    mueble = models.ForeignKey(Mueble, related_name='fotos', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='muebles/galeria/')
    descripcion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Foto de detalle"
        verbose_name_plural = "Fotos de detalles"

# ==============================================================================
# --- 3. PIEZAS Y RECETAS ---
# ==============================================================================
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

# ==============================================================================
# --- 4. CLIENTES (MODELO MEJORADO) ---
# ==============================================================================
class Cliente(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombres")
    apellido = models.CharField(max_length=100, verbose_name="Apellidos")
    ruc_cedula = models.CharField(max_length=20, unique=True, verbose_name="RUC o Cédula")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    
    # --- Dirección Detallada ---
    ciudad = models.CharField(max_length=100, verbose_name="Ciudad")
    barrio = models.CharField(max_length=100, verbose_name="Barrio")
    calle_principal = models.CharField(max_length=150, verbose_name="Calle Principal")
    numero_casa = models.CharField(max_length=20, verbose_name="N° de Casa")
    calle_lateral_1 = models.CharField(max_length=150, blank=True, null=True, verbose_name="Calle Lateral 1")
    calle_lateral_2 = models.CharField(max_length=150, blank=True, null=True, verbose_name="Calle Lateral 2")
    
    # --- Referencia y Mapa ---
    referencia_ubicacion = models.TextField(blank=True, null=True, verbose_name="Referencia de Ubicación")
    geolocalizacion = models.URLField(
        blank=True, 
        null=True, 
        help_text="Pega aquí el enlace de Google Maps (URL)",
        verbose_name="Enlace Google Maps"
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.ruc_cedula}"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
# ==============================================================================
# --- 5. PEDIDOS (SÓLO INFORMACIÓN SOLICITADA) ---
# ==============================================================================
class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Información del Cliente")
    mueble = models.ForeignKey(Mueble, on_delete=models.CASCADE, verbose_name="Información del Mueble")
    fecha_pedido = models.DateField(auto_now_add=True, verbose_name="Fecha de Pedido")

    def __str__(self):
        return f"Pedido: {self.cliente} - {self.mueble.nombre} ({self.fecha_pedido})"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
# ==============================================================================
# --- 6. PERSONAL (ESTRUCTURA COMPLETA) ---
# ==============================================================================
class Personal(models.Model):
    # Vincular con el sistema de usuarios para el Login
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Usuario de Sistema")
    
    nombre = models.CharField(max_length=100, verbose_name="Nombres")
    apellido = models.CharField(max_length=100, verbose_name="Apellidos")
    ruc_cedula = models.CharField(max_length=20, unique=True, verbose_name="RUC o Cédula")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono", blank=True, null=True)
    email = models.EmailField(verbose_name="Correo Electrónico", blank=True, null=True)
    direccion = models.CharField(max_length=255, verbose_name="Dirección", blank=True, null=True)
    especialidad = models.CharField(max_length=100, verbose_name="Especialidad")

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.ruc_cedula}) - {self.especialidad}"

    class Meta:
        verbose_name = "Personal"
        verbose_name_plural = "Personal"

# ==============================================================================
# --- 7. ÓRDENES DE TRABAJO (COORDINADAS) ---
# ==============================================================================
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class OrdenTrabajo(models.Model):
    pedido = models.OneToOneField('Pedido', on_delete=models.CASCADE, verbose_name="Pedido Relacionado")
    personal_asignado = models.ManyToManyField('Personal', verbose_name="Personal Asignado")
    
    corte = models.BooleanField(default=False, verbose_name="Corte")
    canteado = models.BooleanField(default=False, verbose_name="Canteado")
    armado = models.BooleanField(default=False, verbose_name="Armado")
    limpieza = models.BooleanField(default=False, verbose_name="Limpieza")
    empaquetado = models.BooleanField(default=False, verbose_name="Empaquetado")

    finalizado = models.BooleanField(default=False, verbose_name="¿Orden Terminada?")
    fecha_inicio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Finalización")

    def __str__(self):
        return f"OT: {self.pedido}"

    def save(self, *args, **kwargs):
        # 1. LÓGICA AUTOMÁTICA DE FINALIZACIÓN
        # Revisamos si todas las tareas están marcadas
        tareas = [self.corte, self.canteado, self.armado, self.limpieza, self.empaquetado]
        
        if all(tareas):
            self.finalizado = True
            if not self.fecha_fin:
                self.fecha_fin = timezone.now()
        else:
            self.finalizado = False
            self.fecha_fin = None

        # 2. PROCESO DE STOCK (Antes de validar para asegurar que se ejecute)
        if self.pk:
            # Traemos la orden de la base de datos para comparar
            orden_previa = OrdenTrabajo.objects.get(pk=self.pk)
            # Accedemos al mueble a través del pedido (ajustar si el campo en Pedido se llama distinto)
            mueble_relacionado = getattr(self.pedido, 'mueble', None)

            if mueble_relacionado:
                # Si ahora se marcó empaquetado y antes no estaba
                if not orden_previa.empaquetado and self.empaquetado:
                    mueble_relacionado.stock_disponible += 1
                    mueble_relacionado.save()
                # Si se desmarcó empaquetado
                elif orden_previa.empaquetado and not self.empaquetado:
                    if mueble_relacionado.stock_disponible > 0:
                        mueble_relacionado.stock_disponible -= 1
                        mueble_relacionado.save()

        # 3. GUARDADO FINAL
        # Nota: Quitamos full_clean() de aquí para que el Admin maneje la validación
        # y no bloquee el proceso de guardado del stock.
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"