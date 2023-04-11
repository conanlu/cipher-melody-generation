import music21
import argparse
import math
import os
import magenta.music as mm
import tensorflow as tf
import pypianoroll
import matplotlib.pyplot as plt
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.music import DEFAULT_QUARTERS_PER_MINUTE
from magenta.models.shared import sequence_generator_bundle
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from note_seq.protobuf.generator_pb2 import GeneratorOptions
from note_seq.protobuf.music_pb2 import NoteSequence


def char_to_note(c):
    ret = chr((((((ord(c[0].lower()) - 97) % 7) + 65) + 2) % 7) + 65)
    print(ret)
    return ret  + "4"


def string_to_primer(input_string):
    s = music21.stream.Stream()
    for c in input_string:
        if c.isalpha():
            s.append(music21.note.Note(char_to_note(c), type='quarter'))
        else:
            s.append(music21.note.Rest())
    mf = music21.midi.translate.streamToMidiFile(s)
    mf.open('input.mid', 'wb')
    mf.write()
    mf.close()



# generates midi and visualization of machine-generated melody
def generate(input):
    string_to_primer(input)
    generator_id = 'lookback_rnn'
    bundle_name = generator_id + ".mag"
    mm.notebook_utils.download_bundle(bundle_name, "bundles")
    bundle = sequence_generator_bundle.read_bundle_file(
        os.path.join("bundles", bundle_name))

    generator_map = melody_rnn_sequence_generator.get_generator_map()
    generator = generator_map[generator_id](checkpoint=None, bundle=bundle)
    generator.initialize()
    primer_filename = ("input.mid")
    primer_sequence = mm.midi_io.midi_file_to_note_sequence(primer_filename)

    if primer_sequence.tempos:
        if len(primer_sequence.tempos) > 1:
            raise Exception("This will end up being the first tempo anyways")
        qpm = primer_sequence.tempos[0].qpm
    else:
        qpm = 60  # just choosing a value, because it was None before

    seconds_per_step = 60.0 / qpm / getattr(generator, "steps_per_quarter", 4)

    primer_sequence_length_steps = math.ceil(primer_sequence.total_time / seconds_per_step)

    primer_sequence_length_time = primer_sequence_length_steps * seconds_per_step
    # This is a pure magenta hack to make sure it starts generating right after the primer, without an extra bar.
    primer_end_adjust = (0.00001 if primer_sequence_length_time > 0 else 0)

    primer_start_time = 0
    primer_end_time = (primer_start_time
                       + primer_sequence_length_time)

    total_length_steps = 128
    generation_length_steps = total_length_steps - primer_sequence_length_steps
    generation_length_steps

    if generation_length_steps <= 0:
        raise Exception("Total length in steps too small "
                        + "(" + str(total_length_steps) + ")"
                        + ", needs to be at least one bar bigger than primer "
                        + "(" + str(primer_sequence_length_steps) + ")")
    generation_length_time = generation_length_steps * seconds_per_step

    generation_start_time = primer_end_time
    generation_end_time = (generation_start_time
                           + generation_length_time
                           + primer_end_adjust)

    generator_options = GeneratorOptions()

    # parameters of the generator
    temperature: float = 1.0
    beam_size: int = 1
    branch_factor: int = 1
    steps_per_iteration: int = 1

    generator_options.args['temperature'].float_value = temperature
    generator_options.args['beam_size'].int_value = beam_size
    generator_options.args['branch_factor'].int_value = branch_factor
    generator_options.args['steps_per_iteration'].int_value = steps_per_iteration

    generator_options.generate_sections.add(
        start_time=generation_start_time,
        end_time=generation_end_time)

    sequence = generator.generate(input_sequence=primer_sequence, generator_options=generator_options)
    mm.midi_io.note_sequence_to_midi_file(sequence=sequence, output_file="static/output.mid")
    multitrack = pypianoroll.read("static/output.mid")
    plt.figure(figsize=(8,4))
    multitrack.plot()
    plt.savefig("static/images/sing.png")