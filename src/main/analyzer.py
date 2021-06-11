import getopt
import os
import re
import sys
from os import listdir
from os.path import isfile, join

import soundfile as sf

from main.common.enums import WindowType
from main.common.track import TrackInfo, Track, Result
from main.dsp.eval import evaluate


def main(argv):
    # inputfile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\heartache_-5\\reference_-5.wav"
    inputfile = ''

    # comparefile = ''
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\mixed\\normal project Project\\heartache_-5.wav"

    # input_dir = ""
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\heartache_-5"

    #basendrum
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_percussive_5"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\08. midi_percussive_+5"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\percussive\\midi_percussive_+5.wav"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_percussive_-5"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\07. midi_percussive_-5"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\percussive\\midi_percussive_-5.wav"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_percussive_12"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\06. midi_percussive_+12"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\percussive\\midi_percussive_+12.wav"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_percussive_-12"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\05. midi_percussive_-12"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\percussive\\midi_percussive_-12.wav"

    #mixed
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_mixed_5"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\04. midi_mixed_+5"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\mixed\\midi_mixed_+5.wav"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_mixed_-5"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\03. midi_mixed_-5"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\mixed\\midi_mixed_-5.wav"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_mixed_12"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\02. midi_mixed_+12"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\mixed\\midi_mixed_+12.wav"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\01. midi_mixed_-12"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_mixed_-12"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\mixed\\midi_mixed_-12.wav"

    #melodic
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_melodic_5"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\12. midi_melodic_+5"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\melodic\\midi_melodic_+5.wav"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_melodic_-5"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\11. midi_melodic_-5"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\melodic\\midi_melodic_-5.wav"
    input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_melodic_12"
    input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\ba21_loma_2_py\\res\\out\\midi_melodic_12"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\09. midi_melodic_+12"
    comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\melodic\\midi_melodic_+12.wav"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\true names\\midi_melodic_-12"
    # input_dir = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\test sounds\\10. midi_melodic_-12"
    # comparefile = "C:\\Users\\Alex\\Documents\\zhaw\\BA\\reference songs\\simi\\melodic\\midi_melodic_-12.wav"

    try:
        opts, args = getopt.getopt(argv, "hi:c:", ["ifile=", "cfile="])
    except getopt.GetoptError:
        displayHelp(2)
    for opt, arg in opts:
        if opt == '-h':
            displayHelp(0)
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-c", "--cfile"):
            comparefile = arg

    if inputfile == '' and input_dir == '':
        print("no input file selected")
        displayHelp(2)
    if comparefile == "":
        print("no compare file selected")
        displayHelp(2)
    if input_dir != "":
        print("inputfile: " + inputfile + " comparefile: " + comparefile)
        analyze_folder(input_dir, comparefile)
    else:
        analyze(inputfile, comparefile)


def analyze(inputfile, comparefile, ref_samples=[]):
    track = getBaseTrack()
    samples, track.info.sample_rate = getSamples(inputfile)
    track.info.setup()
    track.info.name = os.path.basename(os.path.normpath(inputfile))
    track.transformed["analyzer"] = Result(samples, 1, track.info.sample_rate)
    # track.base = wrapper.process(dsp, track.base)

    if len(ref_samples) == 0:
        track.reference, track.info.sample_rate = getSamples(comparefile)
    else:
        track.reference = ref_samples
    # track.reference = wrapper.process(dsp, track.reference)

    evaluate(track)

    return track.reference

def analyze_folder(input_dir, comparefile):
    onlyfiles = [f for f in listdir(input_dir) if isfile(join(input_dir, f)) and os.path.splitext(f)[1] == ".wav"]
    ref_samples = []
    for file in onlyfiles:
        if not re.search("^base_", file):
            print("compare base with "+file)
            if len(ref_samples) == 0:
                ref_samples = analyze(input_dir+"\\"+file, comparefile)
            else:
                analyze(input_dir + "\\" + file, comparefile, ref_samples)



def displayHelp(level):
    print('analyzer.py -i <inputfile> -c <comparefile>')
    sys.exit(level)


def getBaseTrack():
    track_info = TrackInfo()
    track_info.sample_rate = 44100
    track_info.hop_size_factor = 4
    track_info.normalize = False
    track_info.windowType = WindowType.hann.name
    track_info.half_tone_steps_to_shift = 0
    track_info.setup(False)
    track = Track()
    track.info = track_info

    return track


def getSamples(filepath):
    return sf.read(filepath, dtype='float32')


if __name__ == "__main__":
    main(sys.argv[1:])
