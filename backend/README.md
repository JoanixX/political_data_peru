# SERVIDOR DE DATOS - BACKEND/

## VISION GENERAL
El directorio `backend/` expone la inteligencia de datos generada en el pipeline a traves de una API REST. Esta capa es la que permite que aplicaciones de terceros, periodistas o ciudadanos consuman la informacion curada de forma sencilla.

## ARQUITECTURA DEL SERVIDOR
- **Tecnologia**: FastAPI (propuesto) por su alto rendimiento y generacion automatica de documentacion (Swagger/OpenAPI).
- **Controladores**: Endpoints especificos para listar candidatos, ver perfiles detallados, consultar historial legislativo y filtrar por partidos.
- **Validacion de Datos**: Uso profuso de tipado estatico para garantizar que lo que sale de la base de datos es exactamente lo que el cliente espera.

## ENDPOINTS CLAVE (PROPUESTA)
- `GET /v1/candidatos`: Listado completo con filtros de eleccion y partido.
- `GET /v1/candidato/{id}`: Ficha tecnica detallada de un unico actor politico.
- `GET /v1/legislation`: Seguimiento de proyectos de ley y votaciones.
- `GET /v1/analytics/rankings`: Indices derivados del pipeline de analitica.

## PRUEBAS Y CALIDAD
- **tests/**: Pruebas unitarias de los endpoints, garantizando que los contratos de datos se respetan siempre.
- **Dockerfile**: Empaquetado optimizado para el despliegue del servidor independientemente del resto del pipeline.

## COMO CORRER EL BACKEND (MODO DESARROLLO)
1. Instalar dependencias mediante `pip install -r requirements.txt`.
2. Ejecutar `uvicorn src.main:app --reload`.
3. Acceder a `/docs` para ver la documentacion interactiva.
