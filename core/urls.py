"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
Configuración de URLs principal del proyecto
"""
from django.contrib import admin
from django.urls import path, include
from inventario.views import salir_limpio # Tu función personalizada

urlpatterns = [
    # 1. El Admin se queda con su propia lógica interna
    path('admin/', admin.site.urls),
    
    path('inventario/', include('inventario.urls')),

    # 2. Solo este 'salir' mandará al login de operarios
    # Es el que usa tu botón {% url 'salir' %}
    path('logout-taller/', salir_limpio, name='salir'),
]
admin.site.site_header = "Sistema de Gestion de Carpinteria"
admin.site.site_title = "Portal de Gestión"
admin.site.index_title = "Panel de Control - Inventario y Producción"
# Personalización de la interfaz del Admin
