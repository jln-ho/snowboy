import sys
import platform

if platform.linux_distribution()[0] != "Ubuntu" or platform.linux_distribution()[1] != "16.04":
    print >> sys.stderr, "Error: this script will only work with Ubuntu 16.04"
    exit(-1)

import argparse
import tempfile
from scipy.io import wavfile
from pmdl import snowboy_pmdl_config
from pmdl.snowboy import SnowboyPersonalEnroll, SnowboyTemplateCut


def check_enroll_output(enroll_ans):
    if enroll_ans == -1:
        raise Exception("Error initializing streams or reading audio data")
    elif enroll_ans == 1:
        raise Exception("Hotword is too long")
    elif enroll_ans == 2:
        raise Exception("Hotword is too short")


def main():
    parser = argparse.ArgumentParser(description='Command line client for generating snowboy personal model')
    parser.add_argument('-m', '--model', dest="model_file", required=True, help="Model output file")
    parser.add_argument('-s', '--samples', dest="samples", required=True, type=argparse.FileType('r'), nargs='+',
                        help="PCM audio files (mono, 16kHz, 16 bit)")
    parser.add_argument('-lang', '--language', default="en", dest="language", help="Language")
    args = parser.parse_args()

    print("template cut")
    cut = SnowboyTemplateCut(
        resource_filename=snowboy_pmdl_config.get_enroll_resource(args.language))

    out = tempfile.NamedTemporaryFile()
    model_path = str(out.name)

    print("personal enroll")
    enroll = SnowboyPersonalEnroll(
        resource_filename=snowboy_pmdl_config.get_enroll_resource(args.language),
        model_filename=model_path)

    assert cut.NumChannels() == enroll.NumChannels()
    assert cut.SampleRate() == enroll.SampleRate()
    assert cut.BitsPerSample() == enroll.BitsPerSample()
    print("channels: %d, sample rate: %d, bits: %d" % (cut.NumChannels(), cut.SampleRate(), cut.BitsPerSample()))

    for sample in args.samples:
        print("processing %s" % sample.name)
        _, data = wavfile.read(sample)
        data_cut = cut.CutTemplate(data.tobytes())
        enroll_ans = enroll.RunEnrollment(data_cut)

    check_enroll_output(enroll_ans)

    filename = args.model_file
    print("saving model file to %s" % filename)
    with open(filename, "wb") as f:
        f.write(open(out.name).read())
    print("finished")


if __name__ == "__main__":
    main()
