from django.conf import settings
from django.db import models

# Nombres de las plantillas tal como las usa el editor (data.template).
PLANTILLAS = {
    "modern": "Moderno profesional",
    "original": "Original",
    "classic": "Clásico elegante",
    "ats": "Minimalista ATS",
}


class CV(models.Model):
    """Un currículum guardado por una persona.

    El editor de MICV trabaja con un objeto de JavaScript (nombre, cargo,
    experiencia, estudios, etc.). Lo guardamos tal cual en un campo JSON:
    así el editor puede seguir creciendo sin cambiar la base de datos.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,   # si se borra la cuenta, se borran sus CVs
        related_name="cvs",
        verbose_name="usuario",
    )
    titulo = models.CharField("título", max_length=120)
    datos = models.JSONField("datos del editor")
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["-actualizado"]  # el más reciente primero
        verbose_name = "currículum"
        verbose_name_plural = "currículums"

    def __str__(self):
        return f"{self.titulo} ({self.usuario})"

    @property
    def plantilla(self):
        """Nombre legible de la plantilla que eligió la persona."""
        clave = (self.datos or {}).get("template", "original")
        return PLANTILLAS.get(clave, PLANTILLAS["original"])

    def resumen(self):
        """Lo que mostramos en la lista «Mis CVs» y en la API."""
        return {
            "id": self.pk,
            "titulo": self.titulo,
            "plantilla": self.plantilla,
            "actualizado": self.actualizado.isoformat(),
        }
