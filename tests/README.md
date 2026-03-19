# ESTRATEGIA DE PRUEBAS - TESTS/

## VISION GENERAL
El directorio `tests/` es el guardian de la integridad y confiabilidad de este proyecto de Data Science. Sigue una aproximacion de piramide de pruebas para asegurar que tanto la logica de scraping como el procesamiento de datos funcionan segun lo esperado.

## CATEGORIAS DE PRUEBAS

### 1. PRUEBAS UNITARIAS (src/tests_unitarios/)
- **Objetivo**: Probar funciones individuales de limpieza y normalizacion de texto (regex de nombres, conversion de fechas).
- **Herramienta**: Pytest.
- **Ubicacion**: Pruebas de bajo nivel que no requieren conexion a internet o bases de datos.

### 2. PRUEBAS DE INTEGRACION (tests/integration/)
- **Objetivo**: Validar el flujo entre capas (ej. de Raw a Staging).
- **Herramienta**: Pytest con mocks de las respuestas de las fuentes oficiales de Peru.
- **Alcance**: Verifica que el pipeline puede procesar un registro completo desde la ingesta hasta la capa de curacion.

### 3. PRUEBAS DE CALIDAD DE DATOS (tests/data_quality/)
- **Objetivo**: Verificar que los datos de salida cumplen con los contratos de calidad.
- **Herramienta**: Validador de esquemas (Pydantic / Great Expectations).
- **Reglas**: No permitir nulos en el DNI del candidato, fechas en el futuro, o partidos politicos inexistentes.

### 4. PRUEBAS DE API (backend/tests/)
- **Objetivo**: Asegurar que los endpoints del `backend/` devuelven la informacion correcta en el formato esperado (JSON).
- **Herramienta**: HTTPX / TestClient de FastAPI.

## EJECUCION DE LOS TESTS
1. Instalar dependencias de desarrollo (`pip install -e .[dev]`).
2. Ejecutar `pytest` desde el directorio raiz para correr todas las pruebas.
3. El reporte de cobertura (coverage) se generara en la carpeta `htmlcov/` (ver .gitignore).

## FILOSOFIA DE TESTING
- **No datos reales**: Los tests deben usar "Mock Data" (datos falsos controlados) para evitar depender de si la web oficial del estado peruano esta caida o no durante el CI/CD.
- **Automatizacion**: Ningun cambio en el codigo del pipeline debe subirse a `main` sin pasar antes todos los tests de calidad.
