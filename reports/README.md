# REPORTES Y RESULTADOS - REPORTS/

## VISION GENERAL
El directorio `reports/` centraliza los hallazgos y el estado de salud de la plataforma de datos. Aqui se guardan tanto analisis politicos como reportes tecnicos de calidad de los procesos de scraping.

## TIPOS DE REPORTES

### 1. CALIDAD DE DATOS (Data Quality Reports)
- **Frecuencia**: Al final de cada corrida del pipeline (ej. diario/semanal).
- **Contenido**: Deteccion de anomalias, porcentaje de completitud por fuente y fallos en la resolucion de identidades.
- **Formato**: Archivos HTML (generados por herramientas como Great Expectations) o graficos PNG.

### 2. ANALISIS POLITICO (Analytics Reports)
- **Frecuencia**: Generados manualmente o por campania electoral.
- **Contenido**: Mapas de calor de candidatos por regiones, graficos de asistencia legislativa y rankings de productividad.
- **Formato**: PDF resumidos o dashboards estaticos para visualizacion en el `frontend/`.

### 3. ESTADO DEL SCRAPING (Scraping Status)
- **Frecuencia**: Tiempo real o diario.
- **Contenido**: Log de paginas bloqueadas, tiempos de respuesta de las fuentes oficiales de Peru y volumen de registros nuevos.
- **Formato**: Logs estructurados o dashboards de monitoreo basico.

## GENERACION DE REPORTES
Se promueve el uso de librerias como `ydata-profiling` o similares para generar reportes automaticos a partir de los datasets de la capa `curated/`.
