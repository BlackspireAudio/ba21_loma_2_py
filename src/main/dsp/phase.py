import abc
import heapq
from dataclasses import dataclass
from typing import List

import numpy as np

from main.common import utils
from main.common.avg_queue import AvgQueue
from main.common.enums import TransientDetectionType, PhaseResetType
from main.common.movingmedian import MovingMedian
from main.common.track import TrackInfo


class PhaseShifter:
    """Base class for the various phase shifter algorithms"""

    def __init__(self, info: TrackInfo, transient_detection_mode: TransientDetectionType = TransientDetectionType.NONE,
                 phase_reset_type: PhaseResetType = PhaseResetType.FULL_RANGE):
        """
        Initializes the base class
        Stores the track info locally and calculates the expected phase delta for the hop and frame size
        :param info: A TrackInfo object providing information about the track and the transformation
        """
        self.rising_count = 0
        self.info = info
        self.last_magnitude = np.zeros(self.info.frame_size_nyquist)
        self.phase_delta_target = (2.0 * np.pi * self.info.hop_size_analysis) * np.array(range(0, self.info.frame_size_nyquist)) / self.info.frame_size_padded
        self.phase_analysis_prev = np.zeros(self.info.frame_size_nyquist)
        self.phase_synthesis = np.zeros(self.info.frame_size_nyquist)
        self.transient_prob_threshold = 0.35
        self.transient_prob_prev = 0
        self.transient_detection_mode = transient_detection_mode
        self.high_freq_mag_sum_last = 0
        self.high_freq_filter = MovingMedian(19, 85)
        self.high_freq_deriv_filter = MovingMedian(19, 90)
        self.high_freq_deriv_delta = 0
        self.max_mag_avg_queue = AvgQueue(19)
        # amplitude (root-power) ratio equivalent to 3 dB (10**(3/20)=10**0.15)
        # mag1 / mag2 = 10**0.15 ---> mag1 is 3 dB over mag2
        self.magnitude_ratio_3db = 10 ** 0.15
        self.transient_magnitude_min_factor = 10e-6

        self.phase_reset_type = phase_reset_type
        self.band_low = int(np.floor(150 * info.frame_size_padded / info.sample_rate))
        self.band_high = int(np.floor(1000 * info.frame_size_padded / info.sample_rate))
        self.mid_range = slice(0, self.info.frame_size_nyquist)

        self.frame_index = 0

    @abc.abstractmethod
    def process(self, frame_fft: List[complex]) -> List[float]:
        return []

    def high_frequency_transient_detection(self, current_magnitude):
        high_freq_mag_sum = 0.0
        transient_probability = 0.0
        # sum the magnitudes of all bins weighted by their center frequency
        for n in range(0, len(current_magnitude)):
            high_freq_mag_sum = high_freq_mag_sum + current_magnitude[n] * n

        high_freq_deriv = high_freq_mag_sum - self.high_freq_mag_sum_last
        self.high_freq_filter.put(high_freq_mag_sum)
        self.high_freq_deriv_filter.put(high_freq_deriv)
        high_freq_filtered = self.high_freq_filter.get()
        high_freq_deriv_filtered = self.high_freq_deriv_filter.get()
        self.high_freq_mag_sum_last = high_freq_mag_sum
        high_freq_deriv_delta = 0.0
        high_freq_excess = high_freq_mag_sum - high_freq_filtered

        if high_freq_excess > 0:
            # if current high frequency content is above the current median, the difference in gradiant to the median is calculated
            high_freq_deriv_delta = high_freq_deriv - high_freq_deriv_filtered

        if high_freq_deriv_delta < self.last_high_freq_deriv_delta:
            # if the current difference in gradient is smaller than that of the last frame the rising count is reset
            if self.rising_count > 3 and self.last_high_freq_deriv_delta > 0:
                # if the difference in gradient from the median has been rising for at least 3 frames, the current frame holds a transient
                transient_probability = 0.5
            self.rising_count = 0
        else:
            # while the difference in gradient is larger than that of the previous frame, we're on the rising slope before the transient
            self.rising_count = self.rising_count + 1
        self.last_high_freq_deriv_delta = high_freq_deriv_delta
        return transient_probability

    def percussive_transient_detection(self, current_magnitude):
        self.max_mag_avg_queue.push_pop(max(current_magnitude))
        zeroThresh = self.transient_magnitude_min_factor * self.max_mag_avg_queue.get_avg()

        count = 0
        nonZeroCount = 0

        for n in range(0, len(current_magnitude)):
            magnitude_increase_ratio = 0.0
            if self.last_magnitude[n] > zeroThresh:
                # calculate magnitude growth since last frame if last magnitude of current bin is non-zero
                magnitude_increase_ratio = current_magnitude[n] / self.last_magnitude[n]
            elif current_magnitude[n] > zeroThresh:
                # if last magnitude of current bin is below zero threshold but current magnitude is significant, default to 3dB ratio
                magnitude_increase_ratio = self.magnitude_ratio_3db
            # count significant magnitude increases
            if magnitude_increase_ratio >= self.magnitude_ratio_3db: count += 1
            # count significant magnitudes
            if current_magnitude[n] > zeroThresh: nonZeroCount += 1

        self.last_magnitude = current_magnitude
        if (nonZeroCount == 0):
            return 0
        # return the ratio of bins with significant magnitude and bins with significant magnitude which translates to the likelihood of the current frame being a transient
        # count is always smaller than nonZeroCount. The returned ratio therefore has the range [0, 1]
        # small difference between count and nonZeroCount indicate few significant bins without significant growth -> likely a transient
        return count / nonZeroCount

    def compound_transient_detection(self, current_magnitude):
        if self.transient_detection_mode.__eq__(TransientDetectionType.PERCUSSIVE.value):
            return self.percussive_transient_detection(current_magnitude)
        elif self.transient_detection_mode.__eq__(TransientDetectionType.COMPOUND):
            return max(self.percussive_transient_detection(current_magnitude), self.high_frequency_transient_detection(current_magnitude))
        elif self.transient_detection_mode.__eq__(TransientDetectionType.HIGH_FREQ):
            return self.high_frequency_transient_detection(current_magnitude)
        return 0

    def has_transient(self, magnitude):
        transient_prob = self.compound_transient_detection(magnitude)
        if transient_prob > self.transient_prob_prev and transient_prob > self.transient_prob_threshold:
            self.transient_prob_prev = transient_prob
            return True
        self.transient_prob_prev = transient_prob
        return False

    def phase_reset(self, phase):
        if self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED):
            self.phase_synthesis[0: self.band_low] = phase[0: self.band_low]
            self.phase_synthesis[self.band_high: self.info.frame_size_nyquist] = phase[self.band_high: self.info.frame_size_nyquist]
            return slice(self.band_low, self.band_high)
        else:
            self.phase_synthesis = phase
            return self.mid_range


