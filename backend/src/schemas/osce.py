from pydantic import BaseModel, Field

class OsceSanctionRecord(BaseModel):
    ruc: str
    nombre_empresa: str | None = None
    tipo_sancion: str | None = None
    fecha_inicio: str | None = None
    fecha_fin: str | None = None
    motivo: str | None = None
    monto: float | None = None
    numero_resolucion: str | None = None

class OsceCompanyResponse(BaseModel):
    ruc: str
    fup_url: str = Field(description="Hipervínculo a la Ficha Única del Proveedor (OSCE)")
    nombre_empresa: str | None = None
    total_sanciones: int = 0
    sanciones: list[OsceSanctionRecord] = Field(default_factory=list)
    en_penalidades: bool = False
    total_penalidades: int = 0
    en_consorcios: bool = False
    total_consorcios: int = 0