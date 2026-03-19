# DASHBOARD DE VALIDACION - FRONTEND/

## VISION GENERAL
El directorio `frontend/` contiene una aplicación web ligera diseñada para la validacion visual y consulta rápida de los hallazgos del pipeline. Su objetivo no es ser una plataforma comercial compleja, sino una herramienta de "Smoke Test" y presentacion de datos.

## FUNCIONALIDADES
- **Visualizador de Candidatos**: Listado de identidades politicas unificadas con sus antecedentes.
- **Buscador de Proyectos de Ley**: Filtro por palabra clave y autor.
- **Seccion de Calidad**: Graficos que muestran el estado de salud de la data (porcentaje de completitud, errores de matching).

## STACK TECNICO (PROPUESTO)
- **Framework**: Next.js o React para reactividad rapida.
- **Estilos**: Tailwind CSS para un diseño moderno y premium.
- **Consumo**: Conexion directa a la API del `backend/`.

## ESTRUCTURA
- `src/components`: UI components reutilizables (Tablas, Cards, Gráficos).
- `src/pages`: Rutas principales de la aplicación.
- `public/`: Activos estaticos y logos institucionales.

## DESPLIEGUE
Preparado para ser desplegado en Vercel o Netlify de forma independiente, conectándose al backend productivo.
