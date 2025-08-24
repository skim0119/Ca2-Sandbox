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

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import base64

from . import __version__ as ca2roi_version
from .video import (
    load_video_from_contents,
    VideoContentsHandle,
    VideoMetadata,
    convert_frame_to_base64,
)
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
from .smoothing import smooth_intensity_trace
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

# Global cache for analysis results
uploaded_video_contents: dict[str, VideoContentsHandle] = {}  # Keep reference
current_video_data: VideoMetadata | None = None


def assert_video_selected():
    if current_video_data is None:
        raise HTTPException(status_code=400, detail="No video data selected")


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


@app.post("/api/upload-video")
async def upload_video(video_file: UploadFile):
    """Upload a video file and get the first frame as a base64 encoded image.

    Example response:
    {
        "firstFrame": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
        "videoInfo": {
            "width": 640,
            "height": 480,
            "fps": 30.0,
            "total_frames": 1000
        }
    }
    """
    global current_video_data
    global uploaded_video_contents

    print(
        f"Upload endpoint called with file: {video_file.filename}, size: {video_file.size}, content_type: {video_file.content_type}"
    )

    # Validate file format
    if not video_file.filename or not video_file.filename.lower().endswith(
        (".avi", ".mp4", ".mov")
    ):
        print(f"Invalid file format: {video_file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload .avi, .mp4, or .mov files.",
        )

    try:
        print("Reading file content...")
        content = await video_file.read()

        # Save uploaded file to temporary location
        vc = VideoContentsHandle(video_file.filename, content)
        uploaded_video_contents[video_file.filename] = vc

        # Process the video (load all frames for ROI analysis)
        print("Processing video with cv2...")
        meta_data = load_video_from_contents(vc, verbose=True)  # FIXME: use debug flag
        print("Video processing completed")

        first_frame = meta_data.get_first_frame()
        video_info = meta_data.info()

        current_video_data = meta_data
        print(f"Video uploaded and processed successfully. Video info: {video_info}")

        return JSONResponse(
            {
                "firstFrame": convert_frame_to_base64(first_frame),
                "videoInfo": video_info,
            }
        )

    except Exception as e:
        print(f"Failed to process uploaded video: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process uploaded video: {str(e)}"
        )


