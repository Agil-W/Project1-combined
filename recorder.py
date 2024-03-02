import pyaudio
import datetime
import struct
import os


class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.BITS_PER_SAMPLE = 16
        self.frames = []
        self.recording = False

    def record_audio(self):
        audio = pyaudio.PyAudio()
        self.recording = True
        self.frames = []

        stream = audio.open(format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK)

        print("Recording audio... Press the stop button to stop recording.")

        while self.recording:
            data = stream.read(self.CHUNK)
            self.frames.append(data)

        print("Finished recording.")
        # #debugging
        # print(f'Here is the frames size: {len(self.frames)}')

        stream.stop_stream()
        stream.close()
        audio.terminate()

    def stop_recording(self):
        self.recording = False

    def generate_filename(self):
        # Generate a new file name based on the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create the directory if it doesn't exist
        if not os.path.exists("recorded_files"):
            os.makedirs("recorded_files")

        # Set the output file path
        output_file = os.path.join("recorded_files", f"audio_{timestamp}.wav")
        return output_file

    def save_as_wav(self):
        output_file = self.generate_filename()
        wav_header = self.create_wav_header()
        wav_data = b''.join(self.frames)

        with open(output_file, 'wb') as file:
            file.write(wav_header)
            file.write(wav_data)

    def create_wav_header(self):
        channels = self.CHANNELS
        bits_per_sample = self.BITS_PER_SAMPLE
        sample_rate = self.RATE

        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        wav_header = bytearray()

        # RIFF header
        wav_header.extend(b'RIFF')
        # file size including header(36) + data
        wav_header.extend(struct.pack(
            '<I', 36 + len(self.frames)*self.CHUNK*(bits_per_sample//8)))
        wav_header.extend(b'WAVE')

        # fmt chunk
        wav_header.extend(b'fmt ')
        wav_header.extend(struct.pack('<I', 16))  # length of the fmt data
        wav_header.extend(struct.pack('<H', 1))  # format (1 = PCM)
        wav_header.extend(struct.pack('<H', channels))  # number of channels
        wav_header.extend(struct.pack('<I', sample_rate))  # sample rate
        wav_header.extend(struct.pack('<I', byte_rate))  # byte rate
        wav_header.extend(struct.pack('<H', block_align))  # block align
        wav_header.extend(struct.pack('<H', bits_per_sample)
                          )  # bits per sample

        # data chunk
        wav_header.extend(b'data')
        wav_header.extend(struct.pack('<I', len(self.frames)
                          * self.CHUNK*(bits_per_sample//8)))
        return bytes(wav_header)
