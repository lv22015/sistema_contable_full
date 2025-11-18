from typing import  List
from datetime import date


from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ---------USUARIOS--------
class UsuarioCreate(BaseModel):
    username: str
    password: str
    nombre_completo: Optional[str] = None
    rol: Optional[str] = None

class UsuarioResponse(BaseModel):
    id_usuario: int
    username: str
    nombre_completo: Optional[str] = None
    rol: Optional[str] = None
    activo: bool

    class Config:
        from_attributes = True

# ---------LOGIN----------
class LoginRequest(BaseModel):
    username: str
    password: str


# ----------------- CUENTAS -----------------
class CuentaBase(BaseModel):
    codigo: str
    nombre: str
    tipo: str
    nivel: Optional[int] = 1
    cuenta_padre: Optional[str] = None  # Mostrará el nombre del padre, no el ID


class CuentaCreate(CuentaBase):
    pass


class CuentaOut(CuentaBase):
    id_cuenta: int
    fecha_creacion: Optional[datetime] = None

    class Config:
        orm_mode = True


# ----------------- PARTIDAS -----------------
class PartidaDetalleCreate(BaseModel):
    id_cuenta: int
    debe: float = 0.0
    haber: float = 0.0
    descripcion: Optional[str] = None


class PartidaCreate(BaseModel):
    fecha: Optional[date] = None
    descripcion: str
    tipo: Optional[str] = 'DIARIO'
    detalles: List[PartidaDetalleCreate]


class PartidaOut(BaseModel):
    id_partida: int
    fecha: Optional[date] = None
    descripcion: str
    tipo: str
    detalles: List[PartidaDetalleCreate]

    class Config:
        orm_mode = True


# ----------------- MANUAL DE CUENTAS -----------------

class ManualCuentaCreate(BaseModel):
    id_cuenta: int
    descripcion: str
    ejemplos: Optional[str] = None
    id_usuario_crea: Optional[int] = None


class ManualCuentaOut(BaseModel):
    id_manual: int
    id_cuenta: int
    cuenta_nombre: Optional[str] = None
    descripcion: str
    ejemplos: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    id_usuario_crea: Optional[int] = None

    class Config:
        orm_mode = True
