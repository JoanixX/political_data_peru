# LOGICA DEL PIPELINE - DIRECTORIO SRC/

## VISION GENERAL

El directorio `src/` contiene toda la lógica de ingeniería de datos distribuida en módulos independientes y desacoplados. Su arquitectura modular permite que cada etapa del pipeline (Ingesta -> Normalización -> Validación) se ejecute e itere sin comprometer el resto del sistema, utilizando **Polars** como motor de procesamiento distribuido y perezoso (Lazy Evaluation).

## COMPONENTES Y RESPONSABILIDADES TÉCNICAS

### 1. INGESTION (src/ingestion/)

- **Responsabilidad**: Extracción concurrente de datos de portales oficiales (JNE, Congreso).
- **Funcionalidad**: Scrapers optimizados para navegar de forma ética y rápida, descargando miles de archivos JSON estructurados con control de semáforos para no sobrecargar los servidores gubernamentales.
- **Artefactos**: Scripts específicos para cada portal que mantienen el rastro de la fuente original.

### 2. NORMALIZATION (src/normalization/)

Este módulo es el corazón del refinamiento de datos del proyecto (`Capa Silver`).

- **orchestrator.py**: El orquestador principal que consolida todas las categorías (Presidentes, Parlamento, Senadores, Diputados) en un único Parquet unificado. Utiliza la evaluación perezosa de Polars para minimizar el consumo de RAM.
- **cleaners.py (Motor de Limpieza)**: Conjunto de expresiones de Polars diseñadas para la normalización en tiempo de ejecución:
  - **Limpiador Financiero**: expresiones RegEx que transforman cadenas monetarias complejas a `Float64`.
  - **Normalizador de Identidad**: padding de DNI con ceros a la izquierda y limpieza de decimales fantasmas.
  - **Estandarización de Texto**: eliminación de tildes, carácteres especiales, espacios múltiples y normalización tipográfica (UpperCase/TitleCase).
- **standards.py (Global ID Engine)**: Generador de identidades deterministas mediante **UUID v5**. Utiliza un Namespace DNS fijo para asegurar que el mismo político reciba el mismo identificador único a través de todas las fases del proyecto, utilizando el DNI o una clave compuesta como semilla.

### 3. VALIDATION (src/validation/)

Encargado de la integridad y salud del Data Lake.

- **schemas.py (Circuit Breaker)**: Un mecanismo de seguridad diseñado para evitar que datos corruptos "ensucien" la Capa Silver.
- **Lógica de Cortafuegos**:
  - Registros con DNI inválido o nombres críticos nulos se desvían automáticamente a la carpeta de rechazados.
  - Clasifica el motivo de fallo para reporte.
  - Si el porcentaje de registros inválidos supera el umbral definido (20%), se activa el **Circuit Breaker** y se detiene la ejecución para proteger la calidad del pipeline Gold.

### 4. DATASETS (src/datasets/)

- **Responsabilidad**: Gestión de la estructura final y cargadores de datos específicos.
- **Funcionalidad**: Repositorio de modelos y esquemas que definen la salida final hacia el Backend, asegurando que los contratos de datos se cumplan.

### 5. ANALYTICS (src/analytics/)

- **Responsabilidad**: Generación de conocimiento derivado y enriquecimiento de la Capa Gold.
- **Métricas operativas**: `risk_engine.py` calcula índices de riesgo financiero (MAD), legal y estabilidad partidaria.
- **Enriquecimiento**: Orquestación del Join entre candidatos y sus respectivos Planes de Gobierno para generar el `search_context` vectorial.

### 6. ENTITY RESOLUTION (src/entity_resolution/)

- **Responsabilidad**: Motor de búsqueda semántica y vinculación de identidades.
- **Búsqueda Semántica (`vector_store.py`)**: Implementación local (sin APIs externas) para indexar planes de gobierno:
  - **Offline**: Generación de embeddings con `sentence-transformers` y almacenamiento en índices FAISS (`IndexFlatIP`).
  - **Online**: Clase `SemanticSearch` con patrón **Singleton** para búsquedas de alta performance en español peruano.

### 7. MODELS (src/models/)

- **Propósito**: Definición de las entidades de negocio. Es el lenguaje común del proyecto, utilizando clases de datos (DataClasses/Pydantic) para asegurar tipado fuerte en todo el flujo.

### 8. UTILS (src/utils/)

Este directorio centraliza las funciones de apoyo transversales que no pertenecen a la lógica de negocio.

- **logger.py**: Configuración centralizada de logs para el pipeline, permitiendo rastrear el progreso de cada lote de procesamiento.
- **database.py**: Herramientas de conexión y gestión de persistencia SQL operando sobre la capa Gold.

## MEJORES PRÁCTICAS Y ESTÁNDARES

- **Desacoplamiento**: Los módulos de limpieza (`cleaners`) no dependen del orquestador, lo que permite probarlos de forma aislada.
- **Comentarios en Español**: Todo el código está documentado siguiendo el estándar de las instrucciones del proyecto para facilitar la colaboración.
- **Evaluación Perezosa**: Se prioriza `LazyFrame` de Polars sobre `DataFrame` en memoria para el procesamiento de miles de archivos concurrentemente.
- **Idempotencia**: Todas las funciones de generación de identidad son puras, asegurando el mismo resultado ante la misma entrada sin importar el número de ejecuciones.
