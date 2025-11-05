from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.tablas import Cuenta
from ..schemas import CuentaCreate, CuentaOut
from ..utils.conexion_db import get_db

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])


#  Función auxiliar para determinar nivel y cuenta padre
def procesar_nivel_y_padre(db: Session, codigo: str) -> (int, Optional[int]):
    if len(codigo) == 4:
        return 1, None
    else:
        codigo_padre = codigo[:4]
        cuenta_padre = db.query(Cuenta).filter(Cuenta.codigo == codigo_padre).first()
        if not cuenta_padre:
            raise HTTPException(status_code=400, detail=f"No existe la cuenta padre con código {codigo_padre}")
        return 2, cuenta_padre.id_cuenta


# Crear cuenta
@router.post("/", response_model=CuentaOut)
def crear_cuenta(cuenta: CuentaCreate, db: Session = Depends(get_db)):
    db_cuenta_existente = db.query(Cuenta).filter(Cuenta.codigo == cuenta.codigo).first()
    if db_cuenta_existente:
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con ese código")

    nivel, cuenta_padre_id = procesar_nivel_y_padre(db, cuenta.codigo)
    nueva_cuenta = Cuenta(
        codigo=cuenta.codigo,
        nombre=cuenta.nombre,
        tipo=cuenta.tipo,
        nivel=nivel,
        cuenta_padre=cuenta_padre_id
    )
    db.add(nueva_cuenta)
    db.commit()
    db.refresh(nueva_cuenta)
    return nueva_cuenta


# Listar cuentas (con nombre de padre)
@router.get("/", response_model=List[CuentaOut])
def listar_cuentas(db: Session = Depends(get_db)):
    cuentas = db.query(Cuenta).all()
    resultado = []

    for c in cuentas:
        cuenta_dict = c.__dict__.copy()
        cuenta_dict.pop("_sa_instance_state", None)
        if c.cuenta_padre:
            padre = db.query(Cuenta).filter(Cuenta.id_cuenta == c.cuenta_padre).first()
            cuenta_dict["cuenta_padre"] = f"{padre.codigo} - {padre.nombre}" if padre else None
        else:
            cuenta_dict["cuenta_padre"] = None
        resultado.append(cuenta_dict)

    return resultado


# Obtener cuenta por ID
@router.get("/{id_cuenta}", response_model=CuentaOut)
def obtener_cuenta(id_cuenta: int, db: Session = Depends(get_db)):
    cuenta = db.query(Cuenta).filter(Cuenta.id_cuenta == id_cuenta).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return cuenta


@router.put("/{id}", response_model=CuentaOut)
def actualizar_cuenta(id: int, data: CuentaCreate, db: Session = Depends(get_db)):
    c = db.query(Cuenta).filter(Cuenta.id_cuenta == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    # Determinar nivel y cuenta_padre según el código
    codigo = data.codigo.strip()
    nivel = 1
    cuenta_padre_id = None

    if len(codigo) > 4:
        codigo_padre = codigo[:4]
        padre = db.query(Cuenta).filter(Cuenta.codigo == codigo_padre).first()
        if padre:
            nivel = 2
            cuenta_padre_id = padre.id_cuenta

    # Actualizar datos
    c.codigo = codigo
    c.nombre = data.nombre
    c.tipo = data.tipo
    c.nivel = nivel
    c.cuenta_padre = cuenta_padre_id

    db.add(c)
    db.commit()
    db.refresh(c)
    return c



# Eliminar cuenta
@router.delete("/{id_cuenta}")
def eliminar_cuenta(id_cuenta: int, db: Session = Depends(get_db)):
    cuenta = db.query(Cuenta).filter(Cuenta.id_cuenta == id_cuenta).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    # Evitar eliminar si tiene subcuentas
    subcuentas = db.query(Cuenta).filter(Cuenta.cuenta_padre == id_cuenta).first()
    if subcuentas:
        raise HTTPException(status_code=400, detail="No se puede eliminar una cuenta con subcuentas asociadas")

    db.delete(cuenta)
    db.commit()
    return {"mensaje": "Cuenta eliminada correctamente"}
