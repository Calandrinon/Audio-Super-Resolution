import tensorflow as tf
from model import create_model
from constants import *
from DatasetGenerator import DatasetGenerator
import numpy as np
from metrics import signal_to_noise_ratio, root_mean_squared_error, normalised_root_mean_squared_error_training, normalised_root_mean_squared_error_validation
from tensorflow.keras.callbacks import ModelCheckpoint
import matplotlib.pyplot as plt
import datetime

model = create_model()
model.summary()

(input_data_files, target_data_files), (input_validation_files, target_validation_files), _ \
    = DatasetGenerator.split_list_of_files()
input_data, target_data, input_validation_data, target_validation_data = [], [], [], []

print("Loading the .npy files...")

print("Number of input data files: {}".format(len(input_data_files)))
print("Number of target data files: {}".format(len(target_data_files)))
number_of_input_batches = int(NUMBER_OF_TRAINING_TENSORS / BATCH_SIZE)
for index in range(0, number_of_input_batches*BATCH_SIZE):
    input_data.append(np.load("preprocessed_dataset/low_res/" + input_data_files[index]))
    target_data.append(np.load("preprocessed_dataset/high_res/" + target_data_files[index]))
    print("Loaded training sample {}".format(index))

number_of_validation_batches = int(NUMBER_OF_VALIDATION_TENSORS / BATCH_SIZE)
for index in range(0, number_of_validation_batches*BATCH_SIZE):
    input_validation_data.append(np.load("preprocessed_dataset/low_res/" + input_validation_files[index]))
    target_validation_data.append(np.load("preprocessed_dataset/high_res/" + target_validation_files[index]))
    print("Loaded validation sample {}".format(index))

print("Converting Python list to numpy array...")
input_data = np.array(input_data)
target_data = np.array(target_data)
input_validation_data = np.array(input_validation_data)
target_validation_data = np.array(target_validation_data)
print("Done.")

print("Some input tensor shape: {}".format(input_data[0].shape))
print("Some target tensor shape: {}".format(target_data[0].shape))
print("Input data: {}".format(input_data.shape))
print("Target data: {}".format(target_data.shape))
print("Input validation data: {}".format(input_validation_data.shape))
print("Target validation data: {}".format(target_validation_data.shape))
print("Number of input batches: {}".format(number_of_input_batches))
print("Number of validation batches: {}".format(number_of_validation_batches))
print("Number of input data files: {}".format(len(input_data_files)))
print("Number of validation data files: {}".format(len(input_validation_files)))
print("Training started...")

start_time = datetime.datetime.now()

adam_optimizer = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
model.compile(loss="mean_squared_error", optimizer=adam_optimizer,
              metrics=[signal_to_noise_ratio, root_mean_squared_error, normalised_root_mean_squared_error_training, normalised_root_mean_squared_error_validation])

model_filenames = os.listdir("models/")
model_filenames.sort()
latest_epoch = 0
if len(model_filenames) > 0:
    VERSION = int(model_filenames[-1].split('_')[4]) + 1
    latest_epoch = int(model_filenames[-1].split('_')[14])
    NUMBER_OF_EPOCHS += latest_epoch
    model.load_weights(MODEL_PATH)
elif len(os.listdir("./checkpoints")) != 0:
    print("Loading saved checkpoint...")
    latest_checkpoint_path = tf.train.latest_checkpoint(checkpoint_dir=CHECKPOINT_DIRECTORY)
    print("Latest saved checkpoint: {}".format(latest_checkpoint_path))

checkpoint_callback = ModelCheckpoint(filepath=CHECKPOINT_PATH,
                                      save_weights_only=True,
                                      save_best_only=True,
                                      verbose=True,
                                      monitor='val_loss')

history = model.fit(input_data, target_data,
                    batch_size=BATCH_SIZE,
                    epochs=NUMBER_OF_EPOCHS,
                    validation_data=(input_validation_data, target_validation_data),
                    callbacks=[checkpoint_callback],
                    initial_epoch=latest_epoch,
                    verbose=True)

end_time = datetime.datetime.now()

print("model.fit history:")
print(list(history.history.keys()))
print(history.history)

