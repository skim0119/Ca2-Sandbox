from typing import Iterator
import os
from pathlib import Path
import tempfile
import base64
from dataclasses import dataclass, field
import logging

import cv2
import numpy as np
from io import BytesIO
from PIL import Image

from tqdm import tqdm

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    path: str
    first_frame: np.ndarray

    n_frames: int
    width: int
    height: int
    fps: float

    frames_loaded: bool = False
    frames: np.ndarray = field(init=False)

    def info(self):
        return {
            "n_frames": self.n_frames,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
        }

    def get_first_frame(self):
        return self.first_frame

    def load_frames(self):
        if self.frames_loaded:
            return
        self.frames = np.empty((self.n_frames, self.height, self.width), dtype=np.uint8)
        cap = cv2.VideoCapture(self.path)
        for fidx in tqdm(range(self.n_frames)):
            ret, frame = cap.read()
            if not ret:
                break
            if frame.ndim == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.frames[fidx] = frame
        cap.release()
        self.frames_loaded = True

    @classmethod
    def from_video_path(cls, video_path, verbose:bool = False):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        logger.info(f"Loading video: {video_path} with {n_frames} frames")

        ret, first_frame = cap.read()
        assert ret, "Failed to read first frame"
        cap.release()

        obj = cls(
            path=video_path,
            first_frame=first_frame,
            n_frames=n_frames,
            width=width,
            height=height,
            fps=fps,
        )
        obj.load_frames()
        if verbose:
            print(f"Video metadata: {obj.info()}")
        return obj

    def get_intensities(self):
        print(f"{self.frames.shape=}")
        return self.frames.mean(axis=(1, 2))

class VideoContentsHandle:
    def __init__(self, filename:str, content:bytes):
        # Create a temporary file
        print(f"File content read, size: {len(content)} bytes")

        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix)
        self.temp_file.write(content)
        self.temp_file.flush()  # Ensure content is written to disk
        self.temp_file_path = self.temp_file.name

    def __del__(self):
        """Cleanup: close and delete the temporary file when object is destroyed."""
        try:
            if hasattr(self, 'temp_file') and self.temp_file:
                self.temp_file.close()
        except Exception:
            pass
        try:
            if os.path.exists(self.temp_file_path):
                os.remove(self.temp_file_path)
                logger.info(f"Temporary file {self.temp_file_path} deleted.")
        except Exception as e:
            logger.error(f"Error deleting temporary file {self.temp_file_path}: {e}")

def load_video_from_path(video_path, verbose:bool = False) -> VideoMetadata:
    """
    Load a video file and return the frames and video information.
    """

    meta_data = VideoMetadata.from_video_path(video_path, verbose=verbose)
    return meta_data

def load_video_from_contents(vc: VideoContentsHandle, verbose:bool = False) -> VideoMetadata:
    meta_data = VideoMetadata.from_video_path(vc.temp_file_path, verbose=verbose)
    return meta_data

# Functions


def get_first_frame(video_path) -> np.ndarray:
    meta_data = VideoMetadata.from_video_path(video_path)
    return meta_data.get_first_frame()


def highlight_rois(frame, rois):
    for roi in rois:
        x0, y0, x1, y1 = roi
        cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 0, 255), 2)
    return frame


def convert_frame_to_base64(frame):
    # Convert BGR to RGB (OpenCV uses BGR, PIL uses RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to PIL Image
    pil_image = Image.fromarray(frame_rgb)

    # Convert to base64
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    # Create data URL
    base64_image = f"data:image/png;base64,{img_str}"
    return base64_image
