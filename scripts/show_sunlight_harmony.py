#!/usr/bin/env python3
"""Show chord progressions for Sunlight Sonata album."""
import random
from melodica.types import Scale, Mode, NoteInfo, BarGrid
from melodica.harmonize.functional_hmm import FunctionalHMMHarmonizer
from melodica.composer.tension_curve import TensionCurve

PC = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
Q = {0:'Maj',1:'Min',2:'Dim',3:'Aug',4:'s2',5:'s4',
     6:'Maj7',7:'Min7',8:'Dom7',9:'Maj9',10:'Min9',11:'Add9'}

INTERVALS = {
    Mode.IONIAN: [0,2,4,5,7,9,11],
    Mode.LYDIAN: [0,2,4,6,7,9,11],
    Mode.MIXOLYDIAN: [0,2,4,5,7,9,10],
    Mode.MAJOR_PENTATONIC: [0,2,4,7,9],
}

tracks = [
    ('1 Sunrise',        Scale(0, Mode.IONIAN),         52, 16),
    ('2 Morning Light',  Scale(7, Mode.LYDIAN),         68, 16),
    ('3 Meadow Walk',    Scale(2, Mode.MIXOLYDIAN),     100, 16),
    ('4 River Song',     Scale(5, Mode.IONIAN),          76, 16),
    ('5 Afternoon Heat', Scale(9, Mode.MAJOR_PENTATONIC),88, 16),
    ('6 Lemonade',       Scale(4, Mode.LYDIAN),          72, 16),
    ('7 Golden Hour',    Scale(10, Mode.IONIAN),         58, 16),
    ('8 Sunset Waltz',   Scale(0, Mode.MIXOLYDIAN),     64, 20),
    ('9 Starlight',      Scale(2, Mode.IONIAN),          48, 20),
]

for title, scale, bpm, bars in tracks:
    dur = bars * 4.0
    random.seed(hash(title))
    scale_notes = INTERVALS.get(scale.mode, [0,2,4,5,7,9,11])
    melody = []
    for i in range(bars):
        root_midi = 60 + scale.root
        idx = random.randint(0, len(scale_notes) - 1)
        pitch = root_midi + scale_notes[idx] + (12 if random.random() > 0.6 else 0)
        melody.append(NoteInfo(pitch=pitch, start=float(i * 4), duration=4.0))

    tension = TensionCurve(total_beats=dur, curve_type='classical')
    harmonizer = FunctionalHMMHarmonizer(beam_width=6, bar_grid=BarGrid(4, 4), n_candidates=4)
    result = harmonizer.harmonize(melody, scale, dur, tension_curve=tension)

    chords = []
    for c in result:
        fn = c.function.name[:3] if c.function else '---'
        name = PC[c.root] + Q.get(c.quality.value, '?')
        chords.append(name + ':' + fn)

    fns = [c.function.name if c.function else 'NONE' for c in result]
    print(f'{title}  ({PC[scale.root]} {scale.mode.value})')
    print('  ' + ' | '.join(chords))
    tonic = fns.count('TONIC')
    sub = fns.count('SUBDOMINANT')
    dom = fns.count('DOMINANT')
    other = len(fns) - tonic - sub - dom
    parts = [f'TON={tonic}', f'SUB={sub}', f'DOM={dom}']
    if other:
        parts.append(f'OTHER={other}')
    print('  ' + '  '.join(parts))
    print()
