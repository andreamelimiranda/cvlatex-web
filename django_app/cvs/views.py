"""
Vistas de la app «cvs».

Una «vista» es una función que recibe una petición del navegador (request)
y devuelve una respuesta (una página HTML, un JSON, una redirección...).

Aquí hay tres grupos:
  1. Páginas públicas: la portada con el editor y las guías (los mismos .html
     que ya tenía el sitio), más ads.txt, robots.txt y sitemap.xml.
  2. «Mis CVs»: la lista de currículums de la persona, renombrar y borrar.
  3. La API: pequeñas direcciones que usa el editor (JavaScript) para
     guardar y abrir CVs sin recargar la página.
"""

import json
from functools import lru_cache

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .forms import RenombrarForm
from .models import CV

# --------------------------------------------------------------------------
# 1. Páginas públicas
# --------------------------------------------------------------------------

# Solo estas páginas se pueden pedir (así nadie puede leer otros archivos).
PAGINAS = {
    "recursos",
    "guia-cv",
    "cv-ats",
    "cv-sin-experiencia",
    "cv-operario-bodega",
    "entrevista-laboral",
    "errores-curriculum",
    "contacto",
    "privacidad",
}
ARCHIVOS_PLANOS = {
    "ads.txt": "text/plain",
    "robots.txt": "text/plain",
    "sitemap.xml": "application/xml",
}


def _leer(nombre):
    return (settings.SITIO_DIR / nombre).read_text(encoding="utf-8")


# En el servidor guardamos las páginas en memoria (lru_cache) para no leer el
# disco en cada visita. En tu computador (DEBUG) se leen siempre de nuevo,
# así ves al instante los cambios que hagas en los .html.
_leer_en_cache = lru_cache(maxsize=32)(_leer)


def _pagina_con_cuentas(nombre):
    """Devuelve el HTML de la página con el script de cuentas agregado al final."""
    html = _leer(nombre) if settings.DEBUG else _leer_en_cache(nombre)
    extra = (
        f'<link rel="stylesheet" href="{static("cvs/cuenta.css")}">'
        f'<script src="{static("cvs/cuenta.js")}" defer></script>'
    )
    return html.replace("</body>", extra + "</body>", 1)


@ensure_csrf_cookie  # deja la cookie csrftoken que el editor necesita para guardar
def portada(request):
    return HttpResponse(_pagina_con_cuentas("index.html"))


@ensure_csrf_cookie
def pagina(request, nombre):
    if nombre not in PAGINAS:
        raise Http404("Página no encontrada")
    return HttpResponse(_pagina_con_cuentas(f"{nombre}.html"))


def archivo_plano(request, nombre):
    if nombre not in ARCHIVOS_PLANOS:
        raise Http404
    return FileResponse(
        open(settings.SITIO_DIR / nombre, "rb"),
        content_type=ARCHIVOS_PLANOS[nombre],
    )


# --------------------------------------------------------------------------
# 2. «Mis CVs»
# --------------------------------------------------------------------------

@login_required  # si no ha iniciado sesión, la manda a la página de entrar
def mis_cvs(request):
    cvs = request.user.cvs.all()
    return render(request, "cvs/mis_cvs.html", {"cvs": cvs})


@login_required
def renombrar(request, pk):
    # get_object_or_404 con usuario=request.user: nadie puede tocar CVs ajenos.
    cv = get_object_or_404(CV, pk=pk, usuario=request.user)
    if request.method == "POST":
        form = RenombrarForm(request.POST, instance=cv)
        if form.is_valid():
            form.save()
            messages.success(request, "Nombre actualizado.")
            return redirect("mis_cvs")
    else:
        form = RenombrarForm(instance=cv)
    return render(request, "cvs/renombrar.html", {"form": form, "cv": cv})


