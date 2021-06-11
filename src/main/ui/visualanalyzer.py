import tkinter as tk
from tkinter import *

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import signal as sig

import main.common.env as env

matplotlib.use("TkAgg")
LARGE_FONT = ("Verdana", 12)


class VisualAnalyzer(tk.Tk):

    def __init__(self, reference_file_path, compare_file_path, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.wm_title(self, "Audio DSP Test Bench")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(3, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frame_plt_time = PlotView(container, self)
        self.frame_plt_time.grid(row=0, column=0, sticky="nsew")

        self.frame_control = ControlView(container, self)
        self.frame_control.grid(row=1, column=0, sticky="nsew")

        self.frame_plt_freq = PlotView(container, self)
        self.frame_plt_freq.grid(row=2, column=0, sticky="nsew")

        reference, self.sample_rate = sf.read(reference_file_path, dtype='float32')
        transformed, _ = sf.read(compare_file_path, dtype='float32')
        if len(reference) > len(transformed):
            transformed = np.concatenate((transformed, np.zeros(len(reference) - len(transformed))))
        else:
            reference = np.concatenate((reference, np.zeros(len(transformed) - len(reference))))
        self.x_length = len(reference)
        self.signals = [reference, transformed]
        self.change(0)

    def change(self, direction):
        frame_size = int(self.frame_control.frame_size.get())
        step_size = int(self.frame_control.step_size.get())
        frame_index = int(self.frame_control.frame_index.get())

        if direction == 0:
            frame_size = self.x_length
            frame_index = 0
        elif direction > 0:
            frame_index += step_size
            frame_index = min(round(self.x_length / frame_size) - 1, frame_index)
        else:
            frame_index -= step_size
            frame_index = max(0, frame_index)

        if frame_size % 2 != 0: frame_size -= 1

        self.frame_control.frame_size.set(frame_size)
        self.frame_control.frame_index.set(frame_index)

        start_index = frame_index * frame_size
        end_index = start_index + frame_size
        end_index = min(self.x_length, end_index)

        self.frame_plt_time.plot_amp(self.signals, frame_size, start_index, end_index)
        self.frame_plt_freq.plot_mag(self.signals, self.sample_rate, frame_size, start_index, end_index)
        self.frame_plt_time.canvas.draw()
        self.frame_plt_freq.canvas.draw()


class ControlView(Frame):
    def __init__(self, parent, controller: VisualAnalyzer):
        tk.Frame.__init__(self, parent)

        self.btn_forward = Button(self, text="forward", command=lambda: controller.change(1))
        self.btn_backward = Button(self, text="backward", command=lambda: controller.change(-1))
        self.btn_all = Button(self, text="all", command=lambda: controller.change(0))
        self.frame_size = StringVar()
        self.frame_size.set("2048")
        self.txb_frame_size = Entry(self, textvariable=self.frame_size)
        self.step_size = StringVar()
        self.step_size.set("10")
        self.txb_step_size = Entry(self, textvariable=self.step_size)
        self.frame_index = StringVar()
        self.frame_index.set("0")
        self.txb_frame_index = Entry(self, textvariable=self.frame_index)

        for btn in (
                self.btn_backward, self.btn_all, self.btn_forward, self.txb_frame_size, self.txb_step_size,
                self.txb_frame_index):
            btn.pack(side=LEFT, anchor=CENTER, expand=True)


class PlotView(Frame):
    def __init__(self, parent, controller: VisualAnalyzer):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.plot_index = 0
        self.figure, self.plots = plt.subplots(2, figsize=(25, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def plot_mag(self, signals, sample_rate, frame_size, start_index, end_index):
        spectrums = []
        for signal in signals:
            frame = signal[start_index: end_index]
            # spectrum, freqs, _ = plt.magnitude_spectrum(frame, Fs=sample_rate)
            frame = frame * sig.get_window("hann", frame_size)
            frame = np.fft.rfft(frame)
            spectrum = np.abs(frame) * 2 / np.sum(frame_size)
            spectrum = 10 * np.log10(spectrum)
            freqs = np.arange((frame_size / 2) + 1) / (float(frame_size) / sample_rate)
            low_cut = 0
            for i in range(len(freqs)):
                if (freqs[i]) < 50:
                    low_cut = i
                else:
                    break

            spectrum = spectrum[low_cut: len(spectrum)]
            freqs = freqs[low_cut: len(freqs)]
            spectrums.append(spectrum)
        self.plot(freqs, spectrums, scale="log", resolution=100)

    def plot_amp(self, signals, frame_size, start_index, end_index):
        timeline = range(frame_size)
        amplitudes = []
        for signal in signals:
            amplitudes.append(signal[start_index:end_index])
        self.plot(timeline, amplitudes)

    def plot(self, x_values, y_values_list, scale="linear", resolution=0):
        self.plot_index = 0
        for y_values in y_values_list:
            plot = self.plots[self.plot_index]
            plot.clear()
            plot.plot(x_values, y_values)
            # if resolution > 0:
            #     mi = round(min(x_values) / (resolution / 10)) * 10
            #     mx = round(max(x_values) / (resolution / 10)) * 10
            #     plot.set_xticks(np.arange(mi, mx, (mx - mi) / resolution))
            plot.set_xscale(scale)
            self.plot_index += 1


if __name__ == '__main__':
    # reference, sample_rate = sf.read(env.get_resources_out_audio_path("sine_wave_base_3_4/reference_3_4.wav"), dtype='float32')
    # transformed, _ = sf.read(env.get_resources_out_audio_path("sine_wave_base_3_4/transformed_3_4.wav"), dtype='float32')
    window = VisualAnalyzer(
        env.get_resources_out_audio_path("sine_wave_base_3_4/base_3_4.wav"),
        env.get_resources_out_audio_path("sine_wave_base_3_4/transformed_3_4.wav")
    )
    window.mainloop()
