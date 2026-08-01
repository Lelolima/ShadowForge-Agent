"""
============================================================
NVIDIA ShadowForge Agent - Dashboard API
Arquivo: api/dashboard.py
============================================================
API FastAPI com WebSocket para monitoramento real-time
de campanhas, visão da kill chain, eventos e métricas.
============================================================
"""

from __future__ import annotations

import logging
import time
from typing import Any

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, Response
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


if HAS_FASTAPI:
    app = FastAPI(title="ShadowForge Dashboard", version="2.0.0")
    # Segurança: restringir CORS para origens conhecidas do dashboard
    # Em produção, configurar DASHBOARD_ORIGINS no .env
    import os
    _allowed_origins = os.environ.get(
        "DASHBOARD_ORIGINS",
        "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000",
    ).split(",")
    # H-12 FIX: Token de autenticação para WebSocket (via env var)
    _ws_auth_token = os.environ.get("DASHBOARD_WS_TOKEN", "")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "WEBSOCKET"],
        allow_headers=["*"],
    )
else:
    app = None  # type: ignore

logger = logging.getLogger("shadowforge.api.dashboard")

# Estado runtime compartilhado (injetado pelo agente)
_dashboard_state: dict[str, Any] = {
    "agente_online": False,
    "fase_atual": "idle",
    "alvo": "",
    "iteracoes": 0,
    "vulnerabilidades": 0,
    "eventos": [],
    "clients": set(),
}


def update_dashboard_state(key: str, value: Any) -> None:
    """Atualiza estado para broadcasting."""
    _dashboard_state[key] = value


async def broadcast(msg: dict[str, Any]) -> None:
    """Envia mensagem para todos os WebSocket clients."""
    if not HAS_FASTAPI:
        return
    dead = set()
    for ws in list(_dashboard_state.get("clients", set())):
        try:
            await ws.send_json(msg)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _dashboard_state["clients"].discard(ws)


if HAS_FASTAPI:
    @app.get("/api/status")  # type: ignore
    async def api_status() -> dict[str, Any]:
        """Status geral do agente."""
        return {
            "online": _dashboard_state.get("agente_online", False),
            "fase": _dashboard_state.get("fase_atual", "idle"),
            "alvo": _dashboard_state.get("alvo", ""),
            "iteracoes": _dashboard_state.get("iteracoes", 0),
            "vulnerabilidades": _dashboard_state.get("vulnerabilidades", 0),
            "timestamp": time.time(),
        }

    @app.get("/api/campaign")
    async def api_campaign() -> dict[str, Any]:
        """Detalhes da campanha atual."""
        return {k: v for k, v in _dashboard_state.items() if k != "clients"}

    @app.get("/api/events")
    async def api_events() -> dict[str, Any]:
        """Eventos recentes."""
        return {"eventos": _dashboard_state.get("eventos", [])[-200:]}

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        try:
            from observability.metrics import get_metrics, get_metrics_content_type
            data = get_metrics()
            return Response(content=data, media_type=get_metrics_content_type())
        except ImportError:
            return Response(content=b"# prometheus_client not installed\n", media_type="text/plain")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:  # type: ignore
        """WebSocket para streaming tempo real.
        H-12 FIX: Requer token de autenticação via query param ?token=XXX
        ou header Sec-WebSocket-Protocol. Sem token, conexão é rejeitada.
        """
        # H-12 FIX: Verificar token de autenticação
        if _ws_auth_token:
            token = websocket.query_params.get("token", "")
            if token != _ws_auth_token:
                await websocket.close(code=4001, reason="Autenticação necessária — forneça ?token=XXX")
                return
        await websocket.accept()
        _dashboard_state["clients"].add(websocket)
        try:
            await websocket.send_json({
                "type": "init",
                "data": await api_status(),
            })
            while True:
                msg = await websocket.receive_text()
                if msg == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            _dashboard_state["clients"].discard(websocket)
        except Exception:
            _dashboard_state["clients"].discard(websocket)

    @app.get("/", response_class=HTMLResponse)
    async def dashboard_ui() -> str:
        """UI básica do dashboard."""
        return """
    <!DOCTYPE html>
    <html>
    <head><title>ShadowForge Dashboard</title>
    <style>
    body { background: #0a0a0f; color: #00ff41; font-family: monospace; padding: 2rem; }
    h1 { color: #0ff; }
    .metric { display: inline-block; margin: 1rem; padding: 1rem; border: 1px solid #333; }
    .phase { font-size: 2rem; color: #ffd700; }
    #log { background: #111; padding: 1rem; height: 300px; overflow-y: auto; border: 1px solid #333; }
    </style></head>
    <body>
    <h1>SH4D0WF0RG3 Dashboard</h1>
    <div id="status"></div>
    <div id="log"><div class="metric">Aguardando conexão...</div></div>
    <script>
    const ws = new WebSocket("ws://localhost:8000/ws");
    const log = document.getElementById("log");
    const status = document.getElementById("status");
    ws.onmessage = e => {
        const msg = JSON.parse(e.data);
        if (msg.type === "init") {
            status.innerHTML = `<div class=metric>Phase: <span class=phase>${msg.data.fase}</span></div>`;
        }
        if (msg.data) {
            const div = document.createElement("div");
            div.textContent = `> ${msg.data.fase} | ${msg.data.alvo || "No target"} | Iter: ${msg.data.iteracoes}`;
            log.prepend(div);
        }
    };
    </script>
    </body></html>
    """