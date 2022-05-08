from model import create_model
from constants import *
import tensorflow_datasets as tfds
import tensorflow.keras.backend as K
import numpy as np
from metrics import *
from tensorflow.keras.models import Model
import soundfile as sf
import matplotlib.pyplot as plt
import random
import matplotlib.pylab as pl
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import math
import os

print("Loading and compiling model...")
model = create_model()
model.summary()

model.compile(loss="mean_squared_error", optimizer='Adam',
              metrics=[signal_to_noise_ratio, normalised_root_mean_squared_error],
              run_eagerly=True)
model.load_weights(MODEL_PATH)

print("Model layers: {}".format(model.layers))
print("Loading the sample vocal recording from the VCTK dataset...")
dataset = tfds.load("vctk", with_info=False)
sample_array = None
transcript = None
recording_index = 0

chosen_recording = AMOUNT_OF_TRACKS_USED_FOR_DATA_GENERATION + 100

for sample in dataset['train']:
    if recording_index == chosen_recording:
        transcript = sample['text']
        print("Recording transcript: {}".format(transcript))
        sample_array = np.array(sample['speech'], dtype=float)
        break
    recording_index += 1

print("Downsampling the audio...")

sample_array_length = len(sample_array)
sample_array = sample_array[:sample_array_length - (sample_array_length % RESAMPLING_FACTOR)]

high_resolution_chunk = sample_array[(sample_array_length // 2):(sample_array_length // 2) + SAMPLE_DIMENSION]
low_resolution_chunk = high_resolution_chunk[::RESAMPLING_FACTOR]
low_resolution_chunk = np.reshape(low_resolution_chunk, (len(low_resolution_chunk), 1))
input_batch = BATCH_SIZE * [low_resolution_chunk]
input_batch = tf.constant(input_batch)

number_of_layers = len(model.layers)
subset_of_layers = []

os.mkdir("./layer-outputs")

layer_index = 0
for layer in model.layers:
    if 'conv' not in layer.name:
        continue
    print("Plotting the output of layer {}...".format(layer_index))
    subset_of_layers.append(layer.output)
    auxiliary_model = Model(inputs=model.input, outputs=layer.output)
    auxiliary_model.summary()
    intermediate_layer_output = auxiliary_model.predict(input_batch)

    intermediate_layer_output = intermediate_layer_output[0]
    number_of_samples = intermediate_layer_output.shape[0]
    number_of_filters = intermediate_layer_output.shape[1]

    x = np.linspace(1, 5, number_of_samples)

    pl.figure(figsize=(20, 20))
    axes = pl.subplot(projection='3d')
    colors = ['r', 'g', 'b', 'm', 'c', 'y', 'k', 'w']

    for filter_index in range(0, number_of_filters):
        y = np.ones(x.size) * filter_index
        axes.plot(x, y, intermediate_layer_output[:, filter_index], color=colors[filter_index % len(colors)])
        filter_index += 1
    print("Plotted layer {}'s output.".format(layer_index))
    axes.set_title("Output of layer/block no. {} - number of samples = {} - number of filters = {}".format(layer_index, number_of_samples, number_of_filters))
    axes.set_xlabel('Time axis')
    axes.set_zlabel('Amplitude')
    layer_index += 1
    plt.savefig("layer-outputs/features-extracted-by-layer-{}.png".format(layer_index))
    plt.show()
