# LOGICA DEL PIPELINE - DIRECTORIO SRC/

## VISION GENERAL
El directorio `src/` contiene todo el codigo fonte y la logica de procesamiento que hace funcionar este proyecto como una plataforma de Data Science. No es solo un repositorio de scripts sueltos, sino un sistema modular diseñado para ser escalable, mantenible y profesional.

## COMPONENTES DEL PIPELINE

### 1. INGESTION (src/ingestion/)
- **Proposito**: Extraer datos de fuentes oficiales gubernamentales en Peru.
- **Fuentes**: Scrapers exclusivos para el Jurado Nacional de Elecciones (JNE), Congreso de la Republica (legislacion en tiempo real) y el portal de Transparencia.
- **Funcionalidad**: Manejo de peticiones HTTP, procesamiento basico de JSON y tecnicas de web scraping (BeautifulSoup, Selenium/Playwright) de forma etica y eficiente.

### 2. STAGING (src/staging/)
- **Proposito**: Carga inicial desde la fuente cruda hacia la memoria operativa.
- **Funcionalidad**: Manejo de archivos y transformacion de datos en bruto a marcos de datos (Pandas/Polars) para su posterior limpieza masiva.

### 3. NORMALIZATION (src/normalization/)
- **Proposito**: Estandarizacion profunda de datos heterogeneos.
- **Logica**: Limpieza de nombres propio, estandarizacion de fechas ISO-8601, tipado de columnas (Enteros, Flotantes, Booleanos) y reglas de negocio transversales.

### 4. ENTITY RESOLUTION (src/entity_resolution/)
- **Proposito**: Vinculacion de identidades (Matching de entidades).
- **Justificacion**: El problema real es que un candidato puede figurar con diferentes variantes de nombre o DNI en fuentes distintas.
- **Metodologia**: Algoritmos de semejanza de cadenas (Fuzzy Matching, Levenshtein distance) para asegurar que se crea una unica identidad global por cada actor politico.

### 5. VALIDATION (src/validation/)
- **Proposito**: Garantizar la integridad de los datasets antes de su consumo final.
- **Logica**: Verificacion de esquemas (Data Quality Checks), deteccion de nulos inesperados, anomalias y validacion de rangos (ej. fechas de eleccion validas).

### 6. DATASETS (src/datasets/)
- **Proposito**: Definicion de la estructura final de los datasets que se consumiran externamente.
- **Funcionalidad**: Cargadores y manejadores de persistencia para las capas finales.

### 7. ANALYTICS (src/analytics/)
- **Proposito**: Generacion de conocimiento a partir de los datos procesados.
- **Métricas**: Calculo de indices de cambio de partido (transfuguismo), eficacia legislativa, asistencia y antecedentes.

## UTILIDADES Y CONFIGURACION
- **src/utils/**: Modulos de apoyo como loggers globales, herramientas de depuracion y conectores a bases de datos (SQLAlchemy).
- **src/config/**: Centralizacion de parametros de las fuentes, URLs oficiales y constantes del sistema para evitar hardcode.

## BUENAS PRACTICAS
- **Modularidad**: Cada paquete tiene una responsabilidad única segun el flujo (Ingesta -> Limpieza -> Validacion -> Analisis).
- **Comentarios**: Codigo autodocumentado con comentarios claros en español humano.
- **Tipado**: Uso de `pydantic` o anotaciones de tipo para robustecer el intercambio de informacion entre modulos.
