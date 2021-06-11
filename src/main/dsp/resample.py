import abc
from typing import List

import librosa
import numpy as np

from main.common.track import TrackInfo


class Resampler:
    def __init__(self, info: TrackInfo):
        self.info = info

    @abc.abstractmethod
    def process(self, frame: List[float]) -> List[float]:
        return []


class LinearInterpolator(Resampler):
    """Based on DAFX Chapter 7.4.4 Block by block approach http://dafx.de/DAFX_Book_Page/index.html"""

    def __init__(self, info: TrackInfo):
        super().__init__(info)

        # prepare interpolation vectors
        # the goal is to get vectors that hold the frame sample indexes that will used for the resampling
        # multiplying the range with the frame size stretch factor ensures that the entire range of the
        # original frame is used
        self.resample_poc_vec = np.array(range(0, self.info.frame_size_resampling)) * (self.info.frame_size / self.info.frame_size_resampling)
        # round the elements down to get the 'left' index from the perfect resample position, which is most likely a float
        self.resample_index_vec_left = np.floor(self.resample_poc_vec).astype(int)
        # shift all values +1 to get the 'right' index from the perfect resample position
        self.resample_index_vec_right = self.resample_index_vec_left + 1
        # the difference between the pos vec and the left index vec returns the weight for the right index vec
        self.resample_weight_vec_right = self.resample_poc_vec - self.resample_index_vec_left
        # subtracting the left weights from 1 returns the weights for the left index vec and ensures that the resample sum
        # doesn't exceed unity
        self.resample_weight_vec_left = 1 - self.resample_weight_vec_right

    def process(self, frame: List[float]) -> List[float]:
        """
        Resamples the given time domain frame using the prepared index and weight vectors
        :param frame: the time domain frame to be resamples
        :return: returns the resamples frame of the length info.frame_size_resampling
        """
        frame = np.append(frame, [0])
        frame_resampled = \
            [frame[int(index)] for index in self.resample_index_vec_left] * self.resample_weight_vec_left + \
            [frame[int(index)] for index in self.resample_index_vec_right] * self.resample_weight_vec_right
        return frame_resampled


class LibrosaResampler(Resampler):

    def __init__(self, info: TrackInfo):
        super().__init__(info)

    def process(self, frame: List[float]) -> List[float]:
        """
        Resamples the given time domain frame using the prepared index and weight vectors
        :param frame: the time domain frame to be resamples
        :return: returns the resamples frame of the length info.frame_size_resampling
        """
        librosa.resample(frame, self.info.frame_size, self.info.frame_size_resampling)
        return librosa.resample(frame, self.info.frame_size, self.info.frame_size_resampling)
