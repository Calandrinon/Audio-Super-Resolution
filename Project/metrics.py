from tensorflow.keras import backend as K
import tensorflow as tf
from sklearn.metrics import mean_squared_error
from constants import *


def signal_to_noise_ratio(actual_signal, predicted_signal):
    noise = predicted_signal - actual_signal
    noise_power = K.mean(noise ** 2)
    signal_power = K.mean(actual_signal ** 2)
    ratio = 10 * K.log(signal_power) / K.log(noise_power)
    return K.mean(ratio)


def root_mean_squared_error(actual_signal, predicted_signal):
    return tf.sqrt(tf.losses.mean_squared_error(actual_signal, predicted_signal))


def normalised_root_mean_squared_error(actual_signal, predicted_signal):
    return tf.sqrt(tf.losses.mean_squared_error(actual_signal, predicted_signal)) / (
                TRAINING_SET_THIRD_QUANTILE - TRAINING_SET_FIRST_QUANTILE)