class BasicPhaseShifter(PhaseShifter):
    """Based on DAFX Chapter 7.3.5 Phase unwrapping http://dafx.de/DAFX_Book_Page/index.html"""

    def __init__(self, info: TrackInfo, transient_detection_mode: TransientDetectionType = TransientDetectionType.NONE,
                 phase_reset_type: PhaseResetType = PhaseResetType.FULL_RANGE):
        """
        Initializes the class
        :param info: A TrackInfo object providing information about the track and the transformation
        """
        super().__init__(info, transient_detection_mode, phase_reset_type)

    def process(self, frame_fft: List[complex]):
        """
        Takes a frequency domain frame and uses the angle of the complex numbers to stretch the phase using basic horizontal phase propagation
        :param frame_fft: a frame in the frequency domain spectrum
        :return: the transformed phase for each bin
        """
        phase_analysis = np.angle(frame_fft)
        transient_detected = not self.transient_detection_mode.__eq__(TransientDetectionType.NONE) and self.has_transient(abs(frame_fft))
        mid_range = self.mid_range

        if transient_detected:
            mid_range = self.phase_reset(phase_analysis)

        if not transient_detected or self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED):
            phase_delta = self.phase_delta_target[mid_range] + utils.princarg(phase_analysis[mid_range] - self.phase_analysis_prev[mid_range] - self.phase_delta_target[mid_range])
            self.phase_synthesis[mid_range] = utils.princarg(phase_delta * self.info.time_stretch_ratio + self.phase_synthesis[mid_range])

        self.phase_analysis_prev = phase_analysis

        return self.phase_synthesis


