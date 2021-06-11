from dataclasses import dataclass
from typing import List, Dict

import numpy as np


@dataclass(init=False)
class TrackInfo:
    name: str
    sample_rate: int
    frame_size: int
    frame_size_padded: int
    frame_size_nyquist: int
    frame_size_resampling: int
    hop_size_factor: int
    hop_size_analysis: int
    hop_size_synthesis: int
    half_tone_steps_to_shift: int
    pitch_shift_factor: float
    time_stretch_ratio: float
    windowType: str
    normalize: bool

    def setup(self, zero_padding=False):
        self.frame_size = int(2 ** (np.round(np.log2(self.sample_rate / 20))))
        self.pitch_shift_factor = 2 ** (self.half_tone_steps_to_shift / 12)
        self.hop_size_synthesis = int(self.frame_size / self.hop_size_factor)
        self.hop_size_analysis = int(self.hop_size_synthesis / self.pitch_shift_factor)
        self.time_stretch_ratio = self.hop_size_synthesis / self.hop_size_analysis
        self.frame_size_resampling = int(np.floor(self.frame_size * self.hop_size_analysis / self.hop_size_synthesis))
        self.frame_size_padded = self.frame_size * 2 if zero_padding else self.frame_size
        self.frame_size_nyquist = int(self.frame_size_padded / 2 + 1)

    def folder_name(self) -> str:
        return "{name}_{shift:d}".format(name=self.name.replace(" ", "_"), shift=self.half_tone_steps_to_shift)

    def file_name(self, name: str, ext: str) -> str:
        return "{name}_{shift:d}.{ext}".format(name=name, shift=self.half_tone_steps_to_shift, ext=ext)


@dataclass(init=False)
class Result:
    samples: List[float]
    root_mean_squared_deviation: float
    processing_time: float
    realtime_ratio: float

    def __init__(self, samples: List[float], processing_time, sample_rate):
        self.samples = samples
        self.processing_time = processing_time
        self.realtime_ratio = processing_time / (len(samples) / sample_rate)


@dataclass(init=False)
class Track:
    info: TrackInfo
    base: List[float]
    reference: List[float]
    synthesized: Dict[str, Result]

    def __init__(self):
        self.synthesized = {}
