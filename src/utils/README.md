# Utilidades Globales - src/utils/

Este directorio centraliza las funciones de apoyo que no pertenecen a la lógica de negocio pero son necesarias para la operación técnica.

## Contenido

- `logger.py`: Configuración centralizada de logs para el pipeline.
- `database.py`: Conectores y manejo de sesiones con SQLAlchemy.
- `helpers.py`: Funciones genéricas de manipulación de strings y fechas.

## Uso del Logger

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("iniciando proceso de ingesta...")
```
