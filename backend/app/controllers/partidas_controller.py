
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..utils.conexion_db import get_db
from ..models.tablas import Partida, PartidaDetalle, Cuenta
from ..schemas import PartidaCreate, PartidaOut, PartidaDetalleCreate

router = APIRouter(prefix="/partidas", tags=["partidas"])

@router.get("/", response_model=list[PartidaOut])
def listar_partidas(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    partidas = db.query(Partida).offset(skip).limit(limit).all()
    result = []
    for p in partidas:
        detalles = db.query(PartidaDetalle).filter(PartidaDetalle.id_partida == p.id_partida).all()
        detalles_out = [PartidaDetalleCreate(id_cuenta=d.id_cuenta, debe=float(d.debe or 0), haber=float(d.haber or 0), descripcion=d.descripcion) for d in detalles]
        result.append(PartidaOut(id_partida=p.id_partida, fecha=p.fecha, descripcion=p.descripcion, tipo=p.tipo, detalles=detalles_out))
    return result

@router.post("/", response_model=PartidaOut)
def crear_partida(data: PartidaCreate, db: Session = Depends(get_db)):
    p = Partida(fecha=data.fecha, descripcion=data.descripcion, tipo=data.tipo)
    db.add(p); db.commit(); db.refresh(p)
    detalles_objs = []
    for d in data.detalles:
        # validate cuenta exists
        cuenta = db.query(Cuenta).filter(Cuenta.id_cuenta == d.id_cuenta).first()
        if not cuenta:
            raise HTTPException(status_code=400, detail=f"Cuenta {d.id_cuenta} no existe")
        det = PartidaDetalle(id_partida=p.id_partida, id_cuenta=d.id_cuenta, debe=d.debe or 0, haber=d.haber or 0, descripcion=d.descripcion)
        db.add(det); detalles_objs.append(det)
    db.commit()
    detalles = db.query(PartidaDetalle).filter(PartidaDetalle.id_partida == p.id_partida).all()
    detalles_out = [PartidaDetalleCreate(id_cuenta=d.id_cuenta, debe=float(d.debe or 0), haber=float(d.haber or 0), descripcion=d.descripcion) for d in detalles]
    return PartidaOut(id_partida=p.id_partida, fecha=p.fecha, descripcion=p.descripcion, tipo=p.tipo, detalles=detalles_out)

@router.get("/{id}", response_model=PartidaOut)
def ver_partida(id: int, db: Session = Depends(get_db)):
    p = db.query(Partida).filter(Partida.id_partida == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    detalles = db.query(PartidaDetalle).filter(PartidaDetalle.id_partida == p.id_partida).all()
    detalles_out = [PartidaDetalleCreate(id_cuenta=d.id_cuenta, debe=float(d.debe or 0), haber=float(d.haber or 0), descripcion=d.descripcion) for d in detalles]
    return PartidaOut(id_partida=p.id_partida, fecha=p.fecha, descripcion=p.descripcion, tipo=p.tipo, detalles=detalles_out)
