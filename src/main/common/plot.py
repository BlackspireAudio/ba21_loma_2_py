import matplotlib.pyplot as plt
import numpy as np


def plot(plots, index, x, y, r, x_name, y_name, x_res=50, y_res=10):
    p = plots[index]
    x = x[r]
    y = y[r]
    p.plot(x, y)
    p.set_xlabel(x_name)
    p.set_ylabel(y_name)
    set_grid(p)
    set_ticks(p.set_xticks, x, 0, x_res)
    set_ticks(p.set_yticks, y, 2, y_res)
    return index + 1


def set_ticks(func, values, ndec, resolution):
    mi = min(values)
    mx = max(values)
    func(np.arange(mi, mx, round(mx - mi, ndec) / resolution))


def set_grid(p):
    p.grid(b=True, which='both', color='#666666', linestyle='-', alpha=0.2)


def plot_mag(plots, index, x, y, r):
    y = y / max(y)
    return plot(plots, index, x, y, r, 'freq', 'mag')


def plot_mag_spec(plots, index, samples, sample_rate, r):
    y, x, _ = plt.magnitude_spectrum(samples, Fs=sample_rate)
    plot(plots, index, x, y, r, 'freq', 'mag')
    return index + 1


def plot_phase(plots, index, x, y, r):
    return plot(plots, index, x, y, r, 'freq', 'phase', 50, np.pi * 5)


def plot_phase_spec(plots, index, samples, sample_rate, r):
    y, x, _ = plt.phase_spectrum(samples, Fs=sample_rate)
    plot(plots, index, x, y, r, 'freq', 'phase')
    return index + 1


def plot_angle_spec(plots, index, samples, sample_rate, r):
    y, x, _ = plt.angle_spectrum(samples, Fs=sample_rate)
    plot(plots, index, x, y, r, 'freq', 'angle')
    return index + 1
