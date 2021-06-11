import time

import main.dsp.wrapper as wrap
from common.fileio import write
from main.common.track import Track, Result
from main.dsp.eval import evaluate


class Controller:

    def process(self, track: Track, signal_processors: dict):
        print(f"processing: {track.info.name}")
        for key in signal_processors.keys():
            print(f"processing: {key}, pitch-shift: {track.info.half_tone_steps_to_shift}")
            if key.startswith("ps"):
                wrapper = wrap.PitchShiftWrapper(signal_processors[key])
            else:
                wrapper = wrap.TimeStretchWrapper(signal_processors[key])

            start = time.time()
            transformed_samples = wrapper.process(track)
            end = time.time()
            track.synthesized[key] = Result(transformed_samples, end - start, track.info.sample_rate)
            print(f'processing time: {track.synthesized[key].processing_time}; real time ratio: {track.synthesized[key].realtime_ratio}')

        evaluate(track)

        write(track)

    def time_stretch(self, track: Track, signal_processors: dict):
        print(f"processing: {track.info.name}")
        for key in signal_processors.keys():
            print(f"processing: {key}")
            wrapper = wrap.TimeStretchWrapper(signal_processors[key])
            start = time.time()
            transformed_samples = wrapper.process(track)
            end = time.time()
            track.synthesized[key] = Result(transformed_samples, end - start, track.info.sample_rate)
            print(f'processing time: {track.synthesized[key].processing_time}; real time ratio: {track.synthesized[key].realtime_ratio}')

        evaluate(track)

        write(track)
