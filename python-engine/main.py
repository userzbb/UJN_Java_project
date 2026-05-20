"""
无线信号分析引擎 — FastAPI 入口.

启动: uv run main.py
API 文档: http://localhost:8765/docs
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import config
from src.api.ble_routes import router as ble_router
from src.api.csi_routes import router as csi_router

# ── 日志 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── 应用 ──
app = FastAPI(
    title="Wireless Signal Analysis Engine",
    version="0.1.0",
    description="BLE spectrum sensing & CSI signal analysis — DSP engine",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(ble_router)
app.include_router(csi_router)


# ── 健康检查 ──
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "wireless-engine",
    }


# ── 入口 ──
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Wireless Signal Analysis Engine on %s:%d", config.host, config.port)
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=False,
        log_level="info",
    )
