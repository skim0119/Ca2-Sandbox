import os
import json
import shutil
from pathlib import Path
from typing import Optional, List
import tempfile
import zipfile
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

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
    exponential_decay,
    inverse_decay,
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
            "/static",
            StaticFiles(directory=static_dir.as_posix(), html=True),
            name="static",
        )
    else:
        raise FileNotFoundError(f"Pre-built static directory not found: {static_dir}")

    return app


app = create_app()


@app.get("/")
async def root():
    """Serve the main HTML page."""
    static_dir = Path(__file__).parent.parent.parent / "static"
    index_path = static_dir / "index.html"

    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return JSONResponse(
            {
                "message": "Ca2ROI Analysis Server",
                "status": "Pre-built static directory not found",
            }
        )


@app.get("/api/version")
async def get_version():
    return JSONResponse({"version": ca2roi_version, "package": "ca2roi"})


# @app.get("/")
# async def root():
#     """Serve the main HTML page."""
#     static_dir = Path(__file__).parent.parent.parent.parent / "static"
#     index_path = static_dir / "index.html"

#     if index_path.exists():
#         return FileResponse(str(index_path))
#     else:
#         return JSONResponse(
#             {
#                 "message": "Ca2ROI Analysis Server",
#                 "status": "running",
#                 "endpoints": [
#                     "/api/analyze",
#                     "/api/results",
#                     "/api/download",
#                     "/api/version",
#                 ],
#             }
#         )


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


# Global cache for analysis results
analysis_cache = {}


