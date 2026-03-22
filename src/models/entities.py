from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

# Modelos para ingesta directa basados en el link de HVConsolidado
class JNEExperienciaLaboral(BaseModel):
    centro_trabajo: Optional[str] = Field(None, alias="strCentroTrabajo")
    ocupacion: Optional[str] = Field(None, alias="strOcupacionProfesion")
    anio_desde: Optional[str] = Field(None, alias="strAnioTrabajoDesde")
    anio_hasta: Optional[str] = Field(None, alias="strAnioTrabajoHasta")
    ubigeo: Optional[str] = Field(None, alias="strUbigeoTrabajo")
    departamento: Optional[str] = Field(None, alias="strTrabajoDepartamento")

class JNEEducacionUniversitaria(BaseModel):
    universidad: Optional[str] = Field(None, alias="strUniversidad")
    carrera: Optional[str] = Field(None, alias="strCarreraUni")
    concluido: Optional[str] = Field(None, alias="strConcluidoEduUni")
    anio_bachiller: Optional[str] = Field(None, alias="strAnioBachiller")
    anio_titulo: Optional[str] = Field(None, alias="strAnioTitulo")

class JNEIngresos(BaseModel):
    anio: Optional[str] = Field(None, alias="strAnioIngresos")
    remu_publico: float = Field(0.0, alias="decRemuBrutaPublico")
    remu_privado: float = Field(0.0, alias="decRemuBrutaPrivado")
    renta_publico: float = Field(0.0, alias="decRentaIndividualPublico")
    renta_privado: float = Field(0.0, alias="decRentaIndividualPrivado")
    otro_publico: float = Field(0.0, alias="decOtroIngresoPublico")
    otro_privado: float = Field(0.0, alias="decOtroIngresoPrivado")

class JNEBienInmueble(BaseModel):
    tipo: Optional[str] = Field(None, alias="strTipoBienInmueble")
    direccion: Optional[str] = Field(None, alias="strInmuebleDireccion")
    valor: float = Field(0.0, alias="decValor")
    autovaluo: float = Field(0.0, alias="decAutovaluo")

class JNEBienMueble(BaseModel):
    tipo: Optional[str] = Field(None, alias="strVehiculo")
    placa: Optional[str] = Field(None, alias="strPlaca")
    valor: float = Field(0.0, alias="decValor")

class JNETitularidad(BaseModel):
    empresa: Optional[str] = Field(None, alias="strPersonaJuridica")
    tipo: Optional[str] = Field(None, alias="strTipoTitularidad")
    cantidad: float = Field(0.0, alias="decCantidad")
    valor: float = Field(0.0, alias="decValor")

class JNEDatosPersonales(BaseModel):
    id_hoja_vida: int = Field(..., alias="idHojaVida")
    dni: str = Field(..., alias="strDocumentoIdentidad")
    apellido_paterno: str = Field(..., alias="strApellidoPaterno")
    apellido_materno: str = Field(..., alias="strApellidoMaterno")
    nombres: str = Field(..., alias="strNombres")
    fecha_nacimiento: Optional[str] = Field(None, alias="strFechaNacimiento")
    partido: str = Field(..., alias="strOrganizacionPolitica")
    cargo_postula: Optional[str] = Field(None, alias="strCargoEleccion")

class JNEHojaVidaConsolidada(BaseModel):
    datos_personales: JNEDatosPersonales = Field(..., alias="oDatosPersonales")
    experiencia_laboral: List[JNEExperienciaLaboral] = Field(default_factory=list, alias="lExperienciaLaboral")
    educacion_universitaria: List[JNEEducacionUniversitaria] = Field(default_factory=list, alias="lEduUniversitaria")
    ingresos: Optional[JNEIngresos] = Field(None, alias="oIngresos")
    bienes_inmuebles: List[JNEBienInmueble] = Field(default_factory=list, alias="lBienInmueble")
    bienes_muebles: List[JNEBienMueble] = Field(default_factory=list, alias="lBienMueble")
    titularidades: List[JNETitularidad] = Field(default_factory=list, alias="lTitularidad")

class JNEResponse(BaseModel):
    success: bool
    data: Optional[JNEHojaVidaConsolidada] = None
    message: Optional[str] = None

# Ahora están los modelos limpios para el dominio
class PartidoPolitico(BaseModel):
    id_partido: str
    nombre: str
    siglas: Optional[str] = None
    estado: str
    fecha_inscripcion: Optional[datetime] = None

class Candidato(BaseModel):
    id_hoja_vida: int
    dni: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str
    partido: str
    cargo_postulacion: str
    total_ingresos: float = 0.0
    num_propiedades: int = 0
    tiene_antecedentes: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

# NOTA IMPORTANTE
# Si faltara informacion relevante en alguna seccion y fuera bastante
# importante, o sea campos con info vacía por ejemplo o contradicciones, se
# debe gatillar una llamada al link 2 (el de hojavida?idHojaVida=) para
# obtener el detalle expandido y verificar si se puede corregir la info.