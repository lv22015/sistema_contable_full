from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models import tablas
from ..schemas import ManualCuentaCreate, ManualCuentaOut
from ..utils.conexion_db import get_db

router = APIRouter(prefix="/manual_cuentas", tags=["Manual de Cuentas"])


# =====================================================
# 🧾 Crear un registro en el Manual de Cuentas
# =====================================================
@router.post("/", response_model=ManualCuentaOut)
def crear_manual(manual: ManualCuentaCreate, db: Session = Depends(get_db)):
    cuenta = db.query(tablas.Cuenta).filter(tablas.Cuenta.id_cuenta == manual.id_cuenta).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="La cuenta asociada no existe")

    nuevo_manual = tablas.ManualCuenta(
        id_cuenta=manual.id_cuenta,
        descripcion=manual.descripcion.strip(),
        ejemplos=manual.ejemplos.strip() if manual.ejemplos else None,
        id_usuario_crea=manual.id_usuario_crea
    )
    db.add(nuevo_manual)
    db.commit()
    db.refresh(nuevo_manual)

    return {
        "id_manual": nuevo_manual.id_manual,
        "id_cuenta": cuenta.id_cuenta,
        "cuenta_nombre": f"{cuenta.codigo} - {cuenta.nombre}",
        "descripcion": nuevo_manual.descripcion,
        "ejemplos": nuevo_manual.ejemplos,
        "fecha_creacion": nuevo_manual.fecha_creacion,
        "id_usuario_crea": nuevo_manual.id_usuario_crea
    }


# =====================================================
# 📋 Listar manuales de cuentas
# =====================================================
@router.get("/", response_model=List[ManualCuentaOut])
def listar_manuales(db: Session = Depends(get_db)):
    manuales = db.query(tablas.ManualCuenta).all()
    resultado = []

    for m in manuales:
        cuenta = db.query(tablas.Cuenta).filter(tablas.Cuenta.id_cuenta == m.id_cuenta).first()
        resultado.append({
            "id_manual": m.id_manual,
            "id_cuenta": m.id_cuenta,
            "cuenta_nombre": f"{cuenta.codigo} - {cuenta.nombre}" if cuenta else None,
            "descripcion": m.descripcion,
            "ejemplos": m.ejemplos,
            "fecha_creacion": m.fecha_creacion,
            "id_usuario_crea": m.id_usuario_crea
        })

    return resultado


# =====================================================
# 🔍 Obtener manual por ID
# =====================================================
@router.get("/{id_manual}", response_model=ManualCuentaOut)
def obtener_manual(id_manual: int, db: Session = Depends(get_db)):
    m = db.query(tablas.ManualCuenta).filter(tablas.ManualCuenta.id_manual == id_manual).first()
    if not m:
        raise HTTPException(status_code=404, detail="Manual no encontrado")

    cuenta = db.query(tablas.Cuenta).filter(tablas.Cuenta.id_cuenta == m.id_cuenta).first()

    return {
        "id_manual": m.id_manual,
        "id_cuenta": m.id_cuenta,
        "cuenta_nombre": f"{cuenta.codigo} - {cuenta.nombre}" if cuenta else None,
        "descripcion": m.descripcion,
        "ejemplos": m.ejemplos,
        "fecha_creacion": m.fecha_creacion,
        "id_usuario_crea": m.id_usuario_crea
    }


# =====================================================
# ✏️ Actualizar manual
# =====================================================
@router.put("/{id_manual}", response_model=ManualCuentaOut)
def actualizar_manual(id_manual: int, data: ManualCuentaCreate, db: Session = Depends(get_db)):
    m = db.query(tablas.ManualCuenta).filter(tablas.ManualCuenta.id_manual == id_manual).first()
    if not m:
        raise HTTPException(status_code=404, detail="Manual no encontrado")

    cuenta = db.query(tablas.Cuenta).filter(tablas.Cuenta.id_cuenta == data.id_cuenta).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="La cuenta asociada no existe")

    m.id_cuenta = data.id_cuenta
    m.descripcion = data.descripcion.strip()
    m.ejemplos = data.ejemplos.strip() if data.ejemplos else None
    m.id_usuario_crea = data.id_usuario_crea

    db.commit()
    db.refresh(m)

    return {
        "id_manual": m.id_manual,
        "id_cuenta": m.id_cuenta,
        "cuenta_nombre": f"{cuenta.codigo} - {cuenta.nombre}",
        "descripcion": m.descripcion,
        "ejemplos": m.ejemplos,
        "fecha_creacion": m.fecha_creacion,
        "id_usuario_crea": m.id_usuario_crea
    }


# =====================================================
# 🗑️ Eliminar manual
# =====================================================
@router.delete("/{id_manual}")
def eliminar_manual(id_manual: int, db: Session = Depends(get_db)):
    m = db.query(tablas.ManualCuenta).filter(tablas.ManualCuenta.id_manual == id_manual).first()
    if not m:
        raise HTTPException(status_code=404, detail="Manual no encontrado")

    db.delete(m)
    db.commit()
    return {"mensaje": "Manual eliminado correctamente"}
