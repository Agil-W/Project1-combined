import pyaudio
import struct
import threading


class WAVReader:
    def __init__(self, filename):
        self.filename = filename
        self.sample_rate = 0
        self.num_channels = 0
        self.bits_per_sample = 0
        self.audio_data = []

    def read_wav_file(self):
        with open(self.filename, 'rb') as file:
            # Read the WAV file header to extract necessary information
            riff_header = file.read(12)
            format_chunk_header = file.read(24)
            # format_chunk_header[0:4] == 'fmt '
            format_chunk_size = struct.unpack(
                '<I', format_chunk_header[4:8])[0]
            type_of_format = struct.unpack('<H', format_chunk_header[8:10])[0]
            self.num_channels = struct.unpack(
                '<H', format_chunk_header[10:12])[0]
            self.sample_rate = struct.unpack(
                '<I', format_chunk_header[12:16])[0]
            self.bits_per_sample = struct.unpack(
                '<H', format_chunk_header[22:24])[0]

            # skip 'data'
            file.read(8)

            # Read the audio data
            data = file.read()
            # Assuming 16-bit audio
            num_samples = len(data) // (self.bits_per_sample // 8)

            # Unpack the audio data into a list of samples
            self.audio_data = struct.unpack('<{}h'.format(num_samples), data)

    def set_filename(self, filename):
        self.filename = filename

    def get_filename(self):
        return self.filename

    def get_bits_per_sample(self):
        return self.bits_per_sample

    def get_sample_rate(self):
        return self.sample_rate

    def get_num_channels(self):
        return self.num_channels

    def get_audio_data(self):
        return self.audio_data


class SoundPlayer:
    def __init__(self, wav_reader, progress_bar, time):
        self.wav_reader = wav_reader
        self.progress_bar = progress_bar
        self.time = time
        self.playback_speed = 1.0
        self.volume = 1.0
        self.is_playing = False
        self.stop_flag = threading.Event()

    def get_total_time(self):
        return len(self.wav_reader.get_audio_data())/self.wav_reader.get_sample_rate()

    def set_playback_speed(self, speed):
        self.playback_speed = speed

    def set_volume(self, volume):
        self.volume = volume

    def play_sound(self):
        if self.is_playing:  # only one thread can play sound
            return

        def play_sound_thread():
            self.p = pyaudio.PyAudio()
            self.is_playing = True
            adjust_sample_rate = int(
                self.wav_reader.get_sample_rate() * self.playback_speed)

            if adjust_sample_rate > 48000:
                adjust_sample_rate = 48000
            elif adjust_sample_rate < 0:
                adjust_sample_rate = 44100

            self.stream = self.p.open(format=self.p.get_format_from_width(self.wav_reader.get_bits_per_sample()//8),
                                      channels=self.wav_reader.get_num_channels(),
                                      rate=int(self.wav_reader.get_sample_rate()
                                               * self.playback_speed),
                                      output=True)

            audio_data = self.wav_reader.get_audio_data()
            self.total_samples = len(audio_data)
            progress = 0
            full_time = len(self.wav_reader.get_audio_data()
                            ) / self.wav_reader.get_sample_rate()
            for sample in audio_data:
                adjusted_volume_sample = int(sample * self.volume)
                if adjusted_volume_sample < -32768:
                    adjusted_volume_sample = -32768
                elif adjusted_volume_sample > 32767:
                    adjusted_volume_sample = 32767

                if self.stop_flag.is_set():
                    break

                self.stream.write(struct.pack('<h', adjusted_volume_sample))

                progress += 1
                if progress % 100 == 0:
                    progress_time = progress / self.wav_reader.get_sample_rate()
                    self.progress_bar['value'] = progress / \
                        self.total_samples*100
                    self.time.set(f'{progress_time:.2f}/{full_time:.2f}')

            # no one can see this code
            self.progress_bar['value'] = 100
            self.time.set(f'{full_time:.2f}/{full_time:.2f}')
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
            self.is_playing = False

            if not self.stop_flag.is_set():
                self.stream.stop_stream()
                self.stream.close()
                self.p.terminate()
                self.is_playing = False

            self.stop_flag.clear()
        threading.Thread(target=play_sound_thread).start()

    def stop_sound(self):
        if self.is_playing:
            self.stop_flag.set()
            self.is_playing = False

    def trim(self, start_time, end_time):
        start = int(start_time*self.wav_reader.get_sample_rate())
        end = int(end_time*self.wav_reader.get_sample_rate())
        self.wav_reader.audio_data = self.wav_reader.audio_data[start:end]
