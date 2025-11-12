
from fastapi import FastAPI
from .utils.conexion_db import engine, Base
from .controllers import usuarios_controller, cuentas_controller, partidas_controller, manual_cuentas_controller


def create_app():
    app = FastAPI(title="Sistema Contable API")

    # include routers
    app.include_router(usuarios_controller.router)
    app.include_router(cuentas_controller.router)
    app.include_router(partidas_controller.router)
    app.include_router(manual_cuentas_controller.router)

    @app.on_event("startup")
    def on_startup():
        # create tables if not exist
        Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_app()
