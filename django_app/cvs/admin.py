from django.contrib import admin

from .models import CV


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    """Así se ven los CVs en el panel de administración (/admin/)."""

    list_display = ("titulo", "usuario", "plantilla", "actualizado")
    list_filter = ("actualizado",)
    search_fields = ("titulo", "usuario__username", "usuario__email")
    readonly_fields = ("creado", "actualizado")
