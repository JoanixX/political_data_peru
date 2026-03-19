# CAPA DE DATOS (DATA LAKE)

## VISION GENERAL
El directorio `data/` funciona como el motor de almacenamiento persistente del proyecto. Sigue una arquitectura de capas (basada en el modelo Medallion) para garantizar la trazabilidad total del dato, desde su captura en bruto hasta su transformacion en conocimiento curado y listo para el analisis.

## ESTRUCTURA DE CAPAS

### 1. RAW (data/raw/) - Capa Bronze
- **Objetivo**: Ingesta inmutable.
- **Descripcion**: Contiene los archivos originales tal cual se extrajeron de las fuentes gubernamentales (JNE, Congreso, etc.) en formatos como JSON, HTML o CSV.
- **Regla de Oro**: Nunca se modifican estos archivos. Si la fuente cambia o se corrompe, esta capa permite reconstruir todo el pipeline.

### 2. STAGING (data/staging/)
- **Objetivo**: Persistencia intermedia para limpieza.
- **Descripcion**: Datos que han pasado por un proceso inicial de limpieza de ruido (tags HTML, espacios extra) pero que aun no estan normalizados.

### 3. NORMALIZED (data/normalized/) - Capa Silver
- **Objetivo**: Estandarizacion de esquemas.
- **Descripcion**: Aqui los datos de diferentes fuentes comparten los mismos nombres de columnas, formatos de fecha (ISO-8601) y reglas de tipado. Permite que un "Nombre" en el JNE sea comparable con un "Nombre" en el Congreso.

### 4. MATCHING (data/matched/)
- **Objetivo**: Resolucion de entidades.
- **Descripcion**: Tablas que vinculan IDs de diferentes fuentes. Es el resultado del proceso de Entity Resolution, donde se determina que registros en diferentes datasets pertenecen a la misma persona fisica o partido politico.

### 5. CURATED (data/curated/) - Capa Gold
- **Objetivo**: Fuente unica de verdad (Single Source of Truth).
- **Descripcion**: Datasets finales, altamente procesados y validados. Esta capa es la que consume el Backend y las herramientas de Analytics.

### 6. EXPORTS (data/exports/)
- **Objetivo**: Distribucion externa.
- **Descripcion**: Snapshots en formatos amigables (CSV, Parquet, Excel) para que analistas externos o periodistas puedan descargar los resultados sin acceder al pipeline completo.

## CONSIDERACIONES TECNICAS
- **Formato**: Se prefiere el uso de Parquet para capas intermedias por su eficiencia en almacenamiento y velocidad de lectura en procesos de Data Science.
- **Versionado**: Los datos no se suben al repositorio (ver .gitignore). Se gestionan localmente o mediante herramientas de versionado de datos en la nube.
