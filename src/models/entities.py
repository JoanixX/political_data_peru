from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class PartidoPolitico:
    # entidad que representa un partido politico en peru
    id_partido: str
    nombre: str
    siglas: str
    estado: str  # ejemplo: inscrito, cancelado
    fecha_inscripcion: Optional[datetime] = None

@dataclass
class Candidato:
    # representa a un candidato presidencial o congresal
    dni: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str
    id_partido: str
    cargo_postulacion: str
    periodo: int
    antecedentes_penales: bool = False
    metadata: dict = field(default_factory=dict) # para guardar info extra de la fuente

@dataclass
class ProyectoLey:
    # representa una iniciativa legislativa en el congreso
    numero_ley: str
    titulo: str
    fec_presentacion: datetime
    autor_principal_dni: str
    estado_tramite: str
    url_documento: Optional[str] = None

@dataclass
class FuenteDato:
    # trazabilidad del origen de la informacion
    nombre_fuente: str
    fecha_extraccion: datetime
    url_origen: str
    version_scrapper: str