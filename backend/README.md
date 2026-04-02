# SERVIDOR DE DATOS - BACKEND/

## VISION GENERAL

El directorio `backend/` expone la inteligencia de datos generada en el pipeline a traves de una API REST. Esta capa permite que aplicaciones de terceros, periodistas o ciudadanos consuman la informacion curada de forma sencilla y eficiente.

## ARQUITECTURA DEL SERVIDOR

- **Tecnologia**: FastAPI con alto rendimiento y generacion automatica de documentacion (Swagger/OpenAPI).
- **Persistencia**: Lectura directa de archivos Parquet de la Capa Gold (`data/curated/`). No se utiliza base de datos relacional en esta fase.
- **Cache**: In-memory con `cachetools.TTLCache`. Respuestas cacheadas por clave de endpoint + parametros, con invalidacion automatica cuando cambian los datos.
- **ETags**: Hash SHA-256 del archivo Gold como ETag. Soporte para `If-None-Match` con respuesta `304 Not Modified`.
- **Paginacion**: Offset/Limit sobre slices de Polars para latencias menores a 100ms.

## ESTRUCTURA INTERNA

```
backend/src/
├── main.py                  # entrypoint FastAPI con lifespan
├── api/
│   ├── candidates.py        # endpoints de candidatos (listado y detalle)
│   └── health.py            # health check avanzado
├── config/
│   ├── settings.py          # configuracion centralizada (pydantic-settings)
│   └── cache.py             # cache in-memory y gestion de ETags
├── repositories/
│   └── parquet_repository.py    # lectura y hash del Parquet Gold
├── schemas/
│   └── candidates.py        # modelos Pydantic de respuesta
└── services/
    └── candidate_service.py # logica de negocio y transformacion
```

## ENDPOINTS

| Metodo | Ruta                        | Descripcion                                           |
| ------ | --------------------------- | ----------------------------------------------------- |
| `GET`  | `/v1/candidatos`            | Listado paginado con filtros `limit` y `offset`       |
| `GET`  | `/v1/candidato/{global_id}` | Ficha tecnica detallada por UUID v5                   |
| `GET`  | `/health`                   | Estado de salud del sistema (archivos, memoria, ETag) |
| `POST` | `/v1/admin/reload`          | Recarga del dataset sin reiniciar el servidor         |

## CONFIGURACION

Todas las rutas y parametros se cargan via variables de entorno con prefijo `API_`:

| Variable                       | Descripcion                           | Default                                     |
| ------------------------------ | ------------------------------------- | ------------------------------------------- |
| `API_SILVER_PATH`              | Ruta al Parquet Silver                | `data/normalized/candidatos_silver.parquet` |
| `API_GOLD_PATH`                | Ruta al Parquet Gold                  | `data/curated/candidates_gold.parquet`      |
| `API_CACHE_TTL_SECONDS`        | Tiempo de vida del cache (segundos)   | `300`                                       |
| `API_CACHE_MAX_SIZE`           | Entradas maximas en cache             | `256`                                       |
| `API_PAGINATION_DEFAULT_LIMIT` | Registros por pagina por defecto      | `20`                                        |
| `API_PAGINATION_MAX_LIMIT`     | Limite maximo de registros por pagina | `100`                                       |

## COMO CORRER EL BACKEND (MODO DESARROLLO)

1. Instalar dependencias con `poetry install`.
2. Ejecutar `uvicorn backend.src.main:app --reload` desde la raiz del proyecto.
3. Acceder a `/docs` para ver la documentacion interactiva de Swagger.

## SISTEMA DE AUDITORIA (DATA LINEAGE)

El pipeline de auditoria (`src/utils/audit.py`) registra automaticamente los cambios detectados entre ejecuciones del pipeline:

- Se ejecuta tanto en la capa Silver (orchestrator) como en la capa Gold (risk engine).
- Cada cambio se registra en `data/curated/audit_log.parquet` con: `global_id`, `field_changed`, `old_value`, `new_value`, `timestamp`.
- La deteccion es 100% vectorizada con Polars (sin loops Python).
- Permite rastrear la evolucion historica de cualquier registro del sistema.
