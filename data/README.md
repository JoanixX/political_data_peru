# ESTRUCTURA DE DATOS (DATA LAKE) - CAPAS MEDALLION

## VISION GENERAL
El directorio `data/` implementa una arquitectura de capas diseñada para el procesamiento masivo de datos políticos peruanos. Siguiendo el modelo **Medallion**, aseguramos que cada transformación sea rastreable, reproducible y auditable.

## DETALLE DE CAPAS Y RESPONSABILIDADES

### 1. RAW (data/raw/) - Capa Bronze
- **Propósito**: Persistencia inmutable del dato original.
- **Estructura**: Organizado por categorías (`presidentes`, `senadores`, `parlamento_andino`, `diputados`).
- **Contenido**: Archivos JSON individuales tal cual se descargan del Jurado Nacional de Elecciones (JNE) y otras fuentes.
- **Regla de integridad**: Prohibido modificar archivos en esta capa. Es la única fuente de verdad para reconstruir el Data Lake desde cero.

### 2. STAGING (data/staging/)
- **Propósito**: Almacenamiento intermedio de transición.
- **Proceso**: Conversión de formatos heterogéneos a estructuras de datos operativas. Se utiliza para limpiezas de ruido inicial (espacios extra, carácteres de control) antes de la normalización de esquemas.

### 3. NORMALIZED (data/normalized/) - Capa Silver
- **Propósito**: Refinamiento, tipado y estandarización cross-dataset.
- **Tecnología**: Archivos unificados en formato **Parquet** con compresión **ZSTD** para optimizar el espacio en disco sin sacrificar velocidad de lectura.
- **Procesos Críticos**:
    - **Limpieza Financiera**: Conversión de montos (`S/ 1,200.00`, `$500`) a valores de punto flotante de 64 bits.
    - **Normalización de Identidad**: Padding de DNI a 8 dígitos y corrección de formatos numéricos.
    - **Global ID Engine**: Asignación de un UUID v5 persistente basado en DNI o Nombre/Fecha de nacimiento, garantizando que un político tenga el mismo ID en todas las fuentes.
- **Destino Final**: `candidatos_silver.parquet`.

### 4. REJECTED (data/rejected/)
- **Propósito**: Almacenamiento de fallos de calidad (Audit Log).
- **Contenido**: `failed_records.parquet`.
- **Funcionamiento**: Cuando el **Circuit Breaker** detecta un registro que no cumple los mínimos (DNI mal formado, nombres nulos, etc.), lo desvía aquí con una columna extra `motivo_rechazo`. Permite analizar por qué se está perdiendo la integridad sin detener el pipeline masivo.

### 5. MATCHING (data/matched/)
- **Propósito**: Resolución de identidades complejas.
- **Contenido**: Mapeos de resolución de entidades donde múltiples variantes de un nombre se unifican bajo el Global ID generado en la capa Silver.

### 6. CURATED (data/curated/) - Capa Gold
- **Propósito**: Analítica avanzada y consumo de API.
- **Contenido**: Tablas finales agregadas, enriquecidas con métricas de performance política, historial de partidos y vinculaciones. Es la capa que consume directamente el Backend.

### 7. EXPORTS (data/exports/)
- **Propósito**: Interoperabilidad y transparencia.
- **Formato**: CSV y Excel para analistas de datos, periodistas y ciudadanos que no usan el pipeline de Python.

## CONSIDERACIONES DE ALMACENAMIENTO
- **Parquet**: Se utiliza exclusivamente en las capas Silver y Gold por su soporte nativo en motores de Big Data y su eficiencia columnar.
- **ZSTD**: Algoritmo de compresión seleccionado para equilibrar el ratio de compresión (4x respecto a CSV) y la velocidad de descompresión en CPUs modernas.
- **Exclusión**: Todos los directorios de datos están excluidos del control de versiones (`.gitignore`) para evitar el seguimiento de archivos binarios masivos y proteger datos sensibles locales.
