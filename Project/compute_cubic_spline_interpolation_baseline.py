from DatasetGenerator import DatasetGenerator
import numpy as np
from metrics import *

_, _, (input_test_files, target_test_files) = DatasetGenerator.split_list_of_files()
input_test_data, target_test_data = [], []

snr_sum, mse_sum, nrmse_sum = 0, 0, 0
cubic_spline_baseline = lambda x: DatasetGenerator.upsample(x, RESAMPLING_FACTOR)

for index in range(0, NUMBER_OF_TESTING_TENSORS):
    low_resolution_patch = np.load("preprocessed_dataset/low_res/" + input_test_files[index])
    high_resolution_patch = np.load("preprocessed_dataset/high_res/" + target_test_files[index])
    low_resolution_patch = low_resolution_patch.reshape(low_resolution_patch.shape[0])
    high_resolution_patch = high_resolution_patch.reshape(high_resolution_patch.shape[0])
    baseline_patch = cubic_spline_baseline(low_resolution_patch)

    snr = signal_to_noise_ratio(K.constant(high_resolution_patch), K.constant(baseline_patch))
    snr_sum += snr

    print("Loaded testing sample {}".format(index))

snr_mean = snr_sum / NUMBER_OF_TESTING_TENSORS

print("SNR: {}".format(snr_mean))
