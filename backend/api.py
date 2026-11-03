"""Capa de API: traduce peticiones HTTP a llamadas al núcleo del agente.

Por ahora solo expone el health check para validar el despliegue en Vercel.
"""

from fastapi import FastAPI

app = FastAPI(title="Astarito")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Confirma que la función de Python responde."""
    return {"status": "ok"}
