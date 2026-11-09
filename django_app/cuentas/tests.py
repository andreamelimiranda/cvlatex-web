"""Pruebas de registro, inicio de sesión y recuperación de contraseña."""

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase


class CuentasTests(TestCase):
    def test_registro_crea_la_cuenta_e_inicia_sesion(self):
        r = self.client.post("/cuenta/registro/", {
            "username": "camila",
            "email": "Camila@Ejemplo.cl",
            "password1": "una-clave-larga-2026",
            "password2": "una-clave-larga-2026",
        })
        self.assertRedirects(r, "/mis-cvs/")
        usuario = get_user_model().objects.get(username="camila")
        self.assertEqual(usuario.email, "camila@ejemplo.cl")
        self.assertEqual(self.client.get("/api/yo/").json()["usuario"], "camila")

    def test_registro_vuelve_a_la_pagina_anterior(self):
        r = self.client.post("/cuenta/registro/?next=/", {
            "username": "diego", "email": "diego@ejemplo.cl",
            "password1": "una-clave-larga-2026", "password2": "una-clave-larga-2026",
            "next": "/?cv=3",
        })
        self.assertRedirects(r, "/?cv=3", fetch_redirect_response=False)

    def test_registro_no_redirige_a_otros_sitios(self):
        r = self.client.post("/cuenta/registro/", {
            "username": "eva", "email": "eva@ejemplo.cl",
            "password1": "una-clave-larga-2026", "password2": "una-clave-larga-2026",
            "next": "https://sitio-malo.com/",
        })
        self.assertRedirects(r, "/mis-cvs/")

    def test_correo_repetido(self):
        get_user_model().objects.create_user("ana", "ana@ejemplo.cl", "clave-segura-123")
        r = self.client.post("/cuenta/registro/", {
            "username": "ana2", "email": "ANA@ejemplo.cl",
            "password1": "una-clave-larga-2026", "password2": "una-clave-larga-2026",
        })
        self.assertContains(r, "Ya existe una cuenta con ese correo.")

    def test_entrar_y_salir(self):
        get_user_model().objects.create_user("ana", "ana@ejemplo.cl", "clave-segura-123")
        r = self.client.post("/cuenta/entrar/", {"username": "ana", "password": "clave-segura-123"})
        self.assertRedirects(r, "/mis-cvs/")
        r = self.client.post("/cuenta/salir/")
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/api/yo/").json(), {"autenticado": False})

    def test_paginas_en_espanol(self):
        self.assertContains(self.client.get("/cuenta/entrar/"), "Entrar a MICV")
        self.assertContains(self.client.get("/cuenta/registro/"), "Crea tu cuenta gratis")
        self.assertContains(self.client.get("/cuenta/contrasena/recuperar/"), "¿Olvidaste tu contraseña?")

    def test_recuperar_contrasena_envia_correo(self):
        get_user_model().objects.create_user("ana", "ana@ejemplo.cl", "clave-segura-123")
        r = self.client.post("/cuenta/contrasena/recuperar/", {"email": "ana@ejemplo.cl"})
        self.assertRedirects(r, "/cuenta/contrasena/recuperar/enviado/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/cuenta/contrasena/nueva/", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].subject, "Crea una contraseña nueva para MICV")