@app.post("/api/auto-roi")
async def auto_select_rois(request: dict):
    """Automatically select ROIs based on fluctuation map analysis.

    Example request body:
    {
        "video_path": "/path/to/your/video.mp4",
        "threshold_percentage": 99.0,
        "min_distance_percentage": 0.01,
        "n_clusters": 3
    }

    Example response:
    {
        "status": "completed",
        "rois": [
            {
                "id": 0,
                "coords": [x0, y0, x1, y1],
                "n_pixels": 400,
                "avg_intensity": [100.0, 98.2, ...],
                "center": [x, y],
                "fluctuation_strength": 15.5
            }
        ],
        "stats": {
            "n_rois": 3,
            "total_pixels": 1200,
            "coverage_percent": 5.2,
            "threshold_used": 15.5,
            "min_distance_used": 8
        }
    }
    """
    assert_video_selected()
    threshold_percentage = request.get("threshold_percentage", 99.0)
    min_distance_percentage = request.get("min_distance_percentage", 0.01)
    n_clusters = request.get("n_clusters", 3)

    try:
        # Process video
        meta_data = current_video_data
        frames = meta_data.frames

        # Compute bleaching for fluctuation map
        mean_intensity = meta_data.get_intensities()

        # Compute fluctuation map
        fluct_map = compute_fluctuation_map(frames, mean_intensity)

        # Calculate threshold and min_distance
        threshold = np.percentile(fluct_map, threshold_percentage)
        min_distance = int(frames.shape[2] * min_distance_percentage)

        # Perform automatic ROI selection
        roi_data = auto_select_rois_from_fluctuation(
            fluct_map,
            frames,
            threshold,
            min_distance,
            None,  # No workspace needed for API
        )

        if roi_data["rois"]:
            # Apply size filtering (10-90 percentile)
            roi_data = filter_rois_by_size(
                roi_data, min_percentile=50, max_percentile=90
            )

            # Cluster roi normalized intensity by similarity
            cluster_rois_by_similarity(
                roi_data, None, info["fps"], len(frames), n_clusters, None
            )

        return JSONResponse(
            {
                "status": "completed",
                "coords": [roi["coords"] for roi in roi_data["rois"]],
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Auto ROI selection failed: {str(e)}"
        )


@app.post("/api/run-analysis")
async def run_bleaching_analysis(request: dict):
    """Run bleaching analysis on a video file.

    Example request body:
    {
        "video_path": "/path/to/your/video.mp4"
    }

    Example response:
    {
        "status": "completed",
        "bleaching_data": {
            "timePoints": [0.0, 0.033, 0.067, ...], # in seconds
            "meanIntensity": [100.5, 98.2, 96.1, ...],
            "fitParams": {
                "exponential": [I0, tau], # in arbitrary units
                "inverse": [I0, tau] # in arbitrary units
            },
            "r2Scores": {
                "exponential": 0.985,
                "inverse": 0.992
            }
        }
    }
    """
    assert_video_selected()

    try:
        # Process video and compute bleaching
        meta_data = current_video_data
        mean_intensity = meta_data.get_intensities()

        print("Analysis bleaching:")
        print("video info: ", meta_data.info())

        # Create time points
        time_points = np.arange(len(mean_intensity)) / meta_data.fps

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
        result = {
            "status": "completed",
            "bleaching_data": {
                "timePoints": time_points.tolist(),
                "meanIntensity": mean_intensity.tolist(),
                "fitParams": fit_params,
                "r2Scores": r2_scores,
                "videoInfo": {
                    "width": meta_data.width,
                    "height": meta_data.height,
                    "fps": meta_data.fps,
                    "total_frames": meta_data.n_frames,
                },
            },
        }

        return JSONResponse(result)

    except Exception as e:
        print(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500)


@app.post("/api/update-fit-preference")
async def update_fit_preference(request: dict):
    """Update the user's fit preference (exponential vs inverse).

    Example request body:
    {
        "fitType": "exponential"  # or "inverse"
    }
    """
    fit_type = request.get("fit_type")

    if fit_type not in ["exponential", "inverse"]:
        raise HTTPException(status_code=400, detail="Invalid fit type")

    # In a real implementation, you might save this to a database
    # For now, we'll just log it
    return JSONResponse({"status": "updated", "fitType": fit_type})


@app.post("/api/get-roi-traces")
async def get_roi_traces(request: dict):
    """Get intensity traces for selected ROIs with optional EMA smoothing.

    Example request body:
    {
        "rois": [
            {"id": 1, "coords": [x0, y0, x1, y1]},
            {"id": 2, "coords": [x0, y0, x1, y1]}
        ],
        "smoothing": 0.1
    }
    """
    print(f"🔍 get_roi_traces called with request: {request}")

    assert_video_selected()
    rois = request.get("rois", [])
    smoothing_factor = request.get("smoothing", 0.0)

    print(f"🔍 Processing {len(rois)} ROIs with smoothing factor: {smoothing_factor}")

    if not rois:
        print("🔍 No ROIs provided, returning empty traces")
        return JSONResponse({"traces": []})

    try:
        # Get video data
        meta_data = current_video_data
        print(f"🔍 Video metadata: {meta_data.info() if meta_data else 'None'}")

        if not meta_data or meta_data.frames is None or meta_data.frames.size == 0:
            print("🔍 No video frames available")
            raise HTTPException(status_code=500, detail="No video frames available")

        frames = meta_data.frames
        n_frames = frames.shape[0]
        fps = meta_data.fps
        time_points = np.arange(n_frames) / fps

        print(f"🔍 Video info: {n_frames} frames, {fps} fps, shape: {frames.shape}")

        # Get frame dimensions
        height, width = frames.shape[1:]

        traces = []
        for roi in rois:
            roi_id = roi.get("id")
            coords = roi.get("coords")

            x0 = coords["x0"]
            y0 = coords["y0"]
            x1 = coords["x1"]
            y1 = coords["y1"]
            print(f"🔍 ROI {roi_id} coords: {x0}, {y0}, {x1}, {y1}")

            # Ensure coordinates are within bounds
            x0 = int(max(0, min(x0, width - 1)))
            y0 = int(max(0, min(y0, height - 1)))
            x1 = int(max(x0 + 1, min(x1, width)))
            y1 = int(max(y0 + 1, min(y1, height)))

            # Create mask for ROI region
            mask = np.zeros((height, width), dtype=bool)
            mask[y0:y1, x0:x1] = True

            # Extract mean intensity for each frame in the ROI
            intensity_trace = frames[:, mask].mean(axis=1)

            # Apply exponential moving average smoothing if requested
            if smoothing_factor > 0:
                intensity_trace = smooth_intensity_trace(
                    intensity_trace, smoothing_factor
                )

            traces.append(
                {
                    "roiId": roi_id,
                    "intensityTrace": intensity_trace.tolist(),
                    "timePoints": time_points.tolist(),
                }
            )

        print(f"🔍 Returning {len(traces)} traces")
        return JSONResponse({"traces": traces})

    except Exception as e:
        print(f"🔍 Error in get_roi_traces: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to get ROI traces: {str(e)}"
        )
