# CVLaTeX Web

Editor gratuito de currículums inspirado en un CV profesional de dos columnas.

## Funciones actuales
- Editar nombre, cargo, correo, teléfono, ciudad y perfil.
- Añadir, modificar o eliminar experiencias, conocimientos, idiomas y estudios.
- Personalizar dos colores.
- Ver el resultado en formato A4.
- Conservar un borrador en el navegador (localStorage).
- Guardar como PDF mediante la opción Imprimir > Guardar como PDF.
- Descargar código fuente .tex que puede compilarse con XeLaTeX o LuaLaTeX.

**Importante:** El botón PDF actualmente usa la impresión del navegador: el PDF todavía no está compilado directamente desde LaTeX. La plantilla LaTeX y la vista previa HTML pueden tener diferencias de diseño.

## Publicación
El proyecto no requiere proceso de compilación de frontend. Para publicarlo en Cloudflare Pages, conecta el repositorio y configura:
- Framework preset: None
- Production branch: main
- Build command: exit 0 (o ninguno cuando sea permitido)
- Output directory: .

Cada cambio confirmado en main se publicará automáticamente tras completar el despliegue.

## Privacidad
Los datos del CV se guardan únicamente en el almacenamiento local del navegador. No se envían a ningún backend en esta versión.

## Próximos pasos
- Compilación segura de LaTeX a PDF en servidor aislado.
- Mejorar fidelidad tipográfica respecto al documento de referencia.
- Política de privacidad, página informativa y SEO para un lanzamiento público.

## Uso local
Abre index.html en un navegador moderno.