@login_required
def borrar(request, pk):
    cv = get_object_or_404(CV, pk=pk, usuario=request.user)
    if request.method == "POST":
        titulo = cv.titulo
        cv.delete()
        messages.success(request, f"Se borró «{titulo}».")
        return redirect("mis_cvs")
    # Con GET mostramos una página de confirmación antes de borrar.
    return render(request, "cvs/borrar.html", {"cv": cv})


# --------------------------------------------------------------------------
# 3. API para el editor
# --------------------------------------------------------------------------

MAX_BYTES_CV = 3 * 1024 * 1024  # 3 MB (alcanza para un CV con foto)
MAX_CVS_POR_USUARIO = 50
CLAVES_OBLIGATORIAS = {"name", "role", "jobs", "skills", "languages", "education"}


def _error(mensaje, estado=400):
    return JsonResponse({"error": mensaje}, status=estado)


def _api_login_required(vista):
    """Como @login_required, pero responde JSON 401 en vez de redirigir."""

    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _error("Inicia sesión para guardar tus CVs.", 401)
        return vista(request, *args, **kwargs)

    envoltura.__name__ = vista.__name__
    return envoltura


def _leer_cuerpo(request):
    """Lee y valida el JSON que envía el editor. Devuelve (datos, titulo) o un error."""
    if len(request.body) > MAX_BYTES_CV:
        return None, _error("El CV es demasiado grande (máximo 3 MB, revisa la foto).", 413)
    try:
        cuerpo = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None, _error("Los datos enviados no son JSON válido.")
    if not isinstance(cuerpo, dict):
        return None, _error("Formato inválido.")

    datos = cuerpo.get("datos")
    if datos is not None:
        if not isinstance(datos, dict) or not CLAVES_OBLIGATORIAS.issubset(datos):
            return None, _error("Faltan secciones obligatorias del currículum.")

    titulo = cuerpo.get("titulo")
    if titulo is not None:
        if not isinstance(titulo, str) or not titulo.strip():
            return None, _error("El título no puede estar vacío.")
        titulo = titulo.strip()[:120]

    return {"datos": datos, "titulo": titulo}, None


def yo(request):
    """Le dice al editor si hay una sesión iniciada."""
    if request.user.is_authenticated:
        return JsonResponse({"autenticado": True, "usuario": request.user.get_username()})
    return JsonResponse({"autenticado": False})


@_api_login_required
@require_http_methods(["GET", "POST"])
def api_cvs(request):
    """GET: lista de CVs.  POST: crea un CV nuevo."""
    if request.method == "GET":
        return JsonResponse({"cvs": [cv.resumen() for cv in request.user.cvs.all()]})

    cuerpo, error = _leer_cuerpo(request)
    if error:
        return error
    if cuerpo["datos"] is None:
        return _error("Faltan los datos del CV.")
    if request.user.cvs.count() >= MAX_CVS_POR_USUARIO:
        return _error(f"Puedes guardar hasta {MAX_CVS_POR_USUARIO} CVs. Borra alguno para seguir.", 409)

    titulo = cuerpo["titulo"] or (cuerpo["datos"].get("name") or "Mi CV")[:120]
    cv = CV.objects.create(usuario=request.user, titulo=titulo, datos=cuerpo["datos"])
    return JsonResponse(cv.resumen(), status=201)


@_api_login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def api_cv(request, pk):
    """GET: abre un CV.  PUT: lo actualiza.  DELETE: lo borra."""
    cv = request.user.cvs.filter(pk=pk).first()
    if cv is None:
        return _error("No encontramos ese CV en tu cuenta.", 404)

    if request.method == "GET":
        return JsonResponse({**cv.resumen(), "datos": cv.datos})

    if request.method == "DELETE":
        cv.delete()
        return JsonResponse({"borrado": True})

    cuerpo, error = _leer_cuerpo(request)
    if error:
        return error
    if cuerpo["datos"] is not None:
        cv.datos = cuerpo["datos"]
    if cuerpo["titulo"]:
        cv.titulo = cuerpo["titulo"]
    cv.save()
    return JsonResponse(cv.resumen())