class PhaseLockedIdentityShifter(PhaseShifter):
    """
    Based on Improved Phase Vocoder Time-Scale Modification of Audio Chapter III.C.1 Identity Phase Locking https://ieeexplore.ieee.org/document/759041
    and DAFX Chapter 7.4.3 Phase locked vocoder http://dafx.de/DAFX_Book_Page/index.html
    """

    def __init__(self, info: TrackInfo, transient_detection_mode: TransientDetectionType = TransientDetectionType.NONE,
                 phase_reset_type: PhaseResetType = PhaseResetType.FULL_RANGE):
        """
        Initializes the class
        :param info: A TrackInfo object providing information about the track and the transformation
        """
        super().__init__(info, transient_detection_mode, phase_reset_type)
        self.peak_shadow = 1

    def get_magnitude_peaks(self, magnitude: List[float], peak_shadow: int) -> List[float]:
        """
        Determines local maxima in the provided list of magnitudes that overlook at least +-peak_shadow magnitudes to each side
        :param magnitude: the list of magnitudes for which maxima are required
        :param peak_shadow: the number of magnitudes to the left and right that need to be smaller for a peak to be selected
        :return: a list of indexes where local maxima can be found in the provided list of magnitudes
        """
        magnitude_peaks = []
        i = peak_shadow
        while i < len(magnitude) - peak_shadow:
            if magnitude[i] == 0:
                i += 1
                continue
            is_peak = True
            for j in range(-peak_shadow, peak_shadow + 1):
                if magnitude[i] < magnitude[i + j]:
                    is_peak = False
                    break
            if is_peak:
                magnitude_peaks.append(i)
                i += peak_shadow
            i += 1
        return magnitude_peaks

    def get_phase_rotation(self, phase_analysis, peak_index: int):
        """
        Calculates the expected phase shift using the average bin index between the related peaks from the current and last frame
        Calculates and returns the required phase rotation in relation to the measured phase of this frame
        :param phase_analysis: the measured phase of the current frame
        :param peak_index_last: the bin index of the related peak from the last frame
        :param peak_index: the bin index of the selected peak from the current frame
        :return: the required phase rotation in relation to the measured phase of this frame
        """
        peak_phase_delta = self.phase_delta_target[peak_index] + utils.princarg(
            phase_analysis[peak_index] - self.phase_analysis_prev[peak_index] - self.phase_delta_target[peak_index])
        peak_phase_target = utils.princarg(self.phase_synthesis[peak_index] + peak_phase_delta * self.info.time_stretch_ratio)
        return utils.princarg(peak_phase_target - phase_analysis[peak_index])

    def get_upper_bounds(self, magnitude_peaks, magnitude, peak_index):
        if len(magnitude_peaks) <= 1 or peak_index == magnitude_peaks[-1]: return self.info.frame_size_nyquist

        upper_bound_bin_index = peak_index
        while upper_bound_bin_index < self.info.frame_size_nyquist - 1 and magnitude[upper_bound_bin_index] > magnitude[upper_bound_bin_index + 1]:
            upper_bound_bin_index += 1
        return upper_bound_bin_index

    def process(self, frame_fft: List[complex]) -> List[float]:
        """
        Takes a frequency domain frame and uses the angle of the complex numbers to stretch the phase using basic horizontal phase propagation and static vertical phase propagation
        :param frame_fft: a frame in the frequency domain spectrum
        :return: the transformed phase for each bin
        """
        phase_analysis = np.angle(frame_fft)
        magnitude = abs(frame_fft)
        phase_synthesis_temp = np.zeros(self.info.frame_size_nyquist)
        mid_range = self.mid_range
        transient_detected = not self.transient_detection_mode.__eq__(TransientDetectionType.NONE) and self.has_transient(magnitude)

        if transient_detected:
            mid_range = self.phase_reset(phase_analysis)

        if not transient_detected or self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED):
            magnitude_peaks = self.get_magnitude_peaks(magnitude[mid_range], self.peak_shadow)
            if len(magnitude_peaks) > 0:
                # if the current frame has at least 1 peak, horizontal and vertical phase propagation is performed
                upper_bound_bin_index = 0
                for peak_number_current in range(0, len(magnitude_peaks)):
                    peak_index = magnitude_peaks[peak_number_current]
                    peak_phase_rotation = self.get_phase_rotation(phase_analysis, peak_index)
                    lower_bound_bin_index = upper_bound_bin_index
                    upper_bound_bin_index = self.get_upper_bounds(magnitude_peaks, magnitude, peak_index)
                    if transient_detected and self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED):
                        if lower_bound_bin_index < self.band_low: lower_bound_bin_index = self.band_low
                        if upper_bound_bin_index > self.band_high: upper_bound_bin_index = self.band_high
                    phase_synthesis_temp[lower_bound_bin_index:upper_bound_bin_index] = utils.princarg(phase_analysis[lower_bound_bin_index:upper_bound_bin_index] + peak_phase_rotation)

                self.phase_synthesis[mid_range] = phase_synthesis_temp[mid_range]
            else:
                # if either the current or the last frame has no peak, basic horizontal phase propagation is performed
                phase_delta = self.phase_delta_target[mid_range] + utils.princarg(phase_analysis[mid_range] - self.phase_analysis_prev[mid_range] - self.phase_delta_target[mid_range])
                self.phase_synthesis[mid_range] = utils.princarg(self.phase_synthesis[mid_range] + phase_delta * self.info.time_stretch_ratio)

        # cache data for the processing of the next frame
        self.phase_analysis_prev = np.copy(phase_analysis)
        self.frame_index += 1

        return self.phase_synthesis


