import dsp.source as source
from controller import Controller
from main.common.enums import WindowType
from main.dsp.phase import *
from main.dsp.resample import *
from main.dsp.transform import *

configs = {
    # # Based on DAFX Chapter 7.4.4 Block by block approach http://dafx.de/DAFX_Book_Page/index.html
    # "ps-pv-base": lambda info: PitchShifter(info, BasicPhaseShifter(info), LinearInterpolator(info)),
    # "ps-pv-base-tp-full": lambda info: PitchShifter(info, BasicPhaseShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-base-tp-limit": lambda info: PitchShifter(info, BasicPhaseShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    # "ps-pv-base-tc-full": lambda info: PitchShifter(info, BasicPhaseShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-base-tc-limit": lambda info: PitchShifter(info, BasicPhaseShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    # "ps-pv-base-th-full": lambda info: PitchShifter(info, BasicPhaseShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-base-th-limit": lambda info: PitchShifter(info, BasicPhaseShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    #
    # # Based on Improved Phase Vocoder Time-Scale Modification of Audio Chapter III.C.1 Identity Phase Locking https://ieeexplore.ieee.org/document/759041
    # "ps-pv-lock-id": lambda info: PitchShifter(info, PhaseLockedIdentityShifter(info), LinearInterpolator(info)),
    # "ps-pv-lock-id-tp-full": lambda info: PitchShifter(info, PhaseLockedIdentityShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-lock-id-tp-limit": lambda info: PitchShifter(info, PhaseLockedIdentityShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    # "ps-pv-lock-id-tc-full": lambda info: PitchShifter(info, PhaseLockedIdentityShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-lock-id-tc-limit": lambda info: PitchShifter(info, PhaseLockedIdentityShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    # "ps-pv-lock-id-th-full": lambda info: PitchShifter(info, PhaseLockedIdentityShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-lock-id-th-limit": lambda info: PitchShifter(info, PhaseLockedIdentityShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    #
    # # Based on Improved Phase Vocoder Time-Scale Modification of Audio Chapter III.C.2 Scaled Phase Locking https://ieeexplore.ieee.org/document/759041
    # "ps-pv-lock-sc-1": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, scale_factor=1), LinearInterpolator(info)),
    # "ps-pv-lock-sc-1-tp-full": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.FULL_RANGE, scale_factor=1), LinearInterpolator(info)),
    # "ps-pv-lock-sc-1-tp-limit": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.BAND_LIMITED, scale_factor=1), LinearInterpolator(info)),
    # "ps-pv-lock-sc-1-tc-full": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.FULL_RANGE, scale_factor=1), LinearInterpolator(info)),
    "ps-pv-lock-sc-1-tc-limit": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.BAND_LIMITED, scale_factor=1), LinearInterpolator(info)),
    # "ps-pv-lock-sc-1-th-full": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.FULL_RANGE, scale_factor=1), LinearInterpolator(info)),
    # "ps-pv-lock-sc-1-th-limit": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.BAND_LIMITED, scale_factor=1), LinearInterpolator(info)),
    # "ps-pv-lock-sc-a": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, scale_factor=info.time_stretch_ratio), LinearInterpolator(info)),
    # "ps-pv-lock-sc-23a3": lambda info: PitchShifter(info, PhaseLockedScaledShifter(info, scale_factor=2 / 3 + info.time_stretch_ratio / 3), LinearInterpolator(info)),
    #
    # # Based on Rubberband Source Code StrechterProcess.cpp Method: ModifyChunk
    # "ps-pv-lam": lambda info: PitchShifter(info, PhaseLaminarShifter(info), LinearInterpolator(info)),
    # "ps-pv-lam-tp-full": lambda info: PitchShifter(info, PhaseLaminarShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-lam-tp-limit": lambda info: PitchShifter(info, PhaseLaminarShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    # "ps-pv-lam-tc-full": lambda info: PitchShifter(info, PhaseLaminarShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-lam-tc-limit": lambda info: PitchShifter(info, PhaseLaminarShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    # "ps-pv-lam-th-full": lambda info: PitchShifter(info, PhaseLaminarShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.FULL_RANGE), LinearInterpolator(info)),
    # "ps-pv-lam-th-limit": lambda info: PitchShifter(info, PhaseLaminarShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.BAND_LIMITED), LinearInterpolator(info)),
    #
    # # Based on Phase Vocoder Done Right pseudo code https://www.researchgate.net/publication/319503719_Phase_Vocoder_Done_Right
    # "ps-pv-lock-dyn-6": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, magnitude_min_factor=10 ** -6), LinearInterpolator(info)),
    # "ps-pv-lock-dyn-6-tp-full": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.FULL_RANGE, magnitude_min_factor=10 ** -6), LinearInterpolator(info)),
    # "ps-pv-lock-dyn-6-tp-limit": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, TransientDetectionType.PERCUSSIVE, PhaseResetType.BAND_LIMITED, magnitude_min_factor=10 ** -6), LinearInterpolator(info)),
    # "ps-pv-lock-dyn-6-tc-full": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.FULL_RANGE, magnitude_min_factor=10 ** -6), LinearInterpolator(info)),
    # "ps-pv-lock-dyn-6-tc-limit": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, TransientDetectionType.COMPOUND, PhaseResetType.BAND_LIMITED, magnitude_min_factor=10 ** -6), LinearInterpolator(info)),
    # "ps-pv-lock-dyn-6-th-full": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.FULL_RANGE, magnitude_min_factor=10 ** -6), LinearInterpolator(info)),
    # "ps-pv-lock-dyn-6-th-limit": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, TransientDetectionType.HIGH_FREQ, PhaseResetType.BAND_LIMITED, magnitude_min_factor=10 ** -6), LinearInterpolator(info)),
    # "ps-pv-lock-dyn-4": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, magnitude_min_factor=10 ** -4), LinearInterpolator(info)),
    # "ps-pv-lock-dyn-3": lambda info: PitchShifter(info, PhaseLockedDynamicShifter(info, magnitude_min_factor=10 ** -3), LinearInterpolator(info)),
    #
    # # Based on DAFX Chapter 7.4.3 Phase locked vocoder http://dafx.de/DAFX_Book_Page/index.html
    # "ts-pv-lock": lambda info: TimeStretcher(info, BasicPhaseShifter(info)),
    #
    # # Based on Improved Phase Vocoder Time-Scale Modification of Audio Chapter III.C.1 Identity Phase Locking https://ieeexplore.ieee.org/document/759041
    # "ts-pv-lock-id": lambda info: TimeStretcher(info, PhaseLockedIdentityShifter(info)),
    #
    # # Based on Improved Phase Vocoder Time-Scale Modification of Audio Chapter III.C.2 Scaled Phase Locking https://ieeexplore.ieee.org/document/759041
    # "ts-pv-lock-sc-1": lambda info: TimeStretcher(info, PhaseLockedScaledShifter(info, scale_factor=1)),
    #
    # # Based on Rubberband Source Code StretcherProcess.cpp Method: ModifyChunk https://breakfastquay.com/rubberband/
    # "ts-pv-lam": lambda info: TimeStretcher(info, PhaseLaminarShifter(info)),
    #
    # # Based on Phase Vocoder Done Right pseudo code https://www.researchgate.net/publication/319503719_Phase_Vocoder_Done_Right
    # "ts-pv-lock-dyn-6": lambda info: TimeStretcher(info, PhaseLockedDynamicShifter(info, magnitude_min_factor=10 ** -6))

}


