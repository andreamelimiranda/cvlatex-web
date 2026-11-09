"""
Mapa de direcciones del sitio: qué vista responde a cada URL.

  /cuenta/...   registro, entrar, salir, contraseñas   (app cuentas)
  /admin/       panel de administración de Django
  todo lo demás páginas públicas, «Mis CVs» y la API   (app cvs)
"""

from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Administración de MICV"
admin.site.site_title = "MICV"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuenta/", include("cuentas.urls")),
    path("", include("cvs.urls")),  # va al final porque incluye /<página>
]