class PhaseLockedScaledShifter(PhaseShifter):
    """
    Based on Improved Phase Vocoder Time-Scale Modification of Audio Chapter III.C.2 Scaled Phase Locking https://ieeexplore.ieee.org/document/759041
    and DAFX Chapter 7.4.3 Phase locked vocoder http://dafx.de/DAFX_Book_Page/index.html
    """

    def __init__(self, info: TrackInfo, transient_detection_mode: TransientDetectionType = TransientDetectionType.NONE,
                 phase_reset_type: PhaseResetType = PhaseResetType.FULL_RANGE, scale_factor=1):
        """
        Initializes the class
        :param info: A TrackInfo object providing information about the track and the transformation
        """
        super().__init__(info, transient_detection_mode, phase_reset_type)

        self.magnitude_peaks_prev = []
        self.peak_shadow = 1
        self.scale_factor = scale_factor

    def get_magnitude_peaks(self, magnitude: List[float], peak_shadow: int) -> List[float]:
        """
        Determines local maxima in the provided list of magnitudes that overlook at least +-peak_shadow magnitudes to each side
        :param magnitude: the list of magnitudes for which maxima are required
        :param peak_shadow: the number of magnitudes to the left and right that need to be smaller for a peak to be selected
        :return: a list of indexes where local maxima can be found in the provided list of magnitudes
        """
        magnitude_peaks = []
        i = peak_shadow
        while i < self.info.frame_size_nyquist - peak_shadow:
            if magnitude[i] == 0:
                i += 1
                continue
            is_peak = True
            for j in range(-peak_shadow, peak_shadow + 1):
                if magnitude[i] < magnitude[i + j]:
                    is_peak = False
                    break
            if is_peak:
                magnitude_peaks.append(i)
                i += peak_shadow
            i += 1
        return magnitude_peaks

    def get_related_peak(self, peak_number_prev, peak_index_current):
        """
        Selects the next closest peak index from the last frame to the given peak index from the current frame
        :param peak_number_prev: the number (not the index) of last frames peaks. This number will be increased until the corresponding index has minimal distance from peak_index_current
        :param peak_index_current: the bin index of the current frames peak for which a related peak from the last frame is required
        :return: the number and the bin index of the last frames peak that is the closest to the given peak index of the current frame
        """
        while peak_number_prev < len(self.magnitude_peaks_prev) - 1 \
                and abs(peak_index_current - self.magnitude_peaks_prev[peak_number_prev + 1]) < abs(peak_index_current - self.magnitude_peaks_prev[peak_number_prev]):
            peak_number_prev += 1

        return peak_number_prev, self.magnitude_peaks_prev[peak_number_prev]

    def get_peak_synthesis_phase(self, phase_analysis_current, peak_index_last: int, peak_index_current: int):
        """
        Calculates the expected phase shift using the average bin index between the related peaks from the current and last frame
        Calculates and returns the required phase rotation in relation to the measured phase of this frame
        :param phase_analysis_current: the measured phase of the current frame
        :param peak_index_last: the bin index of the related peak from the last frame
        :param peak_index_current: the bin index of the selected peak from the current frame
        :return: the required phase rotation in relation to the measured phase of this frame
        """
        peak_index_average = (peak_index_current + peak_index_last) / 2.0
        peak_phase_delta_expected = 2 * np.pi * self.info.hop_size_analysis * peak_index_average / self.info.frame_size_padded
        peak_phase_delta = peak_phase_delta_expected + utils.princarg(phase_analysis_current[peak_index_current] - self.phase_analysis_prev[peak_index_last] - peak_phase_delta_expected)
        peak_analysis_phase_unwrapped = self.phase_analysis_prev[peak_index_current] + peak_phase_delta
        return self.phase_synthesis[peak_index_current] + peak_phase_delta * self.info.time_stretch_ratio, peak_analysis_phase_unwrapped

    def get_upper_bounds(self, magnitude_peaks_current, magnitude_current, peak_index_current):
        if len(magnitude_peaks_current) <= 1 or peak_index_current == magnitude_peaks_current[-1]: return self.info.frame_size_nyquist

        upper_bound_bin_index = peak_index_current
        while upper_bound_bin_index < self.info.frame_size_nyquist - 1 and magnitude_current[upper_bound_bin_index] > magnitude_current[upper_bound_bin_index + 1]:
            upper_bound_bin_index += 1
        return upper_bound_bin_index

    def process(self, frame_fft: List[complex]) -> List[float]:
        """
        Takes a frequency domain frame and uses the angle of the complex numbers to stretch the phase using basic horizontal phase propagation and static vertical phase propagation
        :param frame_fft: a frame in the frequency domain spectrum
        :return: the transformed phase for each bin
        """
        phase_analysis = np.angle(frame_fft)
        magnitude = abs(frame_fft)
        magnitude_peaks_current = self.get_magnitude_peaks(magnitude, self.peak_shadow)
        phase_synthesis_temp = np.zeros(self.info.frame_size_nyquist)

        mid_range = self.mid_range
        transient_detected = not self.transient_detection_mode.__eq__(TransientDetectionType.NONE) and self.has_transient(magnitude)

        if transient_detected:
            mid_range = self.phase_reset(phase_analysis)

        if not transient_detected or self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED):
            if len(magnitude_peaks_current) > 0 and len(self.magnitude_peaks_prev) > 0:
                # if both the current and the last frame have at least 1 peak, horizontal and vertical phase propagation is performed
                peak_number_prev = 0
                upper_bound_bin_index = 0
                for peak_number_current in range(0, len(magnitude_peaks_current)):
                    peak_index_current = magnitude_peaks_current[peak_number_current]
                    peak_number_prev, peak_index_last = self.get_related_peak(peak_number_prev, peak_index_current)
                    if transient_detected and self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED) and not self.band_low <= peak_index_current < self.band_high: continue
                    peak_synthesis_phase, peak_analysis_phase_unwrapped = self.get_peak_synthesis_phase(phase_analysis, peak_index_last, peak_index_current)
                    lower_bound_bin_index = upper_bound_bin_index
                    upper_bound_bin_index = self.get_upper_bounds(magnitude_peaks_current, magnitude, peak_index_current)
                    if transient_detected and self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED):
                        if lower_bound_bin_index < self.band_low: lower_bound_bin_index = self.band_low
                        if upper_bound_bin_index > self.band_high: upper_bound_bin_index = self.band_high
                    bounds = slice(lower_bound_bin_index, upper_bound_bin_index)
                    phase_analysis_unwrapped = self.phase_analysis_prev[bounds] + self.phase_delta_target[bounds] + utils.princarg(phase_analysis[bounds] - self.phase_analysis_prev[bounds] - self.phase_delta_target[bounds])
                    phase_synthesis_temp[bounds] = peak_synthesis_phase + self.scale_factor * (phase_analysis_unwrapped - peak_analysis_phase_unwrapped)

                self.phase_synthesis[mid_range] = phase_synthesis_temp[mid_range]
            else:
                # if either the current or the last frame has no peak, basic horizontal phase propagation is performed
                phase_delta = self.phase_delta_target[mid_range] + utils.princarg(phase_analysis[mid_range] - self.phase_analysis_prev[mid_range] - self.phase_delta_target[mid_range])
                self.phase_synthesis[mid_range] = self.phase_synthesis[mid_range] + phase_delta * self.info.time_stretch_ratio

        # cache data for the processing of the next frame
        self.phase_analysis_prev = np.copy(phase_analysis)
        self.magnitude_peaks_prev = np.copy(magnitude_peaks_current)
        self.frame_index += 1

        return self.phase_synthesis


