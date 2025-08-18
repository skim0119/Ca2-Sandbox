import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image


def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    for _ in range(n_frames):
        ret, frame = cap.read()
        if not ret:
            break
        if frame.ndim == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frames.append(frame.astype(np.float32))
    cap.release()
    frames = np.stack(frames, axis=0)
    info = {"n_frames": n_frames, "width": width, "height": height, "fps": fps}
    return frames, info


def get_first_frame(video_path):
    """Get the first frame of a video file as a base64 encoded image.

    Args:
        video_path (str): Path to the video file

    Returns:
        tuple: (base64_image_string, video_info_dict)
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    # Get video properties
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Read first frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError("Could not read first frame from video")

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

    # Video info
    video_info = {
        "width": width,
        "height": height,
        "fps": fps,
        "total_frames": n_frames,
    }

    return base64_image, video_info
