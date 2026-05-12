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
# --- 2. MODELO DE MUEBLES
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
        return round((self.area_total_utilizada / area_placa) * 100, 2)

    @property
    def costo_madera(self):
        area_placa = self.ancho_placa_cm * self.largo_placa_cm
        if area_placa > 0:
            porcentaje_uso = self.area_total_utilizada / area_placa
            resultado = Decimal(porcentaje_uso) * self.costo_placa_entera
            return int(resultado) # Entero para Guaraníes
        return 0

    @property
    def costo_insumos(self):
        total = sum(Decimal(ri.cantidad) * ri.insumo.precio_referencia for ri in self.receta_set.all())
        return int(total)

    @property
    def costo_total_produccion(self):
        return self.costo_madera + self.costo_insumos

# --- CLASE QUE FALTABA PARA EL ERROR DE IMPORTACIÓN ---
class FotoMueble(models.Model):
    mueble = models.ForeignKey(Mueble, related_name='fotos', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='muebles/galeria/')
    descripcion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Foto de {self.mueble.nombre}"

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
# --- 4. CLIENTES ---
# ==============================================================================
class Cliente(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombres")
    apellido = models.CharField(max_length=100, verbose_name="Apellidos")
    cedula = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Cédula")
    ruc = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="RUC")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    ciudad = models.CharField(max_length=100, verbose_name="Ciudad")
    barrio = models.CharField(max_length=100, verbose_name="Barrio")
    calle_principal = models.CharField(max_length=150, verbose_name="Calle Principal")
    numero_casa = models.CharField(max_length=20, verbose_name="N° de Casa")
    calle_lateral_1 = models.CharField(max_length=150, blank=True, null=True, verbose_name="Calle Lateral 1")
    calle_lateral_2 = models.CharField(max_length=150, blank=True, null=True, verbose_name="Calle Lateral 2")
    referencia_ubicacion = models.TextField(blank=True, null=True, verbose_name="Referencia de Ubicación")
    geolocalizacion = models.URLField(blank=True, null=True, verbose_name="Enlace Google Maps")

    @property
    def identificacion(self):
        if self.ruc: return f"RUC: {self.ruc}"
        if self.cedula: return f"CI: {self.cedula}"
        return "S/D"

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.identificacion}"

    def clean(self):
        if not self.cedula and not self.ruc:
            raise ValidationError("Debe ingresar al menos una Cédula o un RUC.")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

# ==============================================================================
# --- 5. PEDIDOS ---
# ==============================================================================
class Pedido(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('finalizado', 'Finalizado'),
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    mueble = models.ForeignKey(Mueble, on_delete=models.CASCADE, verbose_name="Mueble")
    fecha_pedido = models.DateField(auto_now_add=True, verbose_name="Fecha de Pedido")
    
    # Campo estirado de Orden de Trabajo
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Finalización")
    
    estado = models.CharField(
        max_length=15, 
        choices=ESTADOS, 
        default='pendiente',
        verbose_name="Estado del Pedido"
    )

    def __str__(self):
        return f"Pedido: {self.cliente} - {self.mueble.nombre} [{self.get_estado_display()}]"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

# ==============================================================================
# --- 6. PERSONAL ---
# ==============================================================================
class Personal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Usuario")
    nombre = models.CharField(max_length=100, verbose_name='Nombres')
    apellido = models.CharField(max_length=100, verbose_name='Apellidos')
    cedula = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Cédula")
    ruc = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="RUC")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    especialidad = models.CharField(max_length=100)

    @property
    def identificacion(self):
        if self.ruc: return f"RUC: {self.ruc}"
        if self.cedula: return f"CI: {self.cedula}"
        return "S/D"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.identificacion})"

    def clean(self):
        if not self.cedula and not self.ruc:
            raise ValidationError("El personal debe tener Cédula o RUC.")

    class Meta:
        verbose_name = "Personal"
        verbose_name_plural = "Personal"

