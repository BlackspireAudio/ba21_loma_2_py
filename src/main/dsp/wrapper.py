import abc
from typing import List

import numpy as np

from main.common.track import Track
from main.dsp.transform import SignalProcessor


class Wrapper:
    """
    Base class for dsp algorithm wrappers
    Responsible for splitting data into processable chunks and piecing them back together
    Provides utility functions like padding and normalizing
    """

    def __init__(self, dsp: SignalProcessor):
        self.dsp = dsp

    @abc.abstractmethod
    def process(self, track: Track):
        return

    def setup(self, samples: List[float]):
        samples = self.pad(samples, self.dsp.info.frame_size)
        # make result array long enough to be able to hold up to time stretch factor 2
        synthesis_samples = np.zeros(len(samples) * 2)
        return samples, synthesis_samples

    def post_processing(self, samples: List[float], target_length: int):
        samples = self.unpad(samples, self.dsp.info.frame_size, target_length)
        samples = self.ola_signal_rescaling(samples)
        return samples

    def pad(self, samples, frame_size):
        samples = np.concatenate((
            list(reversed(np.negative(samples[:frame_size]))),
            samples,
            list(reversed(np.negative(samples[-frame_size:])))
        ))
        return samples

    def unpad(self, samples: List[float], frame_size: int, target_length: int):
        return samples[frame_size: target_length + frame_size]

    def ola_signal_rescaling(self, samples: List[float]):
        rescale_factor = sum(self.dsp.window_squared) / self.dsp.info.hop_size_synthesis
        return samples / max(rescale_factor, max(samples))

    def normalize(self, frame_in, frame_out):
        frame_in_windowed = frame_in * self.dsp.window_squared
        rms_in = np.sqrt(sum(np.power(frame_in_windowed, 2)) / len(frame_in))
        rms_out = np.sqrt(sum(np.power(frame_out, 2)) / len(frame_out))
        return frame_out * (rms_in / rms_out)

class PitchShiftWrapper(Wrapper):
    """Wrapper for a pitch shift algorithm configuration"""

    def process(self, track: Track):
        """
        Splits the samples into frames using the analysis hop size and pieces the stretched and resampled frames back together with the analysis hop size to preserve the song duration
        :param samples: a list of samples of the type float representing the time domain of the song
        :return: Pith shifted samples in a list of the same length as the parameter samples
        """
        samples = track.base
        samples_padded, synthesis_samples = self.setup(samples)
        for a in range(0, len(samples_padded) - self.dsp.info.frame_size, self.dsp.info.hop_size_analysis):
            frame = samples_padded[a:a + self.dsp.info.frame_size]
            frame_transformed, temp2, _ = self.dsp.transform(frame)
            if self.dsp.info.normalize: frame_transformed = self.normalize(frame, frame_transformed)
            synthesis_samples[a:a + len(frame_transformed)] = synthesis_samples[a:a + len(frame_transformed)] + frame_transformed

        return self.post_processing(synthesis_samples, len(track.base))


class TimeStretchWrapper(Wrapper):
    """Wrapper for a time stretch algorithm configuration"""

    def process(self, track: Track):
        """
        Splits the samples into frames using the analysis hop size and pieces the stretched frames back together with the synthesis hop size changing the song length based on the stretch factor
        :param samples: a list of samples of the type float representing the time domain of the song
        :return: time stretched samples in a list of the length len(samples) * time_stretch_ratio
        """
        samples = track.base
        samples_padded, synthesis_samples = self.setup(samples)
        s = 0
        for a in range(0, len(samples) - self.dsp.info.frame_size, self.dsp.info.hop_size_analysis):
            frame = samples[a:a + self.dsp.info.frame_size]
            frame_transformed, _, _ = self.dsp.transform(frame)
            if self.dsp.info.normalize: frame_transformed = self.normalize(frame, frame_transformed)
            length = len(frame_transformed)
            synthesis_samples[s:s + length] = synthesis_samples[s:s + length] + frame_transformed
            s += self.dsp.info.hop_size_synthesis

        return self.post_processing(synthesis_samples, int(len(track.base) * self.dsp.info.time_stretch_ratio))
