# Instrucciones.md

## propósito de este archivo

este archivo es la fuente de verdad operativa del proyecto para reglas persistentes que deben mantenerse entre iteraciones, servicios, funcionalidades y cambios futuros.

debe leerse antes de realizar cualquier modificación dentro del proyecto. si ya existe, debe actualizarse cuando cambie la arquitectura, se agreguen tecnologías, aparezcan nuevas restricciones, se incorporen habilidades técnicas nuevas o cambien las convenciones globales de trabajo.

este archivo no se sube al repositorio. su propósito es mantener memoria operativa consistente para el agent manager y evitar que reglas importantes se pierdan entre prompts.

---

## alcance y prioridad

estas reglas aplican a todo el proyecto y a todas sus subcarpetas, salvo que exista una instrucción local más específica que no contradiga seguridad, aislamiento, consistencia global o decisiones arquitectónicas ya establecidas.

orden de prioridad recomendado:

1. seguridad operativa y restricciones del sistema de archivos
2. este `Instrucciones.md`
3. instrucciones específicas del servicio o tarea actual
4. preferencias técnicas no críticas
5. optimizaciones opcionales

si una instrucción contradice este archivo y además compromete seguridad, aislamiento o consistencia global, debe priorizarse este archivo.

---

## reglas de comentarios en código

todos los comentarios del código deben estar en español.

los comentarios deben ser:

- claros
- útiles
- directos
- naturales
- escritos como lo haría una persona real
- orientados a explicar intención, contexto o responsabilidad técnica

los comentarios no deben ser:

- robóticos
- redundantes
- decorativos
- demasiado obvios
- del tipo “este es un comentario de la línea x”
- del tipo “esta función hace algo”
- del tipo “se imprime el valor”
- comentarios que repiten exactamente lo que ya dice el código sin aportar contexto

cuando sea razonable dentro del contexto técnico, los comentarios deben escribirse en minúscula y con tono natural. por ejemplo:

- correcto: `# valida el token antes de entrar al caso de uso`
- correcto: `# este adaptador transforma la respuesta externa al formato del dominio`
- incorrecto: `# Este Comentario Explica La Línea 42`
- incorrecto: `# esta es la función handle_user_request`
- incorrecto: `# comentario generado automáticamente`

los comentarios deben explicar una o más de estas cosas cuando haga falta:

- por qué existe una decisión
- qué responsabilidad tiene una pieza
- qué no debe hacerse en ese lugar
- qué riesgo técnico se está evitando
- qué dependencia se está desacoplando
- qué supuesto importante hay detrás del código
- qué parte del flujo está representando

si una parte del código es suficientemente clara por sí sola, no se debe comentar por obligación.

---

## reglas de documentación markdown

todos los archivos `.md` deben estar en español.

toda documentación markdown debe mantenerse alineada con el estado real del proyecto. no se debe dejar documentación obsoleta, contradictoria o vacía.

cada archivo markdown debe existir por una razón clara. no debe crearse documentación de relleno.

la documentación debe ser:

- útil
- mantenible
- concreta
- coherente con la arquitectura real
- consistente con la estructura del proyecto
- suficiente para dar contexto técnico y operativo

cuando cambie algo importante, la documentación afectada debe actualizarse. esto incluye, como mínimo:

- nuevas funcionalidades
- nuevos servicios
- nuevas carpetas o módulos con responsabilidad propia
- cambios arquitectónicos
- cambios de stack
- cambios de despliegue
- nuevas variables de entorno
- nuevas integraciones
- decisiones técnicas que cambien la forma de operar

---

## reglas de README

cada componente relevante del proyecto debe tener su `README.md` cuando aporte valor real, por ejemplo frontend, backend o servicios con responsabilidad propia.

cada `README.md` debe mantenerse actualizado cuando cambie algo importante en su alcance.

el `README.md` debe explicar, según corresponda:

- propósito del componente
- contexto dentro del producto
- arquitectura usada
- stack
- estructura de carpetas
- cómo ejecutarlo
- variables de entorno necesarias
- cómo se despliega
- cómo se conecta con otras partes del sistema
- estado de madurez
- decisiones técnicas relevantes

el README no debe ser genérico ni parecer una plantilla vacía.

---

## reglas de commits

los commits deben estar en español.

cada commit debe representar un cambio lógico, entendible y trazable. no se debe hacer un solo commit gigante con muchos cambios sin relación clara.

los commits deben:

- reflejar cambios reales
- estar segmentados por funcionalidad, servicio o ajuste coherente
- evitar mensajes vagos
- evitar mensajes artificiales
- evitar mensajes autoreferenciales
- permitir reconstruir la evolución del proyecto con claridad

formato esperado:

- `feat: agrego estructura base del backend con arquitectura hexagonal`
- `fix: corrijo validación de variables de entorno en desarrollo local`
- `docs: actualizo readme del frontend con flujo de pruebas`
- `refactor: separo adaptadores de persistencia del caso de uso`
- `chore: agrego gitignore explícito para secretos y artefactos temporales`

no usar mensajes como:

- `feat: cambios varios`
- `fix: arreglos`
- `update: actualización`
- `feat: commit real`
- `docs: cosas del readme`

