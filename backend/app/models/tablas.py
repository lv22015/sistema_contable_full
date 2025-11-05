from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from ..utils.conexion_db import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    nombre_completo = Column(String(100))
    rol = Column(String(50))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, server_default=func.now())


class Cuenta(Base):
    __tablename__ = "cuentas"
    id_cuenta = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(20))
    nivel = Column(Integer, default=1)
    cuenta_padre = Column(Integer, ForeignKey('cuentas.id_cuenta'), nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    id_usuario_crea = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=True)


class Partida(Base):
    __tablename__ = "partidas"
    id_partida = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo = Column(String(20), default='DIARIO')
    id_usuario_crea = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())


class PartidaDetalle(Base):
    __tablename__ = "partida_detalle"
    id_detalle = Column(Integer, primary_key=True, index=True)
    id_partida = Column(Integer, ForeignKey('partidas.id_partida', ondelete='CASCADE'), nullable=False)
    id_cuenta = Column(Integer, ForeignKey('cuentas.id_cuenta'), nullable=False)
    debe = Column(Numeric(12, 2), default=0)
    haber = Column(Numeric(12, 2), default=0)
    descripcion = Column(Text)
