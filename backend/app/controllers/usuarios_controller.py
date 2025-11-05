
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from ..utils.conexion_db import get_db
from ..models.tablas import Usuario
from ..schemas import UsuarioCreate, UsuarioOut, UsuarioBase

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/", response_model=list[UsuarioOut])
def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Usuario).offset(skip).limit(limit).all()

@router.post("/", response_model=UsuarioOut)
def crear_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    exists = db.query(Usuario).filter(Usuario.username == data.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="El username ya existe")
    hashed = pwd_context.hash(data.password)
    u = Usuario(username=data.username, password_hash=hashed, nombre_completo=data.nombre_completo, rol=data.rol, activo=data.activo)
    db.add(u); db.commit(); db.refresh(u)
    return u

@router.put("/{id}", response_model=UsuarioOut)
def actualizar_usuario(id: int, data: UsuarioBase, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.id_usuario == id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(u, k, v)
    db.add(u); db.commit(); db.refresh(u)
    return u

@router.delete("/{id}")
def eliminar_usuario(id: int, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.id_usuario == id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(u); db.commit()
    return {"ok": True}
