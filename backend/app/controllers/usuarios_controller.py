from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.tablas import Usuario
from ..schemas import UsuarioCreate, LoginRequest
from ..utils.auth_utils import encriptar, verificar
from ..utils.conexion_db import get_db
from ..utils.token import crear_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------------- REGISTRO ----------------------
@router.post("/register")
def register(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(Usuario).filter(Usuario.username == usuario.username).first()

    if db_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe")

    nuevo = Usuario(
        username=usuario.username,
        password_hash=encriptar(usuario.password),
        nombre_completo=usuario.nombre_completo,
        rol=usuario.rol,
        activo=True
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return {"mensaje": "Usuario creado", "usuario": nuevo.username}


# ---------------------- LOGIN ----------------------
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.username == data.username).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    if not verificar(data.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    token = crear_token({"sub": usuario.username, "rol": usuario.rol})

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "username": usuario.username,
            "nombre_completo": usuario.nombre_completo,
            "rol": usuario.rol
        }
    }
