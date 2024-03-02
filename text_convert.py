import speech_recognition as sr
import os

class TextConvert:
    def __init__(self, selected_file):
        self.recorded_file = selected_file
        self.recognizer = sr.Recognizer()

    def RecordProcess(self):
        
        print("Record:", self.recorded_file)

        recorded_file = sr.AudioFile(self.recorded_file)
        try:
            with recorded_file as source:
                record = self.recognizer.record(source)
            text = self.recognizer.recognize_google(record)
            segments = text.split(".")
            for segment in segments:
                print(segment.strip())  
        except sr.UnknownValueError:
            print("\n unknown value error.")
        except sr.RequestError as e:
            print("\n server request error: {0}".format(e))

        print("\n All record have been converted.")