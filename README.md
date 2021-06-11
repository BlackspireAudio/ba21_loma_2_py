# ba21_loma_2_py

A python project to test and evaluate different dsp algorithms

## Run

Execute the script src/main/start.py to generate pitch shifted audio. The output will be located on
res/out/[song-name]_[shift]/. For each signal, the original, a reference and the results of the various pitch shift
algorithm processors are stored there.

To change the number of half tones to shift, adjust the variable track_info.half_tone_steps_to_shift. To change the
algorithms used, add or remove from the configs dict at the top of src/main/start.py

## Add new Test Files

Add the test file to the folder res/test-data/ In main/start.py call the method pitch_shift_wav with the name of the
test file

## Reference

For comparison, each processed file is shifted using the rubberband audio library integrated with the pyrubberband
wrapper and made available as reference track. Make sure to make the rubberband-cli available as env variable as
described here https://github.com/bmcfee/pyrubberband/issues/18#issuecomment-786515163

## Algorithms

| Name | Description | Status | Performance | Quality | Source| | ------------- | ------------- | ------------- |
------------ | | Phase Vocoder | Simple phase vocoder limited to horizontal phase propagation | Complete | Fast |
acceptable for melodic, unusable for percussion | Based on DAFX Chapter 7.4.4 Block by block
approach http://dafx.de/DAFX_Book_Page/index.html | | Phase Locked Identity Vocoder | Advanced phase vocoder peak
detection and horizontal / static vertical phase propagation | Complete | Med | Good results for percussion, has issue
with broad harmonic envelopes | Based on Improved Phase Vocoder Time-Scale Modification of Audio Chapter III.C.2 Scaled
Phase Locking https://ieeexplore.ieee.org/document/759041 | | Phase Locked Scaled Vocoder | Advanced phase vocoder peak
detection and horizontal / static vertical phase propagation | Complete | Med | Good results for percussion, has issue
with broad harmonic envelopes | Based on Improved Phase Vocoder Time-Scale Modification of Audio Chapter III.C.2 Scaled
Phase Locking https://ieeexplore.ieee.org/document/759041l | | Phase Laminar Vocoder | Advanced phase vocoder with
horizontal and adaptive vertical phase propagation | Complete | Slow (non-real-time) | Acceptable overall results, but
lacks clairity | Based on Rubberband Source Code StretcherProcess.cpp Method:
ModifyChunk https://breakfastquay.com/rubberband/ | | Phase Locked Dynamic Vocoder | Advanced phase vocoder peak
detection and horizontal / dynamic vertical phase propagation | Complete | Slow | Best overall results (except
percussion). Only works for real-time with tolerance > 10**-4 | Based on Phase Vocoder Done Right pseudo
code https://www.researchgate.net/publication/319503719_Phase_Vocoder_Done_Right |

## Transient Detection

### Percussive

Performs phase resets at percussive transients

### High Frequency

Performs phase resets at high frequency transients

### Compound

Mixes the above two detection methods. Provides the best over all results

## Phase Reset

### Full Range

Executes phase resets over the entire frequency range

### Band Limited

Executes phase resets in the low and high frequency band, leaving the normal phase propagation for the mid frequency
band. Provides the best over all results