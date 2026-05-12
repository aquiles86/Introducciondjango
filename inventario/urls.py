from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 1. Panel de tareas (donde están las tarjetas de colores)
    path('tareas/', views.lista_tareas_personal, name='lista_tareas'),
    
    # 2. Ruta para los botones de las tarjetas
    path('marcar/<int:ot_id>/<str:tarea>/', views.marcar_tarea, name='marcar_tarea'),
    
    # 3. Tu nuevo Login (el que no es de admin)
    path('login/', auth_views.LoginView.as_view(template_name='inventario/login.html'), name='login'),
    
    # 4. El Logout que evita que vuelvas al panel gris de admin
    path('logout/', auth_views.LogoutView.as_view(), name='salir'),
    path('factura/<int:factura_id>/', views.factura_detalle_view, name='factura_detalle'),
]