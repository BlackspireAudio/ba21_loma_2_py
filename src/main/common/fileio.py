import csv
import os
from typing import List

import soundfile as sf

import main.common.env as env
from main.common.track import Track


def write(track: Track):
    path = env.get_resources_out_path(track.info.folder_name())
    if not os.path.exists(path): os.mkdir(path)
    write_track_to_wav(track, path)


def read_wav(name):
    name = "/phase-interpretation.py-data/" + name + ".wav"
    return sf.read(name, dtype='float32')


def write_track_to_wav(track: Track, path: str):
    write_wav(os.path.join(path, track.info.file_name("base", "wav")), track.base, track.info.sample_rate)
    write_wav(os.path.join(path, track.info.file_name("reference", "wav")), track.reference, track.info.sample_rate)
    for key in track.synthesized.keys():
        write_wav(os.path.join(path, track.info.file_name(key, "wav")), track.synthesized[key].samples, track.info.sample_rate)


def write_wav(path: str, samples: List, sample_rate: float):
    sf.write(path, samples, sample_rate, subtype='PCM_24')


def open_csv(name: str):
    return open(env.get_resources_out_path(name + '.csv'), mode='w', newline='')


def write_line_to_csv(file, values):
    csv.writer(file).writerow(values)


def close_file(file):
    file.close()
