# Procedimiento de Actualización de Datos OSCE/CONOSCE

## Contexto

Los datos de sanciones, penalidades, inhabilitaciones, conformación jurídica y consorcios provienen del portal oficial **CONOSCE** del Organismo Supervisor de las Contrataciones del Estado (OSCE).

Estos archivos se actualizan manualmente debido a la inestabilidad confirmada de las URLs de datos abiertos (la URL `https://www.datosabiertos.gob.pe/sites/default/files/Empresas_Sancionadas_OSCE.csv` retorna HTTP 404 desde al menos marzo 2026).

## Fuentes y Descarga

### Portal CONOSCE
**URL**: https://portal.osce.gob.pe/conosce/

Desde este portal se descargan los siguientes datasets:

| Archivo | Sección en CONOSCE | Formato | Frecuencia sugerida |
|---|---|---|---|
| `sancionados.csv` | Proveedores Sancionados > Inhabilitados | CSV (delimitador `\|`) | Mensual |
| `sancionados_multa.csv` | Proveedores Sancionados > Multados | CSV (delimitador `\|`) | Mensual |
| `inhabilitaciones_judiciales.csv` | Inhabilitaciones Judiciales | CSV (delimitador `\|`) | Trimestral |
| `penalidades.csv` | Penalidades | CSV (delimitador `\|`) | Mensual |
| `conformacion_juridica.csv` | Conformación Jurídica | CSV (delimitador `\|`) | Semestral |
| `CONOSCE_CONSORCIO{AÑO}_0.xlsx` | Consorcios | XLSX | Anual |

### Pasos de Descarga

1. Acceder a https://portal.osce.gob.pe/conosce/
2. Navegar a la sección correspondiente
3. Descargar el archivo en el formato indicado
4. **No renombrar** los archivos (el pipeline espera nombres exactos)
5. Colocar los archivos en: `data/raw/osce/`

## Ejecución Post-Actualización

Después de actualizar cualquier archivo en `data/raw/osce/`, ejecutar:

```bash
# Regenera los Parquets de staging
python -m src.ingestion.osce_scraper

# Regenera el Gold con los nuevos datos OSCE
python -m src.analytics.risk_engine
```

O bien ejecutar el pipeline completo:

```bash
python -m src.main
```

## Verificación

Tras la ejecución, verificar que los siguientes archivos se hayan generado/actualizado en `data/staging/`:

- `osce_sanctions_registry.parquet` — Registro unificado de sanciones
- `osce_ruc_bridge.parquet` — Tabla puente DNI↔RUC
- `osce_consorcios.parquet` — Miembros de consorcios
- `osce_penalidades.parquet` — Penalidades contractuales

## Consideraciones

- **conformacion_juridica.csv** pesa ~217 MB. No se commitea a Git (está en `.gitignore`). Se procesa con evaluación perezosa (`pl.scan_csv`) para mantener el consumo de RAM controlado.
- Los archivos XLSX de consorcios se publican por año. Al descargar un nuevo año, simplemente añadir el archivo a `data/raw/osce/` sin eliminar los anteriores. El pipeline los concatena automáticamente.
- El campo `FECHA_CORTE` en los CSV indica la fecha de corte de la información. Úsalo para verificar la frescura de los datos.
