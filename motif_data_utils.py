import midi

def one_hot_encode_midi(midi_file_path):
    num_notes = 128

    pattern = midi.read_midifile(midi_file_path)

    encoded_notes = []

    for track in pattern:
        for event in track:
            if isinstance(event, midi.NoteOnEvent) and event.velocity > 0:
                note_vector = [0] * num_notes

                note_vector[event.pitch] = 1

                encoded_notes.append(note_vector)

    return encoded_notes

midi_file_path = 'output/single'
encoded_midi = one_hot_encode_midi(midi_file_path)
