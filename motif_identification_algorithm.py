import mido
import os
from collections import Counter

class MelodicPatternAnalysis:
    def __init__(self):
        self.patterns = []

    def get_patterns(self, motifs):
        for motif in motifs:
            pattern = [note.pitch_interval for note in motif]
            # create a dict to store pattern and its motif
            final_pattern = tuple(pattern)
            self.patterns.append({
                'pattern': final_pattern,
                'motif': motif,
            })

    def get_recurring_patterns(self, total_motifs, total_duration):
        # create dict to store pattern and its info including motif
        recurring_patterns = {}

        # get all patterns
        all_patterns = [pattern['pattern'] for pattern in self.patterns]

        # get all unique patterns
        unique_patterns = set(all_patterns)

        # get all motifs for each unique pattern
        for pattern in unique_patterns:
            pattern_motifs = []
            for motif in self.patterns:
                if motif['pattern'] == pattern:
                    pattern_motifs.append(motif['motif'])

            # compute for pattern info
            pattern_prevalence_score = len(pattern_motifs) / total_motifs
            pattern_duration = 0
            for motif in pattern_motifs:
                for note in motif:
                    pattern_duration += note.duration
            pattern_duration_score = pattern_duration / total_duration

            # store pattern info
            recurring_patterns[pattern] = {
                'motifs': pattern_motifs,
                'prevalence_score': pattern_prevalence_score,
                'duration_score': pattern_duration_score,
            }

        # sort patterns by prevalence score
        recurring_patterns = dict(sorted(recurring_patterns.items(
        ), key=lambda item: item[1]['prevalence_score'], reverse=True))

        return recurring_patterns


