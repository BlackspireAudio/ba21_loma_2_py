import librosa
import numpy as np
import pyrubberband
import soundfile as sf

from main.common.env import get_resources_root_test_data_path
from main.common.track import Track, TrackInfo


class AudioSource:
    def __init__(self, track: Track):
        self.track = track

    def get_track(self) -> Track:
        return self.track


class SineGenerator(AudioSource):
    def __init__(self, info: TrackInfo, length, frequencies, pitch_shift=True):
        sample_count = info.sample_rate * length
        sin = np.zeros(sample_count)
        sin_ref = np.zeros(sample_count)
        pitch_shift_factor = info.pitch_shift_factor
        for freq in frequencies:
            for i in range(0, info.sample_rate * length):
                sin[i] += 1 / len(frequencies) * np.sin(2 * np.pi * freq / info.sample_rate * i)
                sin_ref[i] += 1 / len(frequencies) * np.sin(2 * np.pi * freq / info.sample_rate * i * pitch_shift_factor)

        if not pitch_shift:
            length *= info.time_stretch_ratio
            pitch_shift_factor = 1

        for freq in frequencies:
            for i in range(0, int(info.sample_rate * length)):
                sin_ref[i] += 1 / len(frequencies) * np.sin(2 * np.pi * freq / info.sample_rate * i * pitch_shift_factor)

        track = Track()
        track.info = info
        track.info.name = f"sine_{'-'.join([str(freq) for freq in frequencies])}"
        track.base = sin
        track.reference = sin_ref

        super().__init__(track)


class WavFileReader(AudioSource):

    def __init__(self, info: TrackInfo, pitch_shift=True):
        in_file = get_resources_root_test_data_path(info.name + ".wav")

        track = Track()
        track.info = info
        data, track.info.sample_rate = sf.read(in_file, dtype='float32')
        if len(np.shape(data)) > 1:
            track.base = np.zeros(len(data))
            channels = len(data[0])
            for i in range(len(data)):
                track.base[i] = sum(data[i])
            track.base /= channels
        else:
            track.base = data

        track.info.setup()
        if track.info.half_tone_steps_to_shift == 0:
            track.reference = track.base
        else:
            args = dict()
            args.setdefault("-c", 5)
            args.setdefault("-R", "-R")

            try:
                if pitch_shift:
                    track.reference = pyrubberband.pitch_shift(track.base, info.sample_rate, n_steps=float(info.half_tone_steps_to_shift), rbargs=args)
                else:
                    track.reference = pyrubberband.time_stretch(track.base, info.sample_rate, rate=float(1 / info.time_stretch_ratio), rbargs=args)
            except RuntimeError:
                if pitch_shift:
                    track.reference = librosa.effects.pitch_shift(track.base, info.sample_rate, n_steps=float(info.half_tone_steps_to_shift))
                else:
                    track.reference = librosa.effects.time_stretch(track.base.samples, 1 / info.pitch_shift_factor)

        super().__init__(track)
