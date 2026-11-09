from django.urls import path

from . import views

urlpatterns = [
    # Páginas públicas (los mismos .html de siempre)
    path("", views.portada, name="portada"),
    path("ads.txt", views.archivo_plano, {"nombre": "ads.txt"}),
    path("robots.txt", views.archivo_plano, {"nombre": "robots.txt"}),
    path("sitemap.xml", views.archivo_plano, {"nombre": "sitemap.xml"}),

    # «Mis CVs»
    path("mis-cvs/", views.mis_cvs, name="mis_cvs"),
    path("mis-cvs/<int:pk>/renombrar/", views.renombrar, name="renombrar_cv"),
    path("mis-cvs/<int:pk>/borrar/", views.borrar, name="borrar_cv"),

    # API que usa el editor
    path("api/yo/", views.yo, name="api_yo"),
    path("api/cvs/", views.api_cvs, name="api_cvs"),
    path("api/cvs/<int:pk>/", views.api_cv, name="api_cv"),

    # Guías: /guia-cv.html y también /guia-cv (Cloudflare usa la versión sin .html)
    path("<slug:nombre>.html", views.pagina, name="pagina"),
    path("<slug:nombre>", views.pagina),
]
