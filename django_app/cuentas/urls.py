"""
Direcciones de las cuentas. Casi todo lo pone Django (django.contrib.auth);
nosotros solo elegimos las direcciones en español y las plantillas.
"""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("entrar/", auth_views.LoginView.as_view(), name="entrar"),
    path("salir/", auth_views.LogoutView.as_view(), name="salir"),

    # Cambiar la contraseña (con la sesión iniciada)
    path(
        "contrasena/cambiar/",
        auth_views.PasswordChangeView.as_view(success_url=reverse_lazy("contrasena_cambiada")),
        name="cambiar_contrasena",
    ),
    path(
        "contrasena/cambiada/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="contrasena_cambiada",
    ),

    # Recuperar la contraseña por correo
    path(
        "contrasena/recuperar/",
        auth_views.PasswordResetView.as_view(success_url=reverse_lazy("recuperar_enviado")),
        name="recuperar_contrasena",
    ),
    path(
        "contrasena/recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(),
        name="recuperar_enviado",
    ),
    path(
        "contrasena/nueva/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy("recuperar_listo")),
        name="password_reset_confirm",  # este nombre lo usa el correo de Django
    ),
    path(
        "contrasena/nueva/lista/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="recuperar_listo",
    ),
]