@app.post("/api/run-analysis")
async def run_bleaching_analysis(request: dict):
    """Run bleaching analysis on a video file.

    Example request body:
    {
        "video_path": "/path/to/your/video.mp4"
    }

    Example response:
    {
        "analysis_id": "analysis_abc123",
        "status": "completed",
        "bleaching_data": {
            "time_points": [0.0, 0.033, 0.067, ...],
            "mean_intensity": [100.5, 98.2, 96.1, ...],
            "fit_params": {
                "exponential": [I0, tau],
                "inverse": [I0, tau]
            },
            "r2_scores": {
                "exponential": 0.985,
                "inverse": 0.992
            }
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
        # Check if analysis is already cached
        video_key = str(video_path)
        if video_key in analysis_cache:
            print(f"Using cached analysis for: {video_path}")
            return JSONResponse(analysis_cache[video_key])

        # Process video and compute bleaching
        frames, info = process_video(str(video_path))
        mean_intensity = compute_bleaching(frames)

        # Create time points
        time_points = np.arange(len(mean_intensity)) / info["fps"]

        # Run both exponential and inverse fits
        fit_params = {}
        r2_scores = {}

        # Exponential fit
        try:
            I0_guess = mean_intensity[0]
            tau_guess = time_points[-1] / 3
            popt_exp, _ = curve_fit(
                exponential_decay,
                time_points,
                mean_intensity,
                p0=[I0_guess, tau_guess],
                maxfev=10000,
            )
            fit_params["exponential"] = popt_exp.tolist()
            y_fit_exp = exponential_decay(time_points, *popt_exp)
            r2_scores["exponential"] = r2_score(mean_intensity, y_fit_exp)
        except Exception as e:
            print(f"Warning: Could not fit exponential curve: {e}")
            fit_params["exponential"] = None
            r2_scores["exponential"] = None

        # Inverse fit
        try:
            I0_guess = mean_intensity[0]
            tau_guess = time_points[-1] / 2
            popt_inv, _ = curve_fit(
                inverse_decay,
                time_points,
                mean_intensity,
                p0=[I0_guess, tau_guess],
                maxfev=10000,
            )
            fit_params["inverse"] = popt_inv.tolist()
            y_fit_inv = inverse_decay(time_points, *popt_inv)
            r2_scores["inverse"] = r2_score(mean_intensity, y_fit_inv)
        except Exception as e:
            print(f"Warning: Could not fit inverse curve: {e}")
            fit_params["inverse"] = None
            r2_scores["inverse"] = None

        # Create analysis result
        analysis_id = f"analysis_{hash(video_key) % 1000000}"
        result = {
            "analysis_id": analysis_id,
            "status": "completed",
            "bleaching_data": {
                "time_points": time_points.tolist(),
                "mean_intensity": mean_intensity.tolist(),
                "fit_params": fit_params,
                "r2_scores": r2_scores,
                "video_info": {
                    "width": info["width"],
                    "height": info["height"],
                    "fps": info["fps"],
                    "total_frames": info["n_frames"],
                },
            },
        }

        # Cache the result
        analysis_cache[video_key] = result

        return JSONResponse(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/update-fit-preference")
async def update_fit_preference(request: dict):
    """Update the user's fit preference (exponential vs inverse).

    Example request body:
    {
        "analysis_id": "analysis_abc123",
        "fit_type": "exponential"  # or "inverse"
    }
    """
    analysis_id = request.get("analysis_id")
    fit_type = request.get("fit_type")

    if fit_type not in ["exponential", "inverse"]:
        raise HTTPException(status_code=400, detail="Invalid fit type")

    # In a real implementation, you might save this to a database
    # For now, we'll just log it
    print(f"User preference updated: {analysis_id} -> {fit_type}")

    return JSONResponse(
        {"status": "updated", "analysis_id": analysis_id, "fit_type": fit_type}
    )


@app.post("/api/roi-operations")
async def handle_roi_operations(request: dict):
    """Handle ROI operations: create, select, unselect, compute intensity.

    Example request body:
    {
        "operation": "create",  # "create", "select", "unselect"
        "video_path": "/path/to/video.mp4",
        "roi_data": {
            "id": 1,
            "coords": [x0, y0, x1, y1],  # For create operation
            "selected": true  # For select/unselect operations
        },
        "adjust_bleaching": true,
        "fit_type": "inverse"
    }
    """
    operation = request.get("operation")
    print(f"🎯 ROI operation requested: {request}")
    video_path = Path(request.get("video_path", ""))

    if not video_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Video file not found: {video_path}"
        )

    try:
        # Process video
        frames, info = process_video(str(video_path))

        if operation == "create":
            roi_coords = request["roi_data"]["coords"]
            x0, y0, x1, y1 = roi_coords

            # Create ROI mask
            roi_mask = np.zeros((info["height"], info["width"]), dtype=bool)
            roi_mask[y0:y1, x0:x1] = True

            # Compute intensity over time
            n_frames = frames.shape[0]
            intensity_trace = np.zeros(n_frames)
            for frame_idx in range(n_frames):
                intensity_trace[frame_idx] = frames[frame_idx][roi_mask].mean()

            # Apply bleaching correction if requested
            adjust_bleaching = request.get("adjust_bleaching", False)
            fit_type = request.get("fit_type", "inverse")

            if adjust_bleaching:
                try:
                    # Compute bleaching trend
                    mean_intensity = compute_bleaching(frames)
                    time_points = np.arange(n_frames) / info["fps"]

                    # Get bleaching parameters from cache or compute
                    video_key = str(video_path)
                    if video_key in analysis_cache:
                        bleaching_data = analysis_cache[video_key]["bleaching_data"]
                        if (
                            fit_type == "exponential"
                            and bleaching_data["fit_params"]["exponential"]
                        ):
                            I0, tau = bleaching_data["fit_params"]["exponential"]
                            bleaching_trend = I0 * np.exp(-time_points / tau)
                        elif (
                            fit_type == "inverse"
                            and bleaching_data["fit_params"]["inverse"]
                        ):
                            I0, tau = bleaching_data["fit_params"]["inverse"]
                            bleaching_trend = I0 / (1 + time_points / tau)
                        else:
                            # Fallback to polynomial fit
                            bleaching_trend = np.polyval(
                                np.polyfit(time_points, mean_intensity, 2), time_points
                            )

                        # Correct intensity trace
                        intensity_trace = (
                            intensity_trace / bleaching_trend * bleaching_trend[0]
                        )
                    else:
                        # If no cached analysis, use simple polynomial fit
                        print(
                            f"⚠️ No cached bleaching analysis for {video_key}, using polynomial fit"
                        )
                        bleaching_trend = np.polyval(
                            np.polyfit(time_points, mean_intensity, 2), time_points
                        )
                        intensity_trace = (
                            intensity_trace / bleaching_trend * bleaching_trend[0]
                        )
                except Exception as e:
                    print(
                        f"⚠️ Bleaching correction failed: {e}, using uncorrected intensity"
                    )
                    # Continue without bleaching correction

            return JSONResponse(
                {
                    "status": "created",
                    "roi_id": request["roi_data"]["id"],
                    "intensity_trace": intensity_trace.tolist(),
                    "time_points": (np.arange(n_frames) / info["fps"]).tolist(),
                    "roi_info": {
                        "coords": roi_coords,
                        "n_pixels": int(roi_mask.sum()),
                        "center": [float((x0 + x1) / 2), float((y0 + y1) / 2)],
                    },
                }
            )

        elif operation in ["select", "unselect"]:
            # For select/unselect, we just return success
            # The frontend will handle showing/hiding the ROI
            return JSONResponse(
                {"status": operation, "roi_id": request["roi_data"]["id"]}
            )

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown operation: {operation}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ROI operation failed: {str(e)}")
