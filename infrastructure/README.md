# INFRAESTRUCTURA Y DESPLIEGUE - INFRASTRUCTURE/

## VISION GENERAL
El directorio `infrastructure/` centraliza todo lo necesario para que el proyecto sea ejecutable, reproducible y escalable en entornos de produccion y desarrollo.

## COMPONENTES CLAVE

### 1. DOCKER Y ORQUESTACION
- **Docker Compose**: Define el entorno multi-contenedor que incluye el scraper (Python), la base de datos (PostgreSQL) y el backend para servir la data.
- **Dockerfiles**: Configuraciones especificas para cada servicio, asegurando que las dependencias de sistema (ej. drivers para scraping) sean identicas en cualquier maquina.

### 2. CONFIGURACION DE ENTORNOS
- **Variables de Entorno (.env)**: Manejo centralizado de secretos, tokens de APIs gubernamentales, credenciales de base de datos y puertos de exposicion.
- **Entornos**: Base preparada para despliegue en AWS (EC2/RDS) o plataformas PaaS como Render/Vercel.

### 3. PERSISTENCIA
- **PostgreSQL**: Base de datos relacional para el almacenamiento de identidades politicas y trazabilidad.
- **Volumenes**: Gestion de almacenamiento persistente para las capas de datos locales de la carpeta `data/`.

## PASOS PARA EL DESPLIEGUE LOCAL
1. Clonar el repositorio.
2. Configurar el archivo `.env` basado en `.env.example`.
3. Ejecutar `docker-compose up --build`.

## ESCALABILIDAD FUTURA
- Soporte para Amazon S3 como almacenamiento de los archivos Parquet de la capa Gold.
- Configuracion de CI/CD para despliegue automatico tras pasar pruebas de calidad de datos.
