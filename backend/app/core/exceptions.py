"""Excepciones de dominio de PGAC.

Permiten que los servicios expresen errores de negocio con un código HTTP claro,
traducidos a respuestas JSON uniformes en ``app.main``.
"""

from __future__ import annotations


class PGACError(Exception):
    """Error base de la plataforma PGAC."""

    codigo_http: int = 400

    def __init__(self, mensaje: str, detalle: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalle = detalle


class ActaNoEncontradaError(PGACError):
    """El acta solicitada no existe (HTTP 404)."""

    codigo_http = 404


class DatosActaInvalidosError(PGACError):
    """Los datos del acta son inconsistentes para el trámite solicitado (HTTP 422)."""

    codigo_http = 422


class IAServicioError(PGACError):
    """El proveedor de IA no pudo completar la solicitud (HTTP 503)."""

    codigo_http = 503
