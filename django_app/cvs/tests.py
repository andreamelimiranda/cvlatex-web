"""
Pruebas automáticas de la app «cvs».

Ejecútalas con:   python manage.py test
Cada prueba arma una base de datos vacía, hace peticiones como si fuera un
navegador y revisa que la respuesta sea la esperada.
"""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CV

CV_EJEMPLO = {
    "name": "Camila Rojas",
    "role": "Operaria de bodega",
    "template": "modern",
    "jobs": [{"title": "Picking", "company": "Centro de distribución"}],
    "skills": [],
    "languages": [],
    "education": [],
}


class PaginasPublicasTests(TestCase):
    def test_portada_muestra_el_editor_con_cuentas(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "cvs/cuenta.js")       # se agregó el script de cuentas
        self.assertIn("csrftoken", r.cookies)         # cookie para poder guardar

    def test_guias_con_y_sin_html(self):
        for url in ["/guia-cv.html", "/guia-cv", "/contacto.html", "/privacidad"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_pagina_desconocida_da_404(self):
        self.assertEqual(self.client.get("/no-existe.html").status_code, 404)
        self.assertEqual(self.client.get("/settings.html").status_code, 404)

    def test_archivos_planos(self):
        r = self.client.get("/ads.txt")
        self.assertEqual(r.status_code, 200)
        self.assertIn("google.com", b"".join(r.streaming_content).decode())


class ApiCvsTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.ana = Usuario.objects.create_user("ana", "ana@ejemplo.cl", "clave-segura-123")
        self.beto = Usuario.objects.create_user("beto", "beto@ejemplo.cl", "clave-segura-123")

    def enviar(self, metodo, url, cuerpo):
        return getattr(self.client, metodo)(url, data=json.dumps(cuerpo), content_type="application/json")

    def test_sin_sesion_responde_401(self):
        self.assertEqual(self.client.get("/api/cvs/").status_code, 401)
        self.assertEqual(self.client.get("/api/yo/").json(), {"autenticado": False})

    def test_crear_listar_abrir_actualizar_y_borrar(self):
        self.client.force_login(self.ana)

        r = self.enviar("post", "/api/cvs/", {"titulo": "CV bodega", "datos": CV_EJEMPLO})
        self.assertEqual(r.status_code, 201)
        cv_id = r.json()["id"]
        self.assertEqual(r.json()["plantilla"], "Moderno profesional")

        self.assertEqual(len(self.client.get("/api/cvs/").json()["cvs"]), 1)
        self.assertEqual(self.client.get(f"/api/cvs/{cv_id}/").json()["datos"]["name"], "Camila Rojas")

        nuevos = {**CV_EJEMPLO, "name": "Camila R."}
        r = self.enviar("put", f"/api/cvs/{cv_id}/", {"datos": nuevos})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(CV.objects.get(pk=cv_id).datos["name"], "Camila R.")

        self.assertEqual(self.client.delete(f"/api/cvs/{cv_id}/").status_code, 200)
        self.assertFalse(CV.objects.exists())

    def test_titulo_por_defecto_es_el_nombre(self):
        self.client.force_login(self.ana)
        r = self.enviar("post", "/api/cvs/", {"datos": CV_EJEMPLO})
        self.assertEqual(r.json()["titulo"], "Camila Rojas")

    def test_nadie_puede_ver_ni_tocar_cvs_ajenos(self):
        cv = CV.objects.create(usuario=self.ana, titulo="Privado", datos=CV_EJEMPLO)
        self.client.force_login(self.beto)
        self.assertEqual(self.client.get(f"/api/cvs/{cv.pk}/").status_code, 404)
        self.assertEqual(self.enviar("put", f"/api/cvs/{cv.pk}/", {"titulo": "X"}).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/cvs/{cv.pk}/").status_code, 404)
        self.assertEqual(self.client.get(reverse("borrar_cv", args=[cv.pk])).status_code, 404)
        self.assertEqual(self.client.get("/api/cvs/").json()["cvs"], [])
        self.assertTrue(CV.objects.filter(pk=cv.pk).exists())

    def test_datos_invalidos(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.enviar("post", "/api/cvs/", {"datos": {"name": "sin secciones"}}).status_code, 400)
        r = self.client.post("/api/cvs/", data="esto no es json", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_cv_demasiado_grande(self):
        self.client.force_login(self.ana)
        grande = {**CV_EJEMPLO, "photo": "x" * (3 * 1024 * 1024 + 10)}
        self.assertEqual(self.enviar("post", "/api/cvs/", {"datos": grande}).status_code, 413)

    def test_la_api_exige_csrf(self):
        from django.test import Client

        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.ana)
        r = cliente.post("/api/cvs/", data=json.dumps({"datos": CV_EJEMPLO}), content_type="application/json")
        self.assertEqual(r.status_code, 403)


class MisCvsTests(TestCase):
    def setUp(self):
        self.ana = get_user_model().objects.create_user("ana", "ana@ejemplo.cl", "clave-segura-123")
        self.cv = CV.objects.create(usuario=self.ana, titulo="CV bodega", datos=CV_EJEMPLO)

    def test_pide_iniciar_sesion(self):
        r = self.client.get("/mis-cvs/")
        self.assertRedirects(r, "/cuenta/entrar/?next=/mis-cvs/")

    def test_lista_renombrar_y_borrar(self):
        self.client.force_login(self.ana)
        r = self.client.get("/mis-cvs/")
        self.assertContains(r, "CV bodega")
        self.assertContains(r, f"/?cv={self.cv.pk}")

        r = self.client.post(reverse("renombrar_cv", args=[self.cv.pk]), {"titulo": "CV retail"})
        self.assertRedirects(r, "/mis-cvs/")
        self.cv.refresh_from_db()
        self.assertEqual(self.cv.titulo, "CV retail")

        self.assertContains(self.client.get(reverse("borrar_cv", args=[self.cv.pk])), "¿Borrar")
        r = self.client.post(reverse("borrar_cv", args=[self.cv.pk]))
        self.assertRedirects(r, "/mis-cvs/")
        self.assertFalse(CV.objects.exists())