class MotifIdentification:
    class NoteInfo:
        def __init__(self, timing, pitch, pitch_interval, velocity, duration, start_time):
            self.timing = timing
            self.pitch = pitch
            self.pitch_interval = pitch_interval
            self.velocity = velocity
            self.duration = duration
            self.start_time = start_time

    def __init__(self, all_midi_file_paths, window_length=20):
        self.all_midi_file_paths = all_midi_file_paths
        self.window_length = window_length
        self.total_tracks = 0
        self.all_motifs = []

        self.all_midi_files = []

        temp_total_tracks = 0
        for midi_file_path in self.all_midi_file_paths:
            print(f"Loading midi file: {midi_file_path}\n")
            file = None
            try:
                file = mido.MidiFile(midi_file_path)
            except:
                print(f"Error loading midi file: {midi_file_path}\n")
                continue

            if file:
                self.all_midi_files.append(mido.MidiFile(midi_file_path))
                temp_total_tracks += len(mido.MidiFile(midi_file_path).tracks)

    def create_midi_file_from_pattern(self, pattern, output_file="output.mid"):
        # get ticks per beat from original midi file
        # TODO: get ticks per beat from original midi file

        # get average ticks per beat from all midi files
        ticks_per_beat = 0
        for midi_file in self.all_midi_files:
            ticks_per_beat += midi_file.ticks_per_beat
        ticks_per_beat /= len(self.all_midi_files)

        if not ticks_per_beat:
            ticks_per_beat = 500

        ticks_per_beat = int(ticks_per_beat)

        # create new midi file
        new_midi_file = mido.MidiFile(ticks_per_beat=ticks_per_beat)

        for motif in pattern['motifs']:
            new_track = mido.MidiTrack()
            new_midi_file.tracks.append(new_track)

            # get ave tempo from original midi file
            ave_tempo = 0
            tempo_count = 0
            for midi_file in self.all_midi_files:
                for track in midi_file.tracks:
                    for msg in track:
                        if msg.type == 'set_tempo':
                            ave_tempo += msg.tempo
                            tempo_count += 1

            if tempo_count:
                ave_tempo /= tempo_count

            if ave_tempo:
                ave_tempo = int(ave_tempo)
                new_track.append(
                    mido.MetaMessage(
                        'set_tempo', tempo=ave_tempo, time=0))

            # get time signature from original midi file
            for midi_file in self.all_midi_files:
                for track in midi_file.tracks:
                    for msg in track:
                        if msg.type == 'time_signature':
                            new_track.append(mido.MetaMessage(
                                'time_signature', numerator=msg.numerator, denominator=msg.denominator, time=msg.time))

            # get key signature from original midi file
            for midi_file in self.all_midi_files:
                for track in midi_file.tracks:
                    for msg in track:
                        if msg.type == 'key_signature':
                            new_track.append(mido.MetaMessage(
                                'key_signature', key=msg.key, time=msg.time))

            # sort notes by start time
            motif.sort(key=lambda note: note.start_time)

            for note in motif:
                new_track.append(mido.Message('note_on', note=note.pitch,
                                 velocity=note.velocity, time=note.start_time))
                new_track.append(mido.Message('note_off', note=note.pitch,
                                 velocity=0, time=note.start_time + note.duration))

        new_midi_file.save(output_file)
        print(f"Saved new midi file: {output_file}")

    def create_midi_file(self, patterns, output_file="output.mid"):
        # create new midi file
        new_midi_file = mido.MidiFile()

        # get ave ticks per beat from original midi file
        ticks_per_beat = 0
        for midi_file in self.all_midi_files:
            ticks_per_beat += midi_file.ticks_per_beat
        ticks_per_beat /= len(self.all_midi_files)

        if not ticks_per_beat:
            ticks_per_beat = 500

        ticks_per_beat = int(ticks_per_beat)

        new_midi_file.ticks_per_beat = ticks_per_beat

        for pattern, pattern_info in patterns.items():
            # generate only at most 3 motifs per pattern
            motif_count = 1

            for motif in pattern_info['motifs']:
                if motif_count > 3:
                    break

                new_track = mido.MidiTrack()

                # set track name based on pattern index and motif index ("Pattern 1 Motif 1")
                track_name = f"Pattern {list(patterns.keys()).index(pattern) + 1} Motif {pattern_info['motifs'].index(motif) + 1}"
                # get prevalence score
                prevalence_score = pattern_info['prevalence_score']
                prevalence_score *= 100
                prevalence_score = round(prevalence_score, 2)
                track_name += f" ({prevalence_score}%)"

                new_track.append(mido.MetaMessage(
                    'track_name', name=track_name, time=0))

                # get tempo from original midi file
                ave_tempo = 0
                temp_count = 0
                for midi_file in self.all_midi_files:
                    for track in midi_file.tracks:
                        for msg in track:
                            if msg.type == 'set_tempo':
                                ave_tempo += msg.tempo
                                temp_count += 1

                if temp_count:
                    ave_tempo /= temp_count

                if ave_tempo:
                    ave_tempo = int(ave_tempo)
                    new_track.append(
                        mido.MetaMessage(
                            'set_tempo', tempo=ave_tempo, time=0))

                # get time signature from original midi file
                for midi_file in self.all_midi_files:
                    for track in midi_file.tracks:
                        for msg in track:
                            if msg.type == 'time_signature':
                                new_track.append(mido.MetaMessage(
                                    'time_signature', numerator=msg.numerator, denominator=msg.denominator, time=msg.time))

                # get key signature from original midi file
                for midi_file in self.all_midi_files:
                    for track in midi_file.tracks:
                        for msg in track:
                            if msg.type == 'key_signature':
                                new_track.append(mido.MetaMessage(
                                    'key_signature', key=msg.key, time=msg.time))

                new_midi_file.tracks.append(new_track)

                # sort notes by start time
                motif.sort(key=lambda note: note.start_time)

                for note in motif:
                    new_track.append(mido.Message('note_on',
                                                  note=note.pitch,
                                                  velocity=note.velocity,
                                                  time=note.start_time))
                    new_track.append(mido.Message('note_off',
                                                  note=note.pitch,
                                                  velocity=note.velocity,
                                                  time=note.duration))

                motif_count += 1

        new_midi_file.save(output_file)
        print(f"Saved new midi file: {output_file}")

    def get_window_info(self, window):
        melodic_info = []
        active_notes = {}  # Dictionary to store active notes and their start times

        with_matching_note = 0
        no_matching_note = 0

        for i, msg in enumerate(window):
            if msg.type == 'note_on':
                timing, pitch, velocity = msg.time, msg.note, msg.velocity
                start_time = timing
                # use pitch class
                active_notes[pitch % 12] = start_time

                # Check for a subsequent note_on message with the same pitch
                next_msg_idx = i + 1
                while next_msg_idx < len(window):
                    next_msg = window[next_msg_idx]

                    if next_msg.type in ['note_on', 'note_off']:
                        with_matching_note += 1
                        # calculate pitch interval in terms of class
                        pitch_interval = (next_msg.note - pitch) % 12
                        duration = next_msg.time

                        break

                    next_msg_idx += 1
                else:
                    # if no matching note, skip
                    no_matching_note += 1

                    # compute for default duration using mido.seconds2tick
                    default_seconds = 1

                    ave_ticks_per_beat = 0
                    for midi_file in self.all_midi_files:
                        ave_ticks_per_beat += midi_file.ticks_per_beat
                    ave_ticks_per_beat /= len(self.all_midi_files)
                    default_ticks_per_beat = int(ave_ticks_per_beat)
                    default_tempo = 500000

                    # calculate average tempo for whole midi file
                    tempo = 0
                    tempo_count = 0
                    for midi_file in self.all_midi_files:
                        for track in midi_file.tracks:
                            for msg in track:
                                if msg.type == 'set_tempo':
                                    tempo += msg.tempo
                                    tempo_count += 1
                    tempo = int(tempo / tempo_count)

                    if tempo:
                        default_tempo = tempo

                    default_ticks = mido.second2tick(
                        default_seconds, default_ticks_per_beat, default_tempo)

                    duration = default_ticks
                    continue

                note_info = self.NoteInfo(
                    timing, pitch, pitch_interval, velocity, duration, start_time)
                melodic_info.append(note_info)

        return melodic_info, with_matching_note, no_matching_note

    def process_midi_track(self, track):
        window_length = self.window_length
        motifs = []
        total_messages = len(track)

        # Filter out non-note messages
        track = [msg for msg in track if msg.type in ['note_on', 'note_off']]

        print(f"Total note messages: {len(track)}")

        patterns = []
        total_notes = 0
        matching_note_total = 0
        no_matching_note_total = 0

        if len(track) > 0:
            for i in range(0, total_messages - window_length + 1):
                window = track[i:i + window_length]

                # analyze window to get note infos
                current_motif, with_matching_note, no_matching_note = self.get_window_info(
                    window)
                motifs.append(current_motif)
                matching_note_total += with_matching_note
                no_matching_note_total += no_matching_note

            total_notes = matching_note_total + no_matching_note_total
            print(f"Total motifs: {len(motifs)}")
        return motifs

    def run(self):
        try:
            # Clean output directory
            os.system('rm -rf ./output/*')

            for midi_file in self.all_midi_files:
                current_midi_file = midi_file
                index = self.all_midi_files.index(midi_file)
                total = len(self.all_midi_files)
                # midi file path
                print(
                    f"\nMIDI FILE: {current_midi_file.filename} ({index + 1}/{total})")

                current_midi_file.tracks.sort(key=lambda track: track[0].time)

                for track in current_midi_file.tracks:
                    print(f"\n--- TRACK: {track.name} ---")
                    motifs = self.process_midi_track(track)

                    if motifs:
                        self.all_motifs.append(motifs)

            print(f"\nALL MOTIFS: {len(self.all_motifs)}")

            print("\n--- MELODIC PATTERN ANALYSIS ---")
            # melodic pattern analysis
            melodic_analysis = MelodicPatternAnalysis()

            for motifs in self.all_motifs:
                melodic_analysis.get_patterns(motifs)

            # analyze recurring patterns
            total_motifs = sum(len(motifs) for motifs in self.all_motifs)
            print(f"TOTAL MOTIFS: {total_motifs}")

            total_duration = 0
            for track_motifs in self.all_motifs:
                for motif in track_motifs:
                    for note in motif:
                        total_duration += note.duration

            recurring_patterns = melodic_analysis.get_recurring_patterns(
                total_motifs, total_duration)

            print(f"TOTAL RECURRING PATTERNS: {len(recurring_patterns)}")

            # print top 10 patterns
            print("\nTOP 10 PATTERNS:")
            top_10_patterns = dict(
                list(recurring_patterns.items())[:10])

            pattern_count = 1
            for pattern, pattern_info in top_10_patterns.items():
                print(f"Pattern: {pattern}")
                print(f"Motifs: {len(pattern_info['motifs'])}")
                print(
                    f"Prevalence Score: {pattern_info['prevalence_score']}\n")

                # file name is pattern
                # self.create_midi_file_from_pattern(
                #     pattern_info, f"output/{pattern_count}.mid")
                pattern_count += 1

            # create new midi file
            self.create_midi_file(
                top_10_patterns, 'output/single.mid')

        except Exception as e:
            print(f"Exception: {e}")
            return None