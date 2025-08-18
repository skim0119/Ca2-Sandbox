import os
import json
import shutil
from pathlib import Path
from typing import Optional, List
import tempfile
import zipfile

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import base64

from . import __version__ as ca2roi_version
from .video import process_video, get_first_frame
from .roi import handle_rois, extract_and_save_traces
from .bleaching import (
    compute_bleaching,
    save_bleaching,
    save_bleaching_trend_csv,
    plot_bleaching_trend,
)
from .fluctuation import (
    compute_fluctuation_map,
    save_fluctuation_overlay,
    auto_select_rois_from_fluctuation,
    filter_rois_by_size,
    save_auto_rois_plot,
    plot_roi_intensity_traces,
)
from .roi_similarity import cluster_rois_by_similarity, plot_clustered_rois
from .utils import ensure_workspace

# Pydantic models for request validation
from pydantic import BaseModel, Field
from typing import Optional


class AnalysisRequest(BaseModel):
    video_path: str = Field(..., description="Path to the video file")
    auto_roi: bool = Field(
        True, description="Whether to perform automatic ROI selection"
    )
    threshold_percentage: float = Field(
        99.0, description="Threshold percentage for ROI detection"
    )
    min_distance_percentage: float = Field(
        0.01, description="Minimum distance percentage between ROIs"
    )
    n_clusters: int = Field(
        3, description="Number of clusters for ROI similarity analysis"
    )


def create_app():
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Ca2ROI Analysis Server",
        description="Calcium imaging ROI and bleaching analysis web interface",
        version=ca2roi_version,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount(
            "/static", StaticFiles(directory=str(static_dir), html=True), name="static"
        )
    else:
        raise FileNotFoundError(f"Pre-built static directory not found: {static_dir}")

    return app


app = create_app()


@app.get("/")
async def root():
    """Serve the main HTML page."""
    static_dir = Path(__file__).parent.parent.parent.parent / "static"
    index_path = static_dir / "index.html"

    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return JSONResponse(
            {
                "message": "Ca2ROI Analysis Server",
                "status": "running",
                "endpoints": [
                    "/api/analyze",
                    "/api/results",
                    "/api/download",
                    "/api/version",
                ],
            }
        )


@app.post("/api/analyze")
async def analyze_video(request: AnalysisRequest):
    """Analyze a video file from its path with the given parameters.

    Example request body:
    {
        "video_path": "/path/to/your/video.mp4",
        "auto_roi": true,
        "threshold_percentage": 99.0,
        "min_distance_percentage": 0.01,
        "n_clusters": 3
    }

    Example response:
    {
        "session_id": "ca2roi_abc123",
        "status": "completed",
        "workspace": "/tmp/ca2roi_abc123/results",
        "video_path": "/path/to/your/video.mp4",
        "results": ["bleaching.pkl", "bleaching_trend.csv", "fluctuation_overlay.pdf", "roi_traces.csv"]
    }
    """
    video_path = Path(request.video_path)

    # Validate video file exists and has supported format
    if not video_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Video file not found: {video_path}"
        )

    if not video_path.suffix.lower() in [".avi", ".mp4", ".mov", ".tiff", ".tif"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # Create temporary directory for this session
    session_dir = Path(tempfile.mkdtemp(prefix="ca2roi_"))
    workspace = session_dir / "results"

    try:
        ensure_workspace(workspace)

        # Process video
        frames, info = process_video(str(video_path))

        # Compute bleaching
        mean_intensity = compute_bleaching(frames)
        bleach_pkl_path = workspace / "bleaching.pkl"
        bleach_csv_path = workspace / "bleaching_trend.csv"
        save_bleaching(mean_intensity, info, str(bleach_pkl_path))
        save_bleaching_trend_csv(mean_intensity, info["fps"], str(bleach_csv_path))

        # Compute fluctuation map
        fluct_map = compute_fluctuation_map(frames, mean_intensity)
        overlay_img_path = workspace / "fluctuation_overlay.pdf"
        save_fluctuation_overlay(fluct_map, str(overlay_img_path))

        # Auto ROI selection
        if request.auto_roi:
            import numpy as np

            threshold = np.percentile(fluct_map, request.threshold_percentage)
            min_distance = int(frames.shape[2] * request.min_distance_percentage)

            roi_data = auto_select_rois_from_fluctuation(
                fluct_map, frames, threshold, min_distance, str(workspace)
            )

            # Extract traces
            roi_csv_path = workspace / "roi_traces.csv"
            extract_and_save_traces(frames, roi_data, str(roi_csv_path))

            # Clustering
            cluster_rois_by_similarity(
                str(roi_csv_path), request.n_clusters, str(workspace)
            )

        return JSONResponse(
            {
                "session_id": session_dir.name,
                "status": "completed",
                "workspace": str(workspace),
                "video_path": str(video_path),
                "results": [str(p) for p in workspace.glob("*")],
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """Get analysis results for a session."""
    session_dir = Path(tempfile.gettempdir()) / session_id
    workspace = session_dir / "results"

    if not workspace.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    results = {}
    for file_path in workspace.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(workspace)
            results[str(rel_path)] = {
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
            }

    return JSONResponse({"results": results})


@app.get("/api/download/{session_id}")
async def download_results(session_id: str):
    """Download all results as a ZIP file."""
    session_dir = Path(tempfile.gettempdir()) / session_id
    workspace = session_dir / "results"

    if not workspace.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    zip_path = session_dir / "results.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in workspace.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(workspace)
                zipf.write(file_path, arcname)

    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=f"ca2roi_results_{session_id}.zip",
    )


@app.get("/api/version")
async def get_version():
    """Get the ca2roi version."""
    return JSONResponse({"version": ca2roi_version, "package": "ca2roi"})


@app.post("/api/first-frame")
async def get_video_first_frame(request: dict):
    """Get the first frame of a video file as a base64 encoded image.

    Example request body:
    {
        "video_path": "/path/to/your/video.mp4"
    }

    Example response:
    {
        "first_frame": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
        "video_info": {
            "width": 640,
            "height": 480,
            "fps": 30.0,
            "total_frames": 1000
        }
    }
    """
    video_path = Path(request.get("video_path", ""))

    # Validate video file exists and has supported format
    if not video_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Video file not found: {video_path}"
        )

    if not video_path.suffix.lower() in [".avi", ".mp4", ".mov", ".tiff", ".tif"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    try:
        # Get first frame and video info
        first_frame, video_info = get_first_frame(str(video_path))

        return JSONResponse({"first_frame": first_frame, "video_info": video_info})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get first frame: {str(e)}"
        )
