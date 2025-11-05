
# Sistema Contable - Esqueleto
Proyecto inicial con FastAPI backend (endpoints CRUD para usuarios, cuentas y partidas),
Streamlit frontend (esqueleto de páginas) y PostgreSQL como base de datos.

## Arranque rápido

1. Copia el repo en tu máquina.
2. Construye las imágenes y levanta los contenedores:
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```
3. Accede a:
   - pgAdmin: http://localhost:8080 (admin@conta.local / admin123)
   - Backend docs: http://localhost:8000/docs
   - Frontend Streamlit: http://localhost:8501

## Estructura
- backend/: FastAPI app
- frontend/: Streamlit app con páginas
- database/: init.sql para inicializar la BD

## Notas
- Las tablas se crearán automáticamente por SQLAlchemy al iniciar el backend (además del init.sql al inicializar Postgres).
- Cambia las credenciales en `docker-compose.yml` si lo deseas.
