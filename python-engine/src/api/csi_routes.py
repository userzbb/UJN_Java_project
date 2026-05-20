"""CSI API 路由"""

from fastapi import APIRouter, Depends, HTTPException

from .deps import get_csi_loader, get_event_bus
from ..stream.sse import sse_event_generator

router = APIRouter(prefix="/csi", tags=["CSI"])


@router.get("/datasets")
async def list_datasets(loader=Depends(get_csi_loader)):
    """列出 available CSI datasets。"""
    datasets = loader.list_datasets()
    return {"datasets": datasets}


@router.post("/load")
async def load_dataset(
    body: dict,
    loader=Depends(get_csi_loader),
):
    """
    加载数据集并开始播放。

    body: {"dataset": "signfi_sample", "speed": 1.0}
    """
    dataset = body.get("dataset", "")
    speed = body.get("speed", 1.0)

    if not dataset:
        raise HTTPException(status_code=400, detail="dataset name is required")

    try:
        info = await loader.load(dataset)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    loader.set_speed(speed)
    await loader.play()

    return {"status": "playing", **info}


@router.post("/stop")
async def stop_playback(loader=Depends(get_csi_loader)):
    """停止播放。"""
    await loader.stop()
    return {"status": "stopped"}


@router.post("/pause")
async def pause_playback(loader=Depends(get_csi_loader)):
    """暂停 / 继续。"""
    loader.pause()
    return {"status": "paused", "playing": loader.playing}


@router.post("/seek")
async def seek_frame(body: dict, loader=Depends(get_csi_loader)):
    """跳转到指定帧。"""
    idx = body.get("frame_index", 0)
    loader.seek(int(idx))
    return {"status": "seeked", "frame": idx}


@router.post("/speed")
async def set_speed(body: dict, loader=Depends(get_csi_loader)):
    """设置播放速度 0.1 ~ 10x。"""
    speed = float(body.get("speed", 1.0))
    loader.set_speed(speed)
    return {"status": "ok", "speed": speed}


@router.get("/progress")
async def get_progress(loader=Depends(get_csi_loader)):
    """当前播放进度。"""
    return loader.progress


@router.get("/events/stream")
async def csi_event_stream(eb=Depends(get_event_bus)):
    """
    SSE 端点：实时推送 CSI 帧事件和运动告警。
    Spring Boot 通过此端点接收实时数据。
    """
    return await sse_event_generator(
        eb,
        ["csi:frame", "csi:alert"],
    )