def process_sine(info: TrackInfo, time, frequencies, zero_padding=False):
    info.setup(zero_padding)
    track = source.SineGenerator(info, time, frequencies).get_track()
    signal_processors = {key: configs[key](track.info) for key in configs.keys()}
    controller.process(track, signal_processors)


def process_wav(info: TrackInfo, name, zero_padding=False):
    info.name = name
    info.setup(zero_padding)
    track = source.WavFileReader(info).get_track()
    signal_processors = {key: configs[key](track.info) for key in configs.keys()}
    controller.process(track, signal_processors)


if __name__ == '__main__':
    track_info = TrackInfo()
    track_info.sample_rate = 44100
    track_info.hop_size_factor = 4
    track_info.normalize = False
    track_info.windowType = WindowType.hann.name

    controller = Controller()

    for key in configs.keys():
        print(key)
    track_info.half_tone_steps_to_shift = 5

    # process_sine(track_info, 5, [440])
    # process_sine(track_info, 5, [220, 440, 880, 1720])
    #
    # process_wav(track_info, 'midi_mixed')
    process_wav(track_info, 'midi_melodic')
    # process_wav(track_info, 'midi_percussive')
    # process_wav(track_info, 'strife')
    # process_wav(track_info, 'smash-mouth')
    # process_wav(track_info, 'northwest-passage')
    # process_wav(track_info, 'brass')
    # process_wav(track_info, 'organ', True)
    # process_wav(track_info, 'strings', True)
    # process_wav(track_info, 'heavy-guitar')
    # process_wav(track_info, 'imperial-march')
    # process_wav(track_info, 'cantina-band')
    # process_wav(track_info, 'percussion')
    # process_wav(track_info, 'percussive-melody-1')
    # process_wav(track_info, 'percussive-melody-2')
    # process_wav(track_info, 'speaker')