plot_title = "Resampling factor: " + str(RESAMPLING_FACTOR) \
             + "; Overlap: " + str(OVERLAP) \
             + "; Sample dimension: " + str(SAMPLE_DIMENSION) \
             + "; Epochs: " + str(NUMBER_OF_EPOCHS) \
             + "; Batch size: " + str(BATCH_SIZE) \
             + "; Learning rate: " + str(LEARNING_RATE) \
             + "; Data split: " + str(NUMBER_OF_TRAINING_TENSORS) + "/" + str(NUMBER_OF_VALIDATION_TENSORS) + "/" + str(NUMBER_OF_TESTING_TENSORS)
plot_filename = plot_title.replace(" ", "_").replace(":", "").replace(";", "").replace("/", "_")

loss_files = os.listdir("outputs/losses-as-numpy-arrays")
if len(loss_files) > 0:
    loss_values = np.load("outputs/losses-as-numpy-arrays/loss_values.npy").tolist()
    validation_loss_values = np.load("outputs/losses-as-numpy-arrays/validation_loss_values.npy").tolist()
    snr_values = np.load("outputs/losses-as-numpy-arrays/snr.npy").tolist()
    validation_snr_values = np.load("outputs/losses-as-numpy-arrays/val_snr.npy").tolist()
    root_mse_values = np.load("outputs/losses-as-numpy-arrays/root_mse.npy").tolist()
    validation_root_mse_values = np.load("outputs/losses-as-numpy-arrays/val_root_mse.npy").tolist()
    nrmse_training_values = np.load("outputs/losses-as-numpy-arrays/nrmse_training_values.npy").tolist()
    nrmse_validation_values = np.load("outputs/losses-as-numpy-arrays/nrmse_validation_values.npy").tolist()

    history.history['loss'] = loss_values + history.history['loss']
    history.history['val_loss'] = validation_loss_values + history.history['val_loss']
    history.history['signal_to_noise_ratio'] = snr_values + history.history['signal_to_noise_ratio']
    history.history['val_signal_to_noise_ratio'] = validation_snr_values + history.history['val_signal_to_noise_ratio']
    history.history['root_mean_squared_error'] = root_mse_values + history.history['root_mean_squared_error']
    history.history['val_root_mean_squared_error'] = validation_root_mse_values + history.history['val_root_mean_squared_error']
    history.history['normalised_root_mean_squared_error_training'] = nrmse_training_values + history.history['normalised_root_mean_squared_error_training']
    history.history['val_normalised_root_mean_squared_error_validation'] = nrmse_validation_values + history.history['val_normalised_root_mean_squared_error_validation']

fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(16, 16))
# fig.tight_layout(pad=2.0)
axes.plot(history.history['loss'], label="Training loss", color=(255/255.0, 0/255.0, 0/255.0))
axes.plot(history.history['val_loss'], label="Validation loss", color=(0/255.0, 255/255.0, 0/255.0))
axes.set_xlabel("Epoch")
axes.set_ylabel("Loss")
plt.legend()

model.save_weights("models/model_stage_{}_version_{}_".format(STAGE, VERSION) + plot_filename.lower() + ".h5")

fig.suptitle(plot_title, fontsize="medium")
plt.savefig("outputs/training-plots/training_validation_plot_stage_{}_version_{}_".format(STAGE, VERSION) + plot_filename.lower() + ".png")
plt.show()

np.save("outputs/losses-as-numpy-arrays/loss_values.npy", history.history['loss'])
np.save("outputs/losses-as-numpy-arrays/validation_loss_values.npy", history.history['val_loss'])
np.save("outputs/losses-as-numpy-arrays/snr.npy", history.history['signal_to_noise_ratio'])
np.save("outputs/losses-as-numpy-arrays/val_snr.npy", history.history['val_signal_to_noise_ratio'])
np.save("outputs/losses-as-numpy-arrays/root_mse.npy", history.history['root_mean_squared_error'])
np.save("outputs/losses-as-numpy-arrays/val_root_mse.npy", history.history['val_root_mean_squared_error'])
np.save("outputs/losses-as-numpy-arrays/nrmse_training_values.npy", history.history['normalised_root_mean_squared_error_training'])
np.save("outputs/losses-as-numpy-arrays/nrmse_validation_values.npy", history.history['val_normalised_root_mean_squared_error_validation'])

print("Training started at {}".format(start_time.strftime("%Y-%m-%d %H:%M:%S")))
print("Training ended at {}".format(end_time.strftime("%Y-%m-%d %H:%M:%S")))
