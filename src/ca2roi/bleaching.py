import numpy as np
import pickle

def compute_bleaching(frames):
    return frames.mean(axis=(1,2))

def save_bleaching(mean_intensity, info, out_path):
    bleaching_info = dict(mean_intensity=mean_intensity, **info)
    with open(out_path, 'wb') as f:
        pickle.dump(bleaching_info, f) 