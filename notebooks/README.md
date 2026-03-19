# ANALISIS EXPLORATORIO - NOTEBOOKS/

## VISION GENERAL
El directorio `notebooks/` es el espacio de experimentacion para este proyecto de Data Science. Aqui se prototipan scrapers, se analizan correlaciones y se visualizan los datos por primera vez antes de ser incorporados al pipeline productivo en `src/`.

## CONTENIDO ESPERADO

### 1. EXPLORACION INICIAL (01_exploracion_inicial.ipynb)
- Analisis de nulos en las fuentes originales.
- Estudio de la distribucion de candidatos por regiones y partidos.
- Graficos temporales de actividad legislativa.

### 2. PROTOTIPADO DE SCRAPERS (02_prototipo_scraper.ipynb)
- Pruebas de librerias de scraping (BeautifulSoup, Requests).
- Manejo de paginacion y selectores CSS/XPath temporales.
- Pruebas de limpieza de texto sucio (reglas regex).

### 3. MODELADO DE ENTIDADES (03_prototipo_matching.ipynb)
- Experimentos con algoritmos de semejanza de texto.
- Tuning de umbrales para el Fuzzy Matching de identidades.
- Evaluacion de precision (falsos positivos/negativos en el matching).

## REGLAS DE ORO
- **No para produccion**: Ningun notebook debe ser necesario para que el pipeline de `src/` funcione.
- **Limpieza**: Los notebooks deben subirse limpios de salidas (Clear Outputs) o con salidas muy especificas que justifiquen su versionado.
- **Nomenclatura**: Enumerar los notebooks (01_, 02_, ...) para indicar el flujo logico de la investigacion.
