import copy
import os
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

from main.common import env
from main.common.track import TrackInfo, Track


def time_align_crop(info: TrackInfo, reference: List[float], transformed: List[float], skip_frame_count: int):
    skip_offset = skip_frame_count * info.frame_size
    transformed = transformed[skip_offset:]
    reference = reference[skip_offset:]

    align_offset = 0
    min_rmsd = 1
    for i in range(info.frame_size):
        rmsd = 0
        for j in range(0, info.frame_size):
            rmsd += (transformed[j] - reference[i + j]) ** 2
        rmsd = np.sqrt(rmsd / info.sample_rate)
        if rmsd < min_rmsd:
            min_rmsd = rmsd
            align_offset = i

    print("align offset: ", align_offset)

    length = (min(len(transformed), len(reference)) // info.frame_size - skip_frame_count) * info.frame_size
    transformed = transformed[align_offset:length + align_offset]
    reference = reference[:length]
    return reference, transformed


def get_squared_deviation(info: TrackInfo, window: List[float], reference: List[float], transformed: List[float]):
    phase_frame_pairs = []
    magnitude_frame_pairs = []
    for i in range(0, len(reference) - info.frame_size, info.hop_size_synthesis):
        reference_frame = np.fft.fft(reference[i:i + info.frame_size] * window)
        transformed_frame = np.fft.fft(transformed[i:i + info.frame_size] * window)
        phase_frame_pairs.append((np.angle(reference_frame), np.angle(transformed_frame)))
        mag_ref = abs(reference_frame)
        mag_tran = abs(transformed_frame)
        magnitude_frame_pairs.append((mag_ref / max(mag_ref), mag_tran / max(mag_tran)))
    return magnitude_frame_pairs, phase_frame_pairs


def get_rmsd(info: TrackInfo, frame_pairs: List[Tuple[List[float], List[float]]]):
    rmsd = 0.0
    for frame_pair in frame_pairs:
        for val_pair in zip(frame_pair[0], frame_pair[1]):
            rmsd += (val_pair[0] - val_pair[1]) ** 2
    return np.sqrt(rmsd / (len(frame_pairs) * info.frame_size))


def get_complex_frame(frame: List[float], window: List[float]):
    frame = frame * window
    frame_fft = np.fft.rfft(frame)
    return frame, abs(frame_fft), np.angle(frame_fft)


def generate_spectogram(info: TrackInfo, reference: List[float], transformed: List[float], key):
    result = (transformed - reference) ** 2
    plt.figure(figsize=(18, 8))

    cmap = copy.copy(plt.get_cmap("viridis"))
    vmin = 20 * np.log10(np.max(reference)) - 200
    cmap.set_under(color='k', alpha=None)

    plt.subplot(311)
    plt.specgram(reference, Fs=info.sample_rate, mode='magnitude',
                 vmin=vmin, vmax=0, cmap=cmap)
    plt.xlabel('Time')
    plt.ylabel('Frequency')

    plt.subplot(312)
    # vmin = 20 * np.log10(np.max(transformed)) - 200
    plt.specgram(transformed, Fs=info.sample_rate, mode='magnitude',
                 vmin=vmin, vmax=0, cmap=cmap)
    plt.xlabel('Time')
    plt.ylabel('Frequency')

    plt.subplot(313)
    # vmin = 20 * np.log10(np.max(result)) - 200
    plt.specgram(result, Fs=info.sample_rate, mode='magnitude',
                 vmin=vmin, vmax=0, cmap=cmap)
    plt.xlabel('Time')
    plt.ylabel('Frequency')
    path = env.get_resources_out_path(info.folder_name())
    if not os.path.exists(path): os.mkdir(path)
    plt.savefig(os.path.join(path, key + ".png"))

def evaluate(track: Track):
    window = list(signal.get_window(track.info.windowType, track.info.frame_size, True))
    print("root mean squared deviation:")
    for key in track.synthesized.keys():
        reference, transformed = time_align_crop(track.info, track.reference, track.synthesized[key].samples, 5)
        magnitude_frame_pairs, phase_frame_pairs = get_squared_deviation(track.info, window, reference, transformed)
        track.synthesized[key].root_mean_squared_deviation = get_rmsd(track.info, magnitude_frame_pairs)

        print(f"{key}: {track.synthesized[key].root_mean_squared_deviation}")
        plt.ioff()
        # generate_spectogram(track.info, reference, transformed, key)
    return track
