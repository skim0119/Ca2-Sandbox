import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
from dataclasses import dataclass

from tqdm import tqdm


@dataclass
class VideoMetadata:
    frames: np.ndarray
    first_frame: np.ndarray

    n_frames: int
    width: int
    height: int
    fps: float

    def info(self):
        return {
            "n_frames": self.n_frames,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
        }

    def get_first_frame(self):
        return self.first_frame

    @classmethod
    def from_video_path(cls, video_path, meta_data_only:bool = False, verbose:bool = False):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        print(f"Loading video: {video_path} with {n_frames} frames")

        if meta_data_only:
            ret, first_frame = cap.read()
            frames = np.empty((0, height, width), dtype=np.float32)
        else:
            frames_list = []
            for fidx in tqdm(range(n_frames)):
                ret, frame = cap.read()
                print(f"{frame.shape=}")
                if not ret:
                    break
                if fidx == 0:
                    first_frame = frame.copy()
                if frame.ndim == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frames_list.append(frame.astype(np.float32))
            frames = np.stack(frames_list, axis=0)
            
        cap.release()

        if verbose:
            print(f"Video metadata: {cls(frames=frames, first_frame=first_frame, n_frames=n_frames, width=width, height=height, fps=fps)}")

        return cls(
            frames=frames,
            first_frame=first_frame,
            n_frames=n_frames,
            width=width,
            height=height,
            fps=fps,
        )


def process_video(video_path, verbose:bool = False) -> VideoMetadata:
    """
    Load a video file and return the frames and video information.
    """

    meta_data = VideoMetadata.from_video_path(video_path, verbose=verbose)
    return meta_data


def process_video_metadata_only(video_path) -> VideoMetadata:
    """
    Load only video metadata and first frame (for upload endpoint).
    This is much faster as it doesn't load all frames into memory.
    """

    meta_data = VideoMetadata.from_video_path(video_path, meta_data_only=True)
    return meta_data


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
