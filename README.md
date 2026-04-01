# POLITICAL DATA PERU: INTELIGENCIA Y ANALITICA DE DATOS PUBLICOS

Plataforma dedicada al seguimiento, normalización y análisis de información sobre senadores y candidatos presidenciales en Perú.

## VISION GENERAL

Este proyecto se me ocurrió porque de alguna manera quisiera ayudar en el combate contra fake news o bots que aparecen en redes sociales. Mediante un pipeline avanzado de inteligencia de datos, centralicé y junté info proveniente del Jurado Nacional de Elecciones (JNE), el Congreso de la Republica y portales de transparencia gubernamental. Es un proyecto open source, así que están habilitadas cosas como los PRs para poder mejorar el proyecto, después de todo hay algunas cosas que aún no domino, esto es en parte para aprender ciencia de datos mientras lo aplico a un contexto real y me va a servir.

Es más que todo un ecosistema analítico capaz de vincular identidades de múltiples fuentes para construir una unica fuente de verdad sobre el panorama politico actual. Ahora sí doy paso a la IA para que explique mejor la arquitectura que decidí usar.

## ARQUITECTURA DEL PROYECTO

Para la arquitectura usé la modular, basado en algo como las capas de datos o Medallion Architecture, además de un sistema de procesamiento desacoplado en contenedores:

- **Ingesta:** Extraccion inmutable de fuentes oficiales.
- **Procesamiento:** Pipeline de limpieza, normalizacion y resolucion de identidades.
- **Consumo:** API REST y Dashboard de visualizacion para la toma de decisiones basada en datos.

## STACK TECNICO

- **Backend & Pipeline:** Python (Polars, FastAPI).
- **Inteligencia Artificial:** Sentence-Transformers (MiniLM-L12-v2) & FAISS para Búsqueda Semántica Local.
- **Persistencia:** PostgreSQL y Parquet (ZSTD para alta eficiencia).
- **Frontend:** Next.js / React (para los reportes).
- **Infraestructura:** Docker & Docker Compose.
- **Calidad:** Logic-Based Circuit Breaker / Pytest (validación de integridad de datos).

## ESTRUCTURA DEL REPOSITORIO

El proyecto esta organizado de forma profesional para facilitar la escalabilidad y el mantenimiento:

- `src/`: El nucleo del procesamiento y logica de negocio. [Ver mas detalles](src/README.md)
- `data/`: Estructura del Data Lake (Bronze, Silver, Gold Layers). [Ver mas detalles](data/README.md)
- `backend/`: API para la exposicion y consumo de los datos curados. [Ver mas detalles](backend/README.md)
- `frontend/`: Interfaz de usuario para validacion y visualizacion. [Ver mas detalles](frontend/README.md)
- `notebooks/`: Espacio de investigacion y analisis exploratorio (EDA). [Ver mas detalles](notebooks/README.md)
- `infrastructure/`: Configuracion de contenedores y despliegue. [Ver mas detalles](infrastructure/README.md)
- `tests/`: Estrategia integral de pruebas y calidad de datos. [Ver mas detalles](tests/README.md)
- `docs/`: Documentacion tecnica detallada y decisiones arquitectonicas.
- `reports/`: Hallazgos y reportes de calidad generados automaticamente. [Ver mas detalles](reports/README.md)

## PROCEDIMIENTO DE EJECUCIÓN

El entorno esta totalmente dockerizado para garantizar la reproducibilidad inmediata:

1. Configurar variables en `.env` (guia en `.env.example`).
2. Levantar el ecosistema completo: `docker-compose up --build`.
3. Consultar la documentacion de cada carpeta para instrucciones especificas de desarrollo.

---

_Proyecto diseñado con estándares de ingeniería de datos para garantizar la veracidad, trazabilidad y utilidad de la información política en Perú._
