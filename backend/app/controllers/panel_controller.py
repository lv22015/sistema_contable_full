from fastapi import APIRouter, Depends

from ..utils.auth_dependencies import obtener_usuario_actual

router = APIRouter(prefix="/panel", tags=["Panel"])

@router.get("/")
def panel_principal(usuario = Depends(obtener_usuario_actual)):
    return {"mensaje": f"Bienvenido {usuario['username']}", "rol": usuario["rol"]}
