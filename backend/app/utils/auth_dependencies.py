from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from .token import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username = payload.get("sub")
        rol = payload.get("rol")

        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        return {"username": username, "rol": rol}

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
