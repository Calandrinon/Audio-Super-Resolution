from model import create_model
from constants import *
import tensorflow_datasets as tfds
import tensorflow as tf
from DatasetGenerator import DatasetGenerator
import numpy as np
from metrics import *
import librosa
import librosa.display
import soundfile as sf
import datetime
import matplotlib.pyplot as plt
import random
import re
from tensorflow.python.ops.numpy_ops import np_config
np_config.enable_numpy_behavior()

print("Loading and compiling model...")
model = create_model(NUMBER_OF_RESIDUAL_BLOCKS)
model.compile(loss="mean_squared_error", optimizer='Adam',
              metrics=[signal_to_noise_ratio, normalised_root_mean_squared_error])
# model.load_weights(CHECKPOINT_PATH).expect_partial()
model.load_weights(MODEL_PATH)

print("Loading the sample vocal recording from the VCTK dataset...")
dataset = tfds.load("vctk", with_info=False)
sample_array = None
transcript = None
recording_index = 0

chosen_recording = random.randint(AMOUNT_OF_TRACKS_USED_FOR_DATA_GENERATION + 1, AMOUNT_OF_TRACKS_USED_FOR_DATA_GENERATION + 100)

for sample in dataset['train']:
    if recording_index == chosen_recording:
        transcript = sample['text']
        print("Recording transcript: {}".format(transcript))
        sample_array = np.array(sample['speech'], dtype=float)
        break
    recording_index += 1

sample_array_length = len(sample_array)
sample_array = sample_array[:sample_array_length - (sample_array_length % RESAMPLING_FACTOR)]

median = int(np.median(sample_array))
start_index = np.where(sample_array == median)[0][0]
batch_used_for_prediction = []
high_res_chunks = []

for batch_index in range(0, BATCH_SIZE):
    high_res_chunk = sample_array[start_index:start_index + SAMPLE_DIMENSION]
    low_res_chunk = np.array(high_res_chunk[0::RESAMPLING_FACTOR])
    low_res_chunk = tf.constant(low_res_chunk, dtype=float)
    high_res_chunks.append(high_res_chunk)
    batch_used_for_prediction.append(low_res_chunk)

random_batch_index = random.randint(0, BATCH_SIZE)
result = model.predict(np.array(batch_used_for_prediction))

figure, axes = plt.subplots(3, 1, figsize=(10, 10))
axes[0].set_title("Low-res (1200 samples)")
axes[0].plot(batch_used_for_prediction[random_batch_index])
axes[1].set_title("High-res (4800 samples)")
axes[1].plot(high_res_chunks[random_batch_index])
axes[2].set_title("Super-res (4800 samples)")
axes[2].plot(result[random_batch_index])

high_res_chunk = high_res_chunks[random_batch_index].astype(np.float32)
super_res_chunk = np.array(result[random_batch_index]).reshape(result[random_batch_index].shape[0]).astype(np.float32)

nrmse_high_res_super_res = normalised_root_mean_squared_error(high_res_chunk, super_res_chunk)
figure.suptitle("Whole chunks (High-res/Super-res NRMSE={})".format(round(nrmse_high_res_super_res, 4)))
plt.savefig("outputs/whole-chunks.png")
plt.show()

figure, axes = plt.subplots(3, 1, figsize=(10, 10))
axes[0].set_title("Low-res (25 samples)")
axes[0].plot(batch_used_for_prediction[random_batch_index][0:25])
axes[1].set_title("High-res (100 samples)")
axes[1].plot(high_res_chunks[random_batch_index][0:100])
axes[2].set_title("Super-res (100 samples)")
axes[2].plot(result[random_batch_index][0:100])
part_of_the_high_res_chunk = high_res_chunks[random_batch_index][0:100].astype(np.float32)
part_of_the_super_res_chunk = np.array(result[random_batch_index][0:100]).reshape(result[random_batch_index][0:100].shape[0]).astype(np.float32)
nrmse_parts_of_the_chunk_high_res_super_res = normalised_root_mean_squared_error(part_of_the_high_res_chunk, part_of_the_super_res_chunk)
figure.suptitle("Model result for a small part of a chunk (High-res/Super-res NRMSE={})".format(round(nrmse_parts_of_the_chunk_high_res_super_res, 4)))
plt.savefig("outputs/small-part-of-a-chunk.png")
plt.show()

figure, axes = plt.subplots(1, 1, figsize=(10, 10))
axes.scatter(x=[i for i in range(0, 100)], y=high_res_chunks[random_batch_index][0:100], color="red")
axes.scatter(x=[i for i in range(0, 100)], y=result[random_batch_index][0:100], color="green")
figure.suptitle("Scatterplot - Model result for a small part of a chunk (High-res (red)/Super-res (green) NRMSE={})".format(round(nrmse_parts_of_the_chunk_high_res_super_res, 4)))
plt.savefig("outputs/scatterplot-high-res-super-res.png")
plt.show()