class PhaseLaminarShifter(PhaseShifter):
    """Based on Rubberband Source Code StretcherProcess.cpp Method: ModifyChunk https://breakfastquay.com/rubberband/"""

    def __init__(self, info: TrackInfo, transient_detection_mode: TransientDetectionType = TransientDetectionType.NONE,
                 phase_reset_type: PhaseResetType = PhaseResetType.FULL_RANGE):
        """
        Initializes the class
        :param info: A TrackInfo object providing information about the track and the transformation
        """
        super().__init__(info, transient_detection_mode, phase_reset_type)

        self.frame_index = 0
        self.freq_low = 600
        self.freq_mid = 1200
        self.freq_high = 12000
        stretch_deviation = info.time_stretch_ratio - 1
        rf0 = 600 + (600 * 2 * stretch_deviation ** 3)
        freq_mid_ratio = self.freq_mid / self.freq_low
        freq_high_ratio = self.freq_high / self.freq_low
        self.freq_low = max(self.freq_low, rf0)
        self.freq_mid = self.freq_low * freq_mid_ratio
        self.freq_high = self.freq_low * freq_high_ratio
        self.limit_low = np.floor(self.freq_low * info.frame_size_padded / info.sample_rate)
        self.limit_mid = np.floor(self.freq_mid * info.frame_size_padded / info.sample_rate)
        self.limit_high = np.floor(self.freq_high * info.frame_size_padded / info.sample_rate)
        self.inherit_distance_max = 8
        self.phase_deviation_prev = np.zeros(info.frame_size_nyquist)
        self.lookback_vertical = -1

    def process(self, frame_fft: List[complex]) -> List[float]:
        """
        Takes a frequency domain frame and uses the angle of the complex numbers to stretch the phase using basic horizontal phase propagation and static vertical phase propagation
        :param frame_fft: a frame in the frequency domain spectrum
        :return: the transformed phase for each bin
        """
        phase_analysis = np.angle(frame_fft)
        magnitude_current = abs(frame_fft)

        mid_range = self.mid_range
        transient_detected = not self.transient_detection_mode.__eq__(TransientDetectionType.NONE) and self.has_transient(magnitude_current)
        if transient_detected:
            mid_range = self.phase_reset(phase_analysis)

        if not transient_detected or self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED):
            inherit_count = 0
            inherit_count_acc = 0
            for i in range(0, self.info.frame_size_nyquist)[mid_range]:
                if i <= self.limit_low:
                    inherit_count_max = 0
                elif i <= self.limit_mid:
                    inherit_count_max = 1
                elif i <= self.limit_high:
                    inherit_count_max = 3
                else:
                    inherit_count_max = self.inherit_distance_max

                phase_deviation = utils.princarg(phase_analysis[i] - self.phase_analysis_prev[i] - self.phase_delta_target[i])
                phase_deviation_delta = abs(phase_deviation - self.phase_deviation_prev[i])
                phase_deviation_delta_growing = phase_deviation > self.phase_deviation_prev[i]
                inherit = False
                if inherit_count > inherit_count_max or i == 0:
                    inherit = False
                elif self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED) and (i == self.band_low or i == self.band_high):
                    inherit = False
                elif phase_deviation_delta > phase_deviation_delta_prev and phase_deviation_delta_growing == phase_deviation_delta_growing_prev:
                    inherit = True

                phase_delta = utils.princarg(self.info.time_stretch_ratio * (self.phase_delta_target[i] + phase_deviation))
                if inherit:
                    inherited = utils.princarg(self.phase_synthesis[i + self.lookback_vertical] - phase_analysis[i + self.lookback_vertical])
                    phase_delta_inherited = (phase_delta * inherit_count + inherited * (self.inherit_distance_max - inherit_count)) / self.inherit_distance_max
                    self.phase_synthesis[i] = phase_analysis[i] + phase_delta_inherited
                    inherit_count_acc += inherit_count
                    inherit_count += 1
                else:
                    self.phase_synthesis[i] = self.phase_synthesis[i] + phase_delta
                    inherit_count = 0

                phase_deviation_delta_prev = phase_deviation_delta
                phase_deviation_delta_growing_prev = phase_deviation_delta_growing
                self.phase_deviation_prev[i] = phase_deviation

        self.phase_synthesis = self.phase_synthesis
        self.phase_analysis_prev = np.copy(phase_analysis)
        self.frame_index += 1

        return self.phase_synthesis