si una tarea grande requiere varias partes, deben proponerse varios commits pequeños y coherentes.

---

## excepción para textos visibles del producto

las reglas de comentarios, markdown informal o minúsculas no aplican a textos visibles del producto.

esto incluye:

- textos de interfaz
- mensajes mostrados al usuario
- mensajes de error visibles
- títulos de páginas
- labels
- placeholders
- correos visibles al usuario
- contenido UX
- mensajes transaccionales

en esos casos sí deben usarse mayúsculas, puntuación, ortografía y estilo correctos según el contexto del producto.

tampoco se debe forzar minúscula en:

- nombres propios
- siglas
- identificadores técnicos
- nombres de librerías
- convenciones del lenguaje
- claves o nombres que deban respetar un estándar externo

---

## reglas de seguridad operativa y sistema de archivos

toda operación debe mantenerse estrictamente dentro del directorio raíz del proyecto actual y sus subcarpetas internas.

solo se permite leer, modificar, crear o eliminar archivos que estén dentro del proyecto.

está prohibido acceder, modificar, crear o eliminar archivos fuera del proyecto. esto incluye rutas del sistema operativo o del usuario, por ejemplo:

- `C:\`
- `D:\`
- `/`
- `/usr/`
- `/etc/`
- `/home/`
- `~/`
- `AppData`
- `Program Files`
- `Windows`
- cualquier otra ruta que no pertenezca al proyecto actual

no se permite el uso de rutas absolutas en código, scripts o comandos. todas las rutas deben ser relativas al proyecto.

si se detecta una ruta que no sea claramente relativa al proyecto, debe detenerse la acción y solicitar autorización explícita antes de continuar.

no se permite crear archivos temporales fuera del proyecto. si se necesitan temporales, deben vivir dentro de una carpeta interna del propio proyecto, por ejemplo:

- `./tmp`
- `./temp`
- otra carpeta equivalente dentro del repositorio o directorio raíz del proyecto

está prohibido ejecutar comandos que afecten directa o indirectamente al sistema operativo anfitrión. esto incluye, entre otros:

- instalaciones globales
- cambios en variables globales del sistema
- cambios de configuración del sistema
- cambios en permisos del sistema
- manipulación del registro
- acciones que requieran privilegios de administrador
- alteraciones globales de herramientas o gestores de paquetes

no se permite modificar configuraciones globales de:

- herramientas
- gestores de paquetes
- runtimes
- shells
- sistema operativo
- entorno del usuario

toda configuración debe permanecer encapsulada dentro del proyecto.

está prohibido ejecutar comandos potencialmente destructivos, incluyendo variantes o equivalentes de:

- `rm -rf`
- `del /s`
- `format`
- `shutdown`
- `reboot`

tampoco se debe ejecutar ninguna acción ambigua que pueda eliminar, alterar o comprometer archivos fuera del proyecto.

si una instrucción, requerimiento o cambio solicitado implica directa o indirectamente interactuar con el sistema fuera del proyecto, se debe detener la ejecución, explicar el riesgo técnico y esperar autorización explícita antes de proceder.

si existe cualquier ambigüedad sobre si una acción afecta o no al sistema fuera del proyecto, debe asumirse que es potencialmente riesgosa hasta que se confirme lo contrario.

nunca se debe asumir que existen permisos de administrador ni capacidades ilimitadas sobre el entorno de ejecución.

el principio general es aislamiento total: todas las operaciones deben permanecer contenidas dentro del proyecto y no deben comprometer la estabilidad, integridad ni seguridad del sistema anfitrión.

---

## reglas de archivos privados y versionado

este archivo `Instrucciones.md` no debe subirse al repositorio.

tampoco deben subirse al repositorio los archivos privados o sensibles del proyecto, incluyendo, según corresponda:

- `.env`
- `.env.production`
- scripts locales para generación de secretos
- credenciales
- llaves
- tokens
- temporales
- artefactos locales de pruebas
- datos sensibles no versionables

sí debe existir una plantilla versionable como `.env.example` para documentar variables necesarias sin exponer secretos reales.

---

## reglas de mantenimiento de este archivo

este archivo debe actualizarse cuando ocurra cualquiera de estas situaciones:

- se agrega una nueva regla persistente
- cambia la arquitectura global
- cambia el stack principal
- se incorpora una nueva tecnología importante
- se detecta una convención que debe mantenerse entre iteraciones
- aparece una nueva restricción de seguridad
- cambia la forma correcta de documentar o commitear
- cambia el alcance operativo del agent manager
- se aprende una lección técnica que deba conservarse como memoria del proyecto

no debe crecer con ruido innecesario. debe mantenerse claro, útil y vigente.

---

## criterio general de trabajo

si una acción mejora velocidad pero pone en riesgo seguridad, aislamiento, claridad o mantenibilidad, se debe priorizar seguridad, aislamiento, claridad y mantenibilidad.

si una instrucción es ambigua, no debe interpretarse de la forma más agresiva. debe priorizarse la opción más segura, local y reversible, o solicitar autorización si el riesgo es real.

si una regla de este archivo ya está cubierta por una instrucción local más específica y compatible, ambas deben convivir sin contradicción.

este archivo funciona como memoria operativa persistente. debe leerse siempre antes de modificar el proyecto.
