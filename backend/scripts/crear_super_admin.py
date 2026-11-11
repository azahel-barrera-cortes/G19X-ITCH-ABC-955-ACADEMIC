"""
Script para crear un Super Administrador en la base de datos existente.

Uso:
    python scripts/crear_super_admin.py

No borra ningún dato existente. Solo crea el usuario si no existe ya
un Super Administrador con el email configurado en SEED_ADMIN_EMAIL.
Si las tablas no existen, las crea automáticamente.
"""
from __future__ import annotations

from app.core.config import settings
from app.core import security
from app.db.session import SessionLocal, engine
from app.models.usuario import Usuario
from app.db.base import Base


def _init_tables() -> None:
    """Crea las tablas si aún no existen (sin borrar datos)."""
    from app import models  # noqa: F401  (registra modelos en Base.metadata)
    Base.metadata.create_all(bind=engine)


def main() -> None:
    _init_tables()

    db = SessionLocal()
    try:
        # Verificar si ya existe un Super Administrador
        existente = (
            db.query(Usuario)
            .filter(Usuario.rol == "SuperAdministrador")
            .first()
        )
        if existente:
            print(
                f"Ya existe un Super Administrador: {existente.email} "
                f"(id={existente.id})"
            )
            return

        # Verificar si el email del seed ya está ocupado por otro rol
        ocupante = (
            db.query(Usuario)
            .filter(Usuario.email == settings.seed_admin_email)
            .first()
        )
        if ocupante:
            print(
                f"El email {settings.seed_admin_email} ya está registrado "
                f"con el rol '{ocupante.rol}'. "
                f"Promoviendo a Super Administrador..."
            )
            ocupante.rol = "SuperAdministrador"
            db.commit()
            db.refresh(ocupante)
            print(
                f"Usuario {ocupante.email} promovido a Super Administrador."
            )
            return

        # Crear nuevo Super Administrador
        usuario = Usuario(
            email=settings.seed_admin_email,
            nombre_completo=settings.seed_admin_nombre,
            rol="SuperAdministrador",
            password_hash=security.hash_password(settings.seed_admin_password),
            activo=True,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        print(
            "Super Administrador creado exitosamente:\n"
            f"  Email:    {usuario.email}\n"
            f"  Nombre:   {usuario.nombre_completo}\n"
            f"  Rol:      {usuario.rol}\n"
            f"  ID:       {usuario.id}\n"
            f"  Activo:   {usuario.activo}\n"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()