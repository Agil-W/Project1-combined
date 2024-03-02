import tkinter as tk
import os
import threading
import time
import datetime
import struct
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, filedialog
from recorder import AudioRecorder
from playback import SoundPlayer, WAVReader
from text_convert import TextConvert


class RecorderApp:
    def __init__(self):
        self.WAVReader = WAVReader(None)
        self.root = tk.Tk()
        self.root.geometry('1000x700')
        self.root.title("Audio Recorder")
        self.root.resizable(False, False)
        self.trim_data_start = tk.StringVar()
        self.trim_data_end = tk.StringVar()
        self.insert_start_time = tk.StringVar()
        self.insert_end_time = tk.StringVar()
        self.listbox = tk.Listbox(self.root, width='30', height='35')
        self.listbox.grid(row='0', column='0', sticky='NW')
        self.refresh()

        self.display_panel = tk.Frame(
            self.root, width='950', height='563', bg='grey')
        self.display_panel.grid(row='0', column='1')

        self.figure = plt.figure(figsize=(9.5, 5.63))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.display_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.control_panel = tk.Frame(self.root, width='1000', height='150')
        self.control_panel.grid(row='1', columnspan='2', sticky='SEW')

        self.progress_bar = ttk.Progressbar(
            self.display_panel, length='600', orient='horizontal', maximum='100')
        self.progress_bar.place(x='160', y='520')

        self.time = tk.StringVar()
        self.time_stamp = tk.Label(self.display_panel, width='10', textvariable=self.time, font=(
            "Arial", 11, "bold"))
        self.time_stamp.place(x='31', y='520')
        # button

        self.record_button = tk.Button(self.control_panel, text="⏺", font=(
            "Arial", 25, "bold"), relief='solid', command=self.toggle_recording)
        self.record_button.place(x='20', y='35')

        self.play_button = tk.Button(self.control_panel, text="▶️", font=(
            "Arial", 25, "bold"), relief='solid', command=self.play_audio)
        self.play_button.place(x='105', y='35')

        self.stop_button = tk.Button(self.control_panel, text="⏹", font=(
            "Arial", 25, "bold"), relief='solid', command=self.stop_audio)
        self.stop_button.place(x='185', y='35')

        self.trim_button = tk.Button(self.control_panel, text="✂️", font=(
            "Arial", 25, "bold"), relief='solid', command=self.trim_popup)
        self.trim_button.place(x='265', y='35')

        self.refresh_button = tk.Button(self.control_panel, text="🔄", font=(
            "Arial", 25, "bold"), relief='solid', command=self.refresh)
        self.refresh_button.place(x='345', y='35')

        self.insert_button = tk.Button(self.control_panel, text="📩", font=(
            "Arial", 25, "bold"), relief='solid', command=self.insert_popup)
        self.insert_button.place(x='425', y='35')

        self.volume = tk.Scale(
            self.control_panel, orient='horizontal', width='25', length='150', from_='0', to='100', command=self.set_volume)
        self.volume.set(1)
        self.volume.place(x='820', y='50')

        self.vol_label = tk.Label(self.control_panel, text="Volume")
        self.vol_label.place(x='820', y='33')

        self.play_speed = tk.Scale(
            self.control_panel, orient='horizontal', width='25', length='150', from_='0.1', to='8', resolution='0.1', command=self.set_play_speed)  # max is 8
        self.play_speed.set(1)
        self.play_speed.place(x='650', y='50')

        self.play_speed_label = tk.Label(self.control_panel, text="Play Speed")
        self.play_speed_label.place(x='650', y='33')

        self.recorder = AudioRecorder()
        self.WAVReader = WAVReader(None)
        self.player = SoundPlayer(
            self.WAVReader, self.progress_bar, self.time)

        self.root.mainloop()

    def refresh(self):
        if not os.path.exists("recorded_files"):
            os.makedirs("recorded_files")
        recorded_files = [file for file in os.listdir(
            "recorded_files") if file.endswith(".wav")]

        recorded_files = sorted(recorded_files)

        self.listbox.delete(0, tk.END)

        for file in recorded_files:
            self.listbox.insert(tk.END, file)

    def toggle_recording(self):
        if not self.recorder.recording:  # Start recording if not already recording
            self.record_button.config(text="⏹", fg="red")
            threading.Thread(target=self.recorder.record_audio).start()
            self.start_time = time.time()
        else:  # Stop recording if already recording
            self.record_button.config(text="⏺", fg="black")
            self.recorder.stop_recording()
            self.recorder.save_as_wav()
            self.refresh()

    def play_audio(self):
        if not self.listbox.curselection():
            return
        selected_file = self.listbox.get(self.listbox.curselection())
        self.WAVReader.set_filename(f"recorded_files/{selected_file}")
        if self.WAVReader.get_filename() is None:
            return
        self.WAVReader.read_wav_file()

        audio_data = self.WAVReader.get_audio_data()
        time = [i/self.WAVReader.get_sample_rate()
                for i in range(len(audio_data))]

        self.ax.clear()
        self.ax.plot(time, audio_data, color='b')
        self.ax.set_title(f"{selected_file}")
        self.ax.set_axis_off()
        self.canvas.draw()

        text_converter = TextConvert(f"recorded_files/{selected_file}")
        threading.Thread(target=text_converter.RecordProcess).start()   

        self.player.play_sound()

    def stop_audio(self):
        self.player.stop_sound()

    def set_play_speed(self, speed):
        self.player.set_playback_speed(float(speed))

    def set_volume(self, volume):
        self.player.set_volume(float(volume))

    def is_recording(self):
        return self.recording

    def time_to_seconds(self, time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

    def trim(self, start_time, end_time, selected_file):
        self.WAVReader.set_filename(f"recorded_files/{selected_file}")
        if self.WAVReader.get_filename() is None:
            return
        self.WAVReader.read_wav_file()

        audio_data = self.WAVReader.get_audio_data()
        num_sample = len(self.WAVReader.audio_data)
        print(num_sample/self.WAVReader.get_sample_rate())  # second of file
        start = int(start_time*self.WAVReader.get_sample_rate())
        end = int(end_time*self.WAVReader.get_sample_rate())

        trimmed_audio_data = audio_data[start:end]
        byte_data = struct.pack('<{}h'.format(
            len(trimmed_audio_data)), *trimmed_audio_data)

        new_header = self.create_new_wav_header(
            num_channels=self.WAVReader.get_num_channels(),
            sample_rate=self.WAVReader.get_sample_rate(),
            bits_per_sample=self.WAVReader.get_bits_per_sample(),
            num_samples=len(trimmed_audio_data)
        )
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"trimmed_file_{timestamp}.wav", 'wb') as file:
            file.write(new_header)
            file.write(byte_data)
        print("Done trimming")

    def trim_popup(self):
        if not self.listbox.curselection():
            return
        selected_file = self.listbox.get(self.listbox.curselection())
        self.top = tk.Toplevel(self.root)
        self.top.geometry("750x200")
        self.top.title("Trim")
        self.txt = tk.Label(self.top, text="Please enter the trim input (xx:xx:xx)", font=(
            "Arial", 20, "bold"))
        self.txt.pack()
        self.input_panel = tk.Frame(
            self.top, width='750', height='100')
        self.input_panel.pack()

        self.start_time_txt = tk.Label(self.input_panel, text="Start Time", font=(
            "Arial", 20, "bold"))
        self.start_time_txt.grid(row='0', column='0')
        self.end_time_txt = tk.Label(self.input_panel, text="End Time", font=(
            "Arial", 20, "bold"))
        self.end_time_txt.grid(row='1', column='0')
        self.input_box_start_time = tk.Entry(
            self.input_panel, textvariable=self.trim_data_start)
        self.input_box_start_time.grid(row='0', column='1')
        self.input_box_end_time = tk.Entry(
            self.input_panel, textvariable=self.trim_data_end)
        self.input_box_end_time.grid(row='1', column='1')
        self.sumbit_button = tk.Button(self.input_panel, text="Submit", font=(
            "Arial", 20, "bold"), command=lambda: self.submit_input_popup(selected_file))
        self.sumbit_button.grid(row='2', columnspan=2)

    def open_file_dialog(self):
        self.file_path = tk.filedialog.askopenfilename(title="Select a File", filetypes=[
            ("Wav files", "*.wav"), ("All files", "*.*")])
        if self.file_path:
            self.file_label.config(text=f"Selected File: {self.file_path}")
            self.process_file(self.selected_file_path, self.file_path)
            self.top.lift()

    def process_file(self, original_file_path, overwrite_file_path):
        if original_file_path and overwrite_file_path:
            start_time = self.insert_start_time.get()
            end_time = self.insert_end_time.get()
            if start_time and ":" in start_time and end_time and ":" in end_time:
                start_digits = start_time.split(":")
                end_digits = end_time.split(":")
                start_time_in_seconds = int(
                    start_digits[0]) * 3600 + int(start_digits[1]) * 60 + int(start_digits[2])
                end_time_in_seconds = int(
                    end_digits[0]) * 3600 + int(end_digits[1]) * 60 + int(end_digits[2])

                self.insert(original_file_path, overwrite_file_path,
                            start_time_in_seconds, end_time_in_seconds)

    def insert_popup(self):
        if not self.listbox.curselection():
            return
        selected_file = self.listbox.get(self.listbox.curselection())
        self.selected_file_path = f"recorded_files/{selected_file}"
        self.top = tk.Toplevel(self.root)
        self.top.geometry("750x300")
        self.top.title("Insert")

        self.Frame = tk.Frame(self.top, width='750', height='150')
        self.Frame.pack()
        self.txt = tk.Label(self.Frame, text="Please choose the file to be insert ", font=(
            "Arial", 15, "bold"))
        self.txt.pack()
        self.open_file_button = tk.Button(
            self.Frame, text='Open File', command=self.open_file_dialog)
        self.open_file_button.pack()
        self.file_label = tk.Label(self.Frame, text="Selected File:")
        self.file_label.pack()

        # Add input fields for the start time and end time
        self.start_time_text = tk.Label(self.Frame, text="Start Time (xx:xx:xx)", font=(
            "Arial", 15, "bold"))
        self.start_time_text.pack()
        self.start_time_input = tk.Entry(
            self.Frame, textvariable=self.insert_start_time, width='30')
        self.start_time_input.pack()

        self.end_time_text = tk.Label(self.Frame, text="End Time (xx:xx:xx)", font=(
            "Arial", 15, "bold"))
        self.end_time_text.pack()
        self.end_time_input = tk.Entry(
            self.Frame, textvariable=self.insert_end_time, width='30')
        self.end_time_input.pack()
        # Retrieve start and end times from the input fields
        start_time = self.start_time_input.get()
        end_time = self.end_time_input.get()

        # Convert times to seconds
        self.insert_button = tk.Button(
            self.Frame, text='Insert Audio',
            command=lambda: self.insert(
                self.selected_file_path,
                self.file_path,
                # Retrieve start time when button is clicked
                self.time_to_seconds(self.start_time_input.get()),
                # Retrieve end time when button is clicked
                self.time_to_seconds(self.end_time_input.get())
            )
        )
        self.insert_button.pack()

    def insert(self, original_file_path, overwrite_file_path, start_time, end_time):

        self.WAVReader.set_filename(original_file_path)
        self.WAVReader.read_wav_file()
        original_audio_data = self.WAVReader.audio_data

        self.WAVReader.set_filename(overwrite_file_path)
        self.WAVReader.read_wav_file()
        overwrite_audio_data = self.WAVReader.audio_data

        start = int(start_time * self.WAVReader.sample_rate)
        end = int(end_time * self.WAVReader.sample_rate)

        self.audio_data = original_audio_data[:start] + \
            overwrite_audio_data + original_audio_data[end:]

        num_channels = self.WAVReader.get_num_channels()
        sample_rate = self.WAVReader.get_sample_rate()
        bits_per_sample = self.WAVReader.get_bits_per_sample()
        num_samples = len(self.audio_data)
        new_header = self.create_new_wav_header(
            num_channels, sample_rate, bits_per_sample, num_samples)

        # Write the new WAV header and the updated audio data back to the original file
        with open(original_file_path, 'wb') as file:
            file.write(new_header)
            file.write(struct.pack('<{}h'.format(
                len(self.audio_data)), *self.audio_data))

    def submit_input_popup(self, selected_file):
        if self.input_box_start_time.get() == "" or self.input_box_end_time.get() == "":
            print("please enter valid input")
            return

        self.trim_data_start.set(self.input_box_start_time.get())
        self.trim_data_end.set(self.input_box_end_time.get())
        start_digits = self.trim_data_start.get().split(":")
        end_digits = self.trim_data_end.get().split(":")
        start_time = 0
        end_time = 0

        start_time += int(start_digits[0]) * 3600 + \
            int(start_digits[1]) * 60 + int(start_digits[2])
        end_time += int(end_digits[0]) * 3600 + \
            int(end_digits[1]) * 60 + int(end_digits[2])
        self.input_box_start_time.delete(0, tk.END)
        self.input_box_end_time.delete(0, tk.END)
        print(f"start time in s {start_time} end time in s {end_time}")
        if end_time > start_time:
            self.trim_data_start.set(start_time)
            self.trim_data_end.set(end_time)
            self.trim(start_time, end_time, selected_file)
        else:
            print("please enter valid input")
            return

    def create_new_wav_header(self, num_channels, sample_rate, bits_per_sample, num_samples):
        byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
        block_align = num_channels * (bits_per_sample // 8)

        wav_header = bytearray()

        # RIFF header
        wav_header.extend(b'RIFF')
        wav_header.extend(struct.pack(
            '<I', 36 + num_samples * block_align))  # file size
        wav_header.extend(b'WAVE')

        # fmt chunk
        wav_header.extend(b'fmt ')
        wav_header.extend(struct.pack('<I', 16))  # length of the fmt data
        wav_header.extend(struct.pack('<H', 1))  # format (1 = PCM)
        wav_header.extend(struct.pack('<H', num_channels)
                          )  # number of channels
        wav_header.extend(struct.pack('<I', sample_rate))  # sample rate
        wav_header.extend(struct.pack('<I', byte_rate))  # byte rate
        wav_header.extend(struct.pack('<H', block_align))  # block align
        wav_header.extend(struct.pack('<H', bits_per_sample)
                          )  # bits per sample

        # data chunk
        wav_header.extend(b'data')
        wav_header.extend(struct.pack(
            '<I', num_samples * block_align))  # data size

        return bytes(wav_header)


RecorderApp()
