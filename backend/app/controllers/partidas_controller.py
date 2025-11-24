from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..utils.conexion_db import get_db
from ..models.tablas import Partida, PartidaDetalle, Cuenta, LibroMayorEntry
from ..schemas import PartidaCreate, PartidaOut, PartidaDetalleCreate

router = APIRouter(prefix="/partidas", tags=["partidas"])


@router.post("/", response_model=PartidaOut)
def crear_partida(data: PartidaCreate, db: Session = Depends(get_db)):
    from ..utils.libro_utils import insertar_movimiento_simple, rebuild_account_from_date

    # crear la partida principal
    p = Partida(fecha=data.fecha, descripcion=data.descripcion, tipo=data.tipo)
    db.add(p)
    db.commit()
    db.refresh(p)

    detalles_objs = []
    # mapa para trackear fecha mínima por cuenta (si se necesita rebuild)
    fechas_afectadas_por_cuenta = {}

    for d in data.detalles:
        # validar existencia de cuenta
        cuenta = db.query(Cuenta).filter(Cuenta.id_cuenta == d.id_cuenta).first()
        if not cuenta:
            raise HTTPException(status_code=400, detail=f"Cuenta {d.id_cuenta} no existe")

        det = PartidaDetalle(
            id_partida=p.id_partida,
            id_cuenta=d.id_cuenta,
            debe=d.debe or 0,
            haber=d.haber or 0,
            descripcion=d.descripcion,
        )
        db.add(det)
        detalles_objs.append(det)

        # Trackear fecha mínima por cuenta
        if d.id_cuenta not in fechas_afectadas_por_cuenta:
            fechas_afectadas_por_cuenta[d.id_cuenta] = p.fecha
        else:
            if p.fecha and p.fecha < fechas_afectadas_por_cuenta[d.id_cuenta]:
                fechas_afectadas_por_cuenta[d.id_cuenta] = p.fecha

    db.commit()

    # actualizar libro mayor de forma mínima: intentar append, o marcar para rebuild
    cuentas_necesitan_rebuild = set()
    for det in detalles_objs:
        ok = insertar_movimiento_simple(db, det.id_cuenta, p.fecha, p.id_partida, det.debe, det.haber)
        if not ok:
            cuentas_necesitan_rebuild.add(det.id_cuenta)
        else:
            db.commit()

    # reconstruir cuentas que lo necesiten (fecha anterior insertada)
    for id_cuenta in cuentas_necesitan_rebuild:
        fecha_desde = fechas_afectadas_por_cuenta.get(id_cuenta, p.fecha)
        rebuild_account_from_date(db, id_cuenta, fecha_desde)
        db.commit()

    # devolver partida creada (igual que antes)
    detalles = db.query(PartidaDetalle).filter(PartidaDetalle.id_partida == p.id_partida).all()
    detalles_out = [
        PartidaDetalleCreate(
            id_cuenta=d.id_cuenta, debe=float(d.debe or 0), haber=float(d.haber or 0), descripcion=d.descripcion
        )
        for d in detalles
    ]
    return PartidaOut(id_partida=p.id_partida, fecha=p.fecha, descripcion=p.descripcion, tipo=p.tipo, detalles=detalles_out)


@router.get("/", response_model=List[PartidaOut])
def listar_partidas(db: Session = Depends(get_db)):
    """
    Lista todas las partidas con sus detalles (usado por el frontend).
    """
    partidas = db.query(Partida).order_by(Partida.fecha.desc(), Partida.id_partida.desc()).all()
    result = []
    for p in partidas:
        detalles = db.query(PartidaDetalle).filter(PartidaDetalle.id_partida == p.id_partida).all()
        detalles_out = [
            PartidaDetalleCreate(id_cuenta=d.id_cuenta, debe=float(d.debe or 0), haber=float(d.haber or 0), descripcion=d.descripcion)
            for d in detalles
        ]
        result.append(PartidaOut(id_partida=p.id_partida, fecha=p.fecha, descripcion=p.descripcion, tipo=p.tipo, detalles=detalles_out))
    return result


@router.get("/{id}", response_model=PartidaOut)
def ver_partida(id: int, db: Session = Depends(get_db)):
    p = db.query(Partida).filter(Partida.id_partida == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    detalles = db.query(PartidaDetalle).filter(PartidaDetalle.id_partida == p.id_partida).all()
    detalles_out = [
        PartidaDetalleCreate(id_cuenta=d.id_cuenta, debe=float(d.debe or 0), haber=float(d.haber or 0), descripcion=d.descripcion)
        for d in detalles
    ]
    return PartidaOut(id_partida=p.id_partida, fecha=p.fecha, descripcion=p.descripcion, tipo=p.tipo, detalles=detalles_out)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_partida(id: int, db: Session = Depends(get_db)):
    """
    Elimina una partida: borra entradas del libro mayor asociadas y la partida.
    Devuelve 204 No Content si se borró.
    """
    p = db.query(Partida).filter(Partida.id_partida == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    # Borrar entradas del libro mayor vinculadas (si existen)
    try:
        db.query(LibroMayorEntry).filter(LibroMayorEntry.id_partida == id).delete(synchronize_session=False)
    except Exception:
        # si no existe la tabla o falla, ignorar para no bloquear la eliminación
        pass

    # Borrar detalle (si no está en cascada) y luego la partida
    db.query(PartidaDetalle).filter(PartidaDetalle.id_partida == id).delete(synchronize_session=False)
    db.delete(p)
    db.commit()
    return
