from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# ----------------- USUARIOS -----------------
class UsuarioBase(BaseModel):
    username: str
    nombre_completo: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = True


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioOut(UsuarioBase):
    id_usuario: int
    fecha_creacion: Optional[datetime] = None

    class Config:
        orm_mode = True


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
