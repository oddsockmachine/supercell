from instruments.instrument import Instrument
from instruments.sequencer import Sequencer
from instruments.drum_machine import DrumMachine
from instruments.drum_deviator import DrumDeviator
from instruments.beat_randomizer import BeatRandomizer
from instruments.binary_sequencer import BinarySequencer
from instruments.chord_sequencer import ChordSequencer
from instruments.droplets import Droplets
from instruments.transformer import Transformer




def instrument_lookup(num):
    return {
        0: Instrument,  # Generic, fallback, no functionality
        1: Sequencer,
        2: DrumMachine,
        3: ChordSequencer,
        4: BeatRandomizer,
        5: DrumDeviator,
        6: BinarySequencer,
        7: Droplets,
        8: Transformer,
        'Instrument': Instrument,  # Generic, fallback, no functionality
        'Sequencer': Sequencer,
        'Drum Machine': DrumMachine,
        'Chord Sequencer': ChordSequencer,
        'Beat Randomizer': BeatRandomizer,
        'Drum Deviator': DrumDeviator,
        'Binary Sequencer': BinarySequencer,
        'Droplets': Droplets,
        'Transformer': Transformer,
    }[num]
