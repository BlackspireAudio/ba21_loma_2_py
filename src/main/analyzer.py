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
    """Start of the analyzer. Translates the commandline input and analyzes accordingly"""
    inputfile = ''
    comparefile = ''
    input_dir = ''

    try:
        opts, args = getopt.getopt(argv, "hi:I:c:", ["ifile=", "cfile=", "dir="])
    except getopt.GetoptError:
        displayHelp(2)
    for opt, arg in opts:
        if opt == '-h':
            displayHelp(0)
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-I", "--idir"):
            input_dir = arg
        elif opt in ("-c", "--cfile"):
            comparefile = arg

    print(inputfile, comparefile, input_dir)

    if inputfile == '' and input_dir == '':
        print("no input file/dir selected")
        displayHelp(2)
    if comparefile == "":
        print("no compare file selected")
        displayHelp(2)
    if input_dir != '':
        print("inputfile: " + inputfile + " comparefile: " + comparefile)
        analyze_folder(input_dir, comparefile)
    else:
        analyze(inputfile, comparefile)


def analyze(inputfile, comparefile, ref_samples=[]):
    """"compares an input file with a compare file using the evaluate method"""
    track = getBaseTrack()
    samples, track.info.sample_rate = getSamples(inputfile)
    track.info.setup()
    track.info.name = os.path.basename(os.path.normpath(inputfile))
    track.synthesized["analyzer"] = Result(samples, 1, track.info.sample_rate)
    # track.base = wrapper.process(dsp, track.base)

    if len(ref_samples) == 0:
        track.reference, track.info.sample_rate = getSamples(comparefile)
    else:
        track.reference = ref_samples
    # track.reference = wrapper.process(dsp, track.reference)

    evaluate(track)

    return track.reference

def analyze_folder(input_dir, comparefile):
    """reads all files from a given folder and compares each as an input file against the compare file"""
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
    """"Displays help output"""
    print('analyzer.py {-i <input file>|-I <input dir>} -c <compare file>')
    sys.exit(level)


def getBaseTrack():
    """"Creates a base track for the analyzer"""
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
    """"Reads the samples from the given file"""
    return sf.read(filepath, dtype='float32')


if __name__ == "__main__":
    main(sys.argv[1:])
