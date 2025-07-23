import numpy as np
from skimage import exposure
import cv2

def compute_fluctuation_map(frames, mean_intensity):
    n_frames = frames.shape[0]
    bleaching_trend = np.polyval(np.polyfit(np.arange(n_frames), mean_intensity, 2), np.arange(n_frames))
    corrected = frames - bleaching_trend[:, None, None]
    fluctuation_map = np.std(corrected, axis=0)
    norm_fluct = exposure.rescale_intensity(fluctuation_map, out_range=(0,255)).astype(np.uint8)
    overlay = cv2.applyColorMap(norm_fluct, cv2.COLORMAP_JET)
    first_frame = frames[0].astype(np.uint8)
    first_frame_rgb = cv2.cvtColor(first_frame, cv2.COLOR_GRAY2BGR)
    overlayed = cv2.addWeighted(first_frame_rgb, 0.6, overlay, 0.4, 0)
    return fluctuation_map, overlayed

def save_fluctuation_overlay(overlayed, out_path):
    cv2.imwrite(out_path, overlayed) 