class PhaseLockedDynamicShifter(PhaseShifter):
    """Based on Phase Vocoder Done Right pseudo code https://www.researchgate.net/publication/319503719_Phase_Vocoder_Done_Right"""

    def __init__(self, info: TrackInfo, transient_detection_mode: TransientDetectionType = TransientDetectionType.NONE,
                 phase_reset_type: PhaseResetType = PhaseResetType.FULL_RANGE, magnitude_min_factor=10 ** -6):
        super().__init__(info, transient_detection_mode, phase_reset_type)

        self.magnitude_min_factor = magnitude_min_factor
        self.max_magnitude = 0
        self.magnitude_prev = np.zeros(self.info.frame_size_nyquist)
        self.phase_delta_prev = np.zeros(self.info.frame_size_nyquist)

    def process(self, frame_fft: List[complex]) -> List[float]:
        magnitude = abs(frame_fft)
        # get imaginary values from fft
        phase_analysis = np.angle(frame_fft)

        # calculate the diff between last and current phase vector)
        phase_delta = self.phase_delta_target + utils.princarg(phase_analysis - self.phase_analysis_prev - self.phase_delta_target)
        phase_delta = phase_delta * self.info.time_stretch_ratio

        mid_range = self.mid_range
        transient_detected = not self.transient_detection_mode.__eq__(TransientDetectionType.NONE) and self.has_transient(magnitude)
        if transient_detected:
            mid_range = self.phase_reset(phase_analysis)

        if not transient_detected or self.phase_reset_type.__eq__(PhaseResetType.BAND_LIMITED):
            self.max_magnitude = max(max(magnitude), self.max_magnitude)
            min_magnitude = self.magnitude_min_factor * self.max_magnitude

            significant_magnitudes = {i: magnitude[i] for i in range(0, self.info.frame_size_nyquist)[mid_range] if magnitude[i] > min_magnitude}
            max_heap = [HeapBin(i, -1, self.magnitude_prev[i], 0) for i in significant_magnitudes.keys()]
            heapq.heapify(max_heap)

            # perform simple horizontal phase propagation for bins with insignificant magnitude
            for i in range(0, self.info.frame_size_nyquist)[mid_range]:
                if i not in significant_magnitudes.keys():
                    self.phase_synthesis[i] = self.phase_synthesis[i] + phase_delta[i]

            while len(significant_magnitudes) > 0 and len(max_heap) > 0:
                max_bin = heapq.heappop(max_heap)
                bin_index = max_bin.bin_index
                time_index = max_bin.time_index
                if time_index < 0 and bin_index in significant_magnitudes.keys():
                    # bin has been taken from the last frame and horizontal phase propagation (using backwards phase time derivative and trapezoidal integration) is needed
                    self.phase_synthesis[bin_index] = self.phase_synthesis[bin_index] + (self.phase_delta_prev[bin_index] + phase_delta[bin_index]) / 2
                    # add the current bin of the current frame to the heap for further processing
                    heapq.heappush(max_heap, HeapBin(bin_index, 0, significant_magnitudes.get(bin_index), utils.princarg(self.phase_synthesis[bin_index] - phase_analysis[bin_index])))
                    # remove the processed bin from the set
                    significant_magnitudes.pop(bin_index)

                if time_index >= 0:
                    # the bin is from the current frame and vertical phase propagation (potentially in both directions) is needed
                    for bin_index_other in (bin_index - 1, bin_index + 1):
                        # check if the surrounding two bins have significant magnitudes
                        if bin_index_other in significant_magnitudes.keys():
                            self.phase_synthesis[bin_index_other] = phase_analysis[bin_index_other] + max_bin.phase_rotation
                            # add the next / prev bin to the heap for further processing
                            heapq.heappush(max_heap, HeapBin(bin_index_other, 0, magnitude[bin_index_other], max_bin.phase_rotation))
                            # remove the processed bin from the set
                            significant_magnitudes.pop(bin_index_other)

        self.phase_analysis_prev = np.copy(phase_analysis)
        self.phase_delta_prev = np.copy(phase_delta)
        self.magnitude_prev = np.copy(magnitude)
        self.frame_index += 1

        return self.phase_synthesis


@dataclass
class HeapBin:
    bin_index: int
    time_index: int
    magnitude: float
    phase_rotation: float

    def __lt__(self, other): return self.magnitude > other.magnitude

    def __eq__(self, other): return self.magnitude == other.magnitude

    def __str__(self): return str(self.magnitude)
