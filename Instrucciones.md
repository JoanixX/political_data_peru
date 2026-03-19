# INSTRUCCIONES DEL PROYECTO (NO SUBIR AL GITHUB)

## REGLAS DE COMENTARIOS Y FORMATO PARA COMMITS, MD, COMENTARIOS Y CÓDIGO
- DEBE incluir un README.md que se actualice siempre que se realiza un cambio o se agrega alguna funcionalidad o servicio. Además, este README.md debe explicar la arquitectura, stack, experiencia adquirida y su fase en producción, para cada carpeta, por ejemplo uno para el frontend, backend, y cada servicio que lo requiera.
- DEBE tener absolutamente todos los comentarios en español, y explicarlo de forma muy clara y concisa, como si fuera hecho por un humano, por ejemplo que en vez de ser "# Este es un comentario de la línea 67.", sea: "# este es un comentario", o sea todo en minúscula y de manera informal, como si lo dijera un humano.
- DEBE tener todos los .md (Markdown) en español y siempre se deben actualizar constantemente de acuerdo a los cambios que hayan.
- DEBE tener los commits tomando en cuenta esto: "feat: Este es un commit generado, no debería ser así. El uso de WebSockets y Neon no debe ser así por ejemplo.", "feat: Este es un commit real y en español, los websockets y neon deben ser así también."
- DEBES hacer que por funcionalidad o servicio se realice un commit, no un solo commit grande que incluya todo. Esto es algo que se tiene que tomar en cuenta siempre y se debe devolver una lista de commits para copiar y pegar.
- DEBES hacer caso omiso a los formatos diferenciados para commits, markdowns, documentación y comentarios SÓLO Y EXCLUSIVAMENTE en el caso de los textos de la página o mensajes de errores del código. O sea, que los mensajes de error, nombres de código, o los nombres y textos que se muestran en el frontend si deben tener sí o sí mayúsculas correctas, puntuación correcta y ortografía correcta.
- DEBES hacer un archivo sólo para ti que sea un .md llamado "Instrucciones" (No se sube al GitHub), que incluya todas las restricciones que hay en esta sección de reglas y formatos de commits, markdowns, documentación, comentarios, código, etc (Que incluya también las reglas de seguridad y restricciones de sistema de archivos). Además, este tiene que actualizarse con la arquitectura, tecnologías, habilidades nuevas conforme avance el proyecto. De este modo, solo se los .md de la carpeta o funcionalidad específica cuando se desee la documentación necesaria para agregar algo y tener el contexto relevante (de todas formas, siempre se leerá el Instrucciones.md).

## REGLAS DE SEGURIDAD Y RESTRICCIONES DE SISTEMA DE ARCHIVOS
- SOLO se permite leer, modificar, crear o eliminar archivos que estén estrictamente dentro del directorio raíz del proyecto actual. Se considera directorio raíz únicamente la carpeta donde se encuentra el código del proyecto y todas sus subcarpetas internas. Bajo ninguna circunstancia se puede salir de este alcance.
- ESTÁ TERMINANTEMENTE PROHIBIDO acceder, modificar, crear o eliminar archivos fuera de la carpeta del proyecto. Esto incluye cualquier ruta absoluta como `C:\`, `D:\`, `/`, `/usr/`, `/etc/`, `/home/`, `~/`, `AppData`, `Program Files`, `Windows`, o cualquier otra ruta perteneciente al sistema operativo o al usuario.
- NO se permite el uso de rutas absolutas en el código ni en comandos. Todas las rutas deben ser relativas al proyecto. Si por alguna razón se detecta una ruta que no sea claramente relativa al proyecto, se debe detener cualquier acción y solicitar autorización explícita antes de continuar.
- NO se permite crear archivos temporales fuera del proyecto. Si se requieren archivos temporales, estos deben generarse exclusivamente dentro de una carpeta interna del proyecto destinada para ese propósito (por ejemplo `/tmp` o `/temp` dentro del proyecto).
- ESTÁ PROHIBIDO ejecutar comandos que afecten directa o indirectamente al sistema operativo, incluyendo pero no limitado a instalación de paquetes globales, modificación de variables de entorno, alteración de configuraciones del sistema, manipulación del registro del sistema, cambios en permisos del sistema o cualquier operación que requiera privilegios de administrador.
- NO se permite el uso de comandos potencialmente destructivos como `rm -rf`, `del /s`, `format`, `shutdown`, `reboot`, ni ninguna variante que pueda eliminar o alterar archivos fuera del alcance del proyecto.
- NO se permite modificar configuraciones globales de herramientas, gestores de paquetes, entornos de ejecución o configuraciones del sistema operativo. Toda configuración debe permanecer encapsulada dentro del proyecto.
- SI alguna instrucción, requerimiento o cambio solicitado implica directa o indirectamente interactuar con el sistema fuera del proyecto, se debe detener inmediatamente la ejecución, explicar claramente el riesgo técnico involucrado y esperar autorización explícita antes de proceder.
- SI existe cualquier ambigüedad sobre si una acción afecta o no al sistema fuera del proyecto, se debe asumir que es potencialmente riesgosa y solicitar confirmación antes de continuar.
- NUNCA se debe asumir que se tienen permisos de administrador ni capacidades ilimitadas sobre el entorno de ejecución.
- EL PRINCIPIO GENERAL ES AISLAMIENTO TOTAL: todas las operaciones deben estar estrictamente contenidas dentro del proyecto y no deben comprometer la estabilidad, integridad o seguridad del sistema operativo anfitrión.

## CONTEXTO TÉCNICO ACTUAL (ACTUALIZADO 19/03/2026)
- **proyecto**: political_data_peru (inteligencia de datos públicos).
- **stack**: python (pandas, polars, fastapi), postgresql, parquet, docker, docker compose, next.js (frontend).
- **arquitectura**: modular / medallion architecture (bronze, silver, gold layers).
- **habilidades**: extracción inmutable, normalización de datos heterogéneos, resolución de identidades político-sociales.