# ==============================================================================
# --- 7. ÓRDENES DE TRABAJO ---
# ==============================================================================
class OrdenTrabajo(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, verbose_name="Pedido Relacionado")
    personal_asignado = models.ManyToManyField(Personal, verbose_name="Personal Asignado")
    
    corte = models.BooleanField(default=False, verbose_name="Corte")
    canteado = models.BooleanField(default=False, verbose_name="Canteado")
    armado = models.BooleanField(default=False, verbose_name="Armado")
    limpieza = models.BooleanField(default=False, verbose_name="Limpieza")
    empaquetado = models.BooleanField(default=False, verbose_name="Empaquetado")

    finalizado = models.BooleanField(default=False, verbose_name="¿Orden Terminada?")
    fecha_inicio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Finalización")

    def __str__(self):
        return f"OT: {self.pedido.mueble.nombre} ({self.pedido.cliente.nombre})"

    def clean(self):
        """
        Validación de secuencia lógica para la tesis: 
        No permite saltarse pasos en el proceso de fabricación.
        """
        if self.pk:
            if self.canteado and not self.corte:
                raise ValidationError("No se puede marcar 'Canteado' sin haber terminado el 'Corte'.")
            
            if self.armado and not self.canteado:
                raise ValidationError("No se puede marcar 'Armado' sin haber terminado el 'Canteado'.")
            
            if self.limpieza and not self.armado:
                raise ValidationError("No se puede marcar 'Limpieza' sin haber terminado el 'Armado'.")
            
            if self.empaquetado and not self.limpieza:
                raise ValidationError("No se puede marcar 'Empaquetado' sin haber terminado la 'Limpieza'.")

    def save(self, *args, **kwargs):
        # Ejecuta las validaciones de clean() antes de guardar
        self.full_clean()

        # 1. Finalización automática de la OT
        tareas = [self.corte, self.canteado, self.armado, self.limpieza, self.empaquetado]
        self.finalizado = all(tareas)
        
        if self.finalizado and not self.fecha_fin:
            self.fecha_fin = timezone.now()
        elif not self.finalizado:
            self.fecha_fin = None

        # 2. Lógica de Stock y Sincronización con Pedido
        if self.pk:
            orden_previa = OrdenTrabajo.objects.get(pk=self.pk)
            mueble_relacionado = self.pedido.mueble
            pedido_relacionado = self.pedido

            # SI SE MARCA COMO EMPAQUETADO (Cambio de False a True)
            if not orden_previa.empaquetado and self.empaquetado:
                # Sube stock
                mueble_relacionado.stock_disponible += 1
                mueble_relacionado.save()
                
                # Finaliza Pedido y COPIA LA FECHA
                pedido_relacionado.estado = 'finalizado'
                pedido_relacionado.fecha_fin = self.fecha_fin or timezone.now() # <--- Sincronización de fecha
                pedido_relacionado.save()

            # SI SE DESMARCA EMPAQUETADO (Cambio de True a False)
            elif orden_previa.empaquetado and not self.empaquetado:
                # Baja stock
                if mueble_relacionado.stock_disponible > 0:
                    mueble_relacionado.stock_disponible -= 1
                    mueble_relacionado.save()
                
                # Regresa Pedido a Pendiente y BORRA LA FECHA
                pedido_relacionado.estado = 'pendiente'
                pedido_relacionado.fecha_fin = None # <--- Se limpia la fecha
                pedido_relacionado.save()

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"
# ==============================================================================
# --- 8. FACTURACIÓN ---
# ==============================================================================
class Factura(models.Model):
    CONDICIONES = (
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    )

    # Relación uno a uno con el pedido
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, verbose_name="Pedido Relacionado")
    
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Emisión")
    nro_factura = models.CharField(max_length=20, unique=True, verbose_name="Número de Factura")
    condicion_venta = models.CharField(max_length=10, choices=CONDICIONES, default='contado', verbose_name="Condición")
    
    # Datos históricos
    cliente_nombre = models.CharField(max_length=200, editable=False)
    cliente_ruc = models.CharField(max_length=20, editable=False)
    mueble_nombre = models.CharField(max_length=200, editable=False)
    
    # Montos
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Precio Unitario")
    iva_10 = models.DecimalField(max_digits=12, decimal_places=0, editable=False, verbose_name="IVA 10%")
    total = models.DecimalField(max_digits=12, decimal_places=0, editable=False, verbose_name="Total Gs.")

    def save(self, *args, **kwargs):
        # Al crear la factura por primera vez
        if not self.pk: 
            # Aquí unimos Nombre y Apellido
            self.cliente_nombre = f"{self.pedido.cliente.nombre} {self.pedido.cliente.apellido}"
            
            self.cliente_ruc = self.pedido.cliente.identificacion
            self.mueble_nombre = self.pedido.mueble.nombre
            self.precio_unitario = self.pedido.mueble.precio_venta
            
            self.total = self.precio_unitario
            self.iva_10 = round(self.total / 11)

            # Lógica de stock
            mueble = self.pedido.mueble
            if mueble.stock_disponible > 0:
                mueble.stock_disponible -= 1
                mueble.save()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Factura {self.nro_factura} - {self.cliente_nombre}"

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"