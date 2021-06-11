import abc

import numpy as np
from scipy import signal

from main.common.track import TrackInfo
from main.dsp.phase import PhaseShifter
from main.dsp.resample import Resampler


class SignalProcessor:
    """Base class for dsp algorithms"""

    def __init__(self, info: TrackInfo):
        self.info = info
        self.window = signal.get_window(self.info.windowType, info.frame_size, True)
        self.window_squared = self.window ** 2

    @abc.abstractmethod
    def transform(self, frame):
        return

    def pad(self, frame):
        return np.pad(frame, (0, int((self.info.frame_size_padded) / 2)), 'constant')

    def unpad(self, frame):
        return frame[0: self.info.frame_size]


class PitchShifter(SignalProcessor):
    """Pitch shifter algorithm container. Initialize with proper component configuration to get the desired effect"""

    def __init__(self, info: TrackInfo, phase_shifter: PhaseShifter, resampler: Resampler):
        """
        Initializes the pith shifter and its components
        :param info: information about the track and the desired pitch shift
        :param phase_shifter: the phase shift algorithm to be used
        :param resampler: the resampler to be used
        """
        super().__init__(info)
        self.phase_shifter = phase_shifter
        self.resampler = resampler

    def transform(self, frame):
        """
        Takes a time domain frame, converts it using fft, performs phase shift, performs ifft and resamples the frame
        :param frame: time domain frame
        :return: stretched and resampled time domain frame
        """
        frame = frame * self.window
        # print(len(frame))
        if self.info.frame_size != self.info.frame_size_padded: frame = self.pad(frame)
        # print(len(frame))
        # print(self.info.frame_size)
        # print(self.info.frame_size_padded)
        # frame = np.fft.fftshift(frame)
        frame_fft = np.fft.rfft(frame)
        phase_transformed = self.phase_shifter.process(frame_fft)
        frame_fft_transposed = (abs(frame_fft) * np.exp(1j * phase_transformed))
        frame_transposed = np.fft.irfft(frame_fft_transposed)
        # frame_transposed = np.fft.ifftshift(frame_transposed)
        if self.info.frame_size != self.info.frame_size_padded: frame_transposed = self.unpad(frame_transposed)
        frame_transposed = frame_transposed * self.window
        frame_resampled = self.resampler.process(frame_transposed)
        return frame_resampled, abs(frame_fft_transposed), phase_transformed


class TimeStretcher(SignalProcessor):
    """Time stretcher algorithm container. Initialize with proper component configuration to get the desired effect"""

    def __init__(self, info: TrackInfo, phase_shifter: PhaseShifter):
        """
        Initializes the pith shifter and its components
        :param info: information about the track and the desired pitch shift
        :param phase_shifter: the phase shift algorithm to be used
        """
        super().__init__(info)
        self.phase_shifter = phase_shifter

    def transform(self, frame):
        """
        Takes a time domain frame, converts it using fft, performs phase shift and performs ifft
        :param frame: time domain frame
        :return: stretched time domain frame
        """
        frame = frame * self.window
        if self.info.frame_size != self.info.frame_size_padded: frame = self.pad(frame)
        frame_fft = np.fft.rfft(frame)
        phase_transformed = self.phase_shifter.process(frame_fft)
        frame_fft_transposed = (abs(frame_fft) * np.exp(1j * phase_transformed))
        frame_transposed = np.fft.irfft(frame_fft_transposed)
        if self.info.frame_size != self.info.frame_size_padded: frame_transposed = self.unpad(frame_transposed)
        frame_transposed = frame_transposed * self.window
        return frame_transposed, abs(frame_fft_transposed), phase_transformed
