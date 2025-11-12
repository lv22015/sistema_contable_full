from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.tablas import Cuenta
from ..schemas import CuentaCreate, CuentaOut
from ..utils.conexion_db import get_db

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])

def procesar_nivel_y_padre(db: Session, codigo: str) -> (int, Optional[int]):
    """
    aqui se determina automáticamente el nivel y el ID del padre
    en función de la longitud del código.
    Ejemplo:
        1101       → nivel 1, sin padre
        110101     → nivel 2, padre 1101
        11010101   → nivel 3, padre 110101
    """
    codigo = codigo.strip()
    longitud = len(codigo)

    # Nivel base
    if longitud <= 4:
        return 1, None

    # Buscar el padre según las longitudes previas (de 4 en 4)
    for i in range(longitud - 1, 3, -1):
        codigo_padre = codigo[:i]
        padre = db.query(Cuenta).filter(Cuenta.codigo == codigo_padre).first()
        if padre:
            nivel = (len(codigo) // 2)  # Puedes ajustar esta lógica según tu estructura
            return nivel, padre.id_cuenta

    raise HTTPException(status_code=400, detail=f"No existe una cuenta padre válida para el código {codigo}")


# Crear cuenta
@router.post("/", response_model=CuentaOut)
def crear_cuenta(cuenta: CuentaCreate, db: Session = Depends(get_db)):
    db_cuenta_existente = db.query(Cuenta).filter(Cuenta.codigo == cuenta.codigo).first()
    if db_cuenta_existente:
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con ese código")

    nivel, cuenta_padre_id = procesar_nivel_y_padre(db, cuenta.codigo)

    nueva_cuenta = Cuenta(
        codigo=cuenta.codigo.strip(),
        nombre=cuenta.nombre.strip(),
        tipo=cuenta.tipo.strip(),
        nivel=nivel,
        cuenta_padre=cuenta_padre_id
    )

    db.add(nueva_cuenta)
    db.commit()
    db.refresh(nueva_cuenta)

    # Añadir nombre del padre al resultado
    padre_nombre = None
    if cuenta_padre_id:
        padre = db.query(Cuenta).filter(Cuenta.id_cuenta == cuenta_padre_id).first()
        if padre:
            padre_nombre = f"{padre.codigo} - {padre.nombre}"

    return {
        "id_cuenta": nueva_cuenta.id_cuenta,
        "codigo": nueva_cuenta.codigo,
        "nombre": nueva_cuenta.nombre,
        "tipo": nueva_cuenta.tipo,
        "nivel": nueva_cuenta.nivel,
        "cuenta_padre": padre_nombre,
        "fecha_creacion": nueva_cuenta.fecha_creacion
    }


# Listar cuentas (muestra nombre del padre)
@router.get("/", response_model=List[CuentaOut])
def listar_cuentas(db: Session = Depends(get_db)):
    cuentas = db.query(Cuenta).order_by(Cuenta.codigo).all()
    resultado = []

    for c in cuentas:
        nombre_padre = None
        if c.cuenta_padre:
            padre = db.query(Cuenta).filter(Cuenta.id_cuenta == c.cuenta_padre).first()
            if padre:
                nombre_padre = f"{padre.codigo} - {padre.nombre}"

        resultado.append({
            "id_cuenta": c.id_cuenta,
            "codigo": c.codigo,
            "nombre": c.nombre,
            "tipo": c.tipo,
            "nivel": c.nivel,
            "cuenta_padre": nombre_padre,
            "fecha_creacion": getattr(c, "fecha_creacion", None)
        })

    return resultado


# Obtener cuenta por ID
@router.get("/{id_cuenta}", response_model=CuentaOut)
def obtener_cuenta(id_cuenta: int, db: Session = Depends(get_db)):
    c = db.query(Cuenta).filter(Cuenta.id_cuenta == id_cuenta).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    nombre_padre = None
    if c.cuenta_padre:
        padre = db.query(Cuenta).filter(Cuenta.id_cuenta == c.cuenta_padre).first()
        if padre:
            nombre_padre = f"{padre.codigo} - {padre.nombre}"

    return {
        "id_cuenta": c.id_cuenta,
        "codigo": c.codigo,
        "nombre": c.nombre,
        "tipo": c.tipo,
        "nivel": c.nivel,
        "cuenta_padre": nombre_padre,
        "fecha_creacion": getattr(c, "fecha_creacion", None)
    }


# Actualizar cuenta
@router.put("/{id}", response_model=CuentaOut)
def actualizar_cuenta(id: int, data: CuentaCreate, db: Session = Depends(get_db)):
    c = db.query(Cuenta).filter(Cuenta.id_cuenta == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    # Recalcular nivel y cuenta padre
    nivel, cuenta_padre_id = procesar_nivel_y_padre(db, data.codigo)

    c.codigo = data.codigo.strip()
    c.nombre = data.nombre.strip()
    c.tipo = data.tipo.strip()
    c.nivel = nivel
    c.cuenta_padre = cuenta_padre_id

    db.commit()
    db.refresh(c)

    nombre_padre = None
    if cuenta_padre_id:
        padre = db.query(Cuenta).filter(Cuenta.id_cuenta == cuenta_padre_id).first()
        if padre:
            nombre_padre = f"{padre.codigo} - {padre.nombre}"

    return {
        "id_cuenta": c.id_cuenta,
        "codigo": c.codigo,
        "nombre": c.nombre,
        "tipo": c.tipo,
        "nivel": c.nivel,
        "cuenta_padre": nombre_padre,
        "fecha_creacion": getattr(c, "fecha_creacion", None)
    }


# Eliminar cuenta (validando subcuentas)
@router.delete("/{id_cuenta}")
def eliminar_cuenta(id_cuenta: int, db: Session = Depends(get_db)):
    cuenta = db.query(Cuenta).filter(Cuenta.id_cuenta == id_cuenta).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    # Validar si tiene subcuentas
    subcuentas = db.query(Cuenta).filter(Cuenta.cuenta_padre == id_cuenta).first()
    if subcuentas:
        raise HTTPException(status_code=400, detail="No se puede eliminar una cuenta con subcuentas asociadas")

    db.delete(cuenta)
    db.commit()
    return {"mensaje": "Cuenta eliminada correctamente"}
