# -*- coding: utf-8 -*-
"""final_features.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oMcnUs9I6nl1GUOIAGG3-LqjitqtyBi2

RELOAD IF IT EVER SHOWS COOKIES ERROR
"""

from google.colab import drive
drive.mount('/content/drive')

"""OLD MODEL"""

from __future__ import print_function
import datetime
import time
import keras
import scipy.io as io
import numpy as np
import os
import scipy.io as sio
import matplotlib.pyplot as plt
from keras.regularizers import l2
from keras.layers import Dense, Dropout, Activation, Flatten, Subtract, Input, BatchNormalization
from keras import backend as K
from keras.models import Sequential, Model
from keras.models import load_model
from tensorflow.keras.layers import Conv2D
#from keras.layers.convolutional import Conv2D
from tensorflow.keras.layers import MaxPooling2D
#from keras.layers.convolutional import MaxPooling2D
from tensorflow.keras.layers import Activation
#from keras.layers.core import Activation
from tensorflow.keras.layers import Flatten
#from keras.layers.core import Flatten
from tensorflow.keras.layers import Dense
#from keras.layers.core import Dense
from tensorflow.keras.utils import to_categorical
#from keras.utils import np_utils
from tensorflow.keras.utils import plot_model
#from keras.utils import plot_model
from keras.optimizers import SGD, RMSprop, Adam
!pip install mat73
import mat73
from keras.layers import Add


# loss function
def NMSE_IRS(y_true, y_pred):
    r_true = y_true[:,:,:,0] #shape: (batchsize, 8, 8)
    i_true = y_true[:,:,:,1]
    r_pred = y_pred[:,:,:,0]
    i_pred = y_pred[:,:,:,1]
    mse_r_sum = K.sum(K.sum(K.square(r_pred - r_true), -1), -1)
    r_sum = K.sum(K.sum(K.square(r_true), -1), -1)
    mse_i_sum = K.sum(K.sum(K.square(i_pred - i_true), -1), -1)
    i_sum = K.sum(K.sum(K.square(i_true), -1), -1)
    num = mse_r_sum + mse_i_sum
    den = r_sum + i_sum
    return num/den

class LossHistory(keras.callbacks.Callback):
    def on_train_begin(self, logs={}):
        self.losses = {'batch':[], 'epoch':[]}
        self.accuracy = {'batch':[], 'epoch':[]}
        self.val_loss = {'batch':[], 'epoch':[]}
        self.val_acc = {'batch':[], 'epoch':[]}

    def on_batch_end(self, batch, logs={}):
        self.losses['batch'].append(logs.get('loss'))
        self.accuracy['batch'].append(logs.get('NMSE'))
        self.val_loss['batch'].append(logs.get('val_loss'))
        self.val_acc['batch'].append(logs.get('val_NMSE'))

    def on_epoch_end(self, batch, logs={}):
        self.losses['epoch'].append(logs.get('loss'))
        self.accuracy['epoch'].append(logs.get('NMSE'))
        self.val_loss['epoch'].append(logs.get('val_loss'))
        self.val_acc['epoch'].append(logs.get('val_NMSE'))

    def loss_plot(self, loss_type):
        iters = range(len(self.losses[loss_type]))
        plt.figure()
        plt.plot(iters, self.losses[loss_type], 'g', label='train loss')
        if loss_type == 'epoch':
            plt.plot(iters, self.val_loss[loss_type], 'k', label='val loss')
        plt.grid(True)
        plt.xlabel(loss_type)
        plt.ylabel('NMSE-loss')
        plt.legend(loc="upper right")
        plt.title('Training and Validation loss')
        plt.savefig('loss curve.png')
        plt.show()


def train_model(model, train, test, epochs, batch_size):
    # X-data
    xx_train = train[0]
    xx_train = xx_train.astype('float32')
    X_train = xx_train

    xx_test = test[0]
    xx_test = xx_test.astype('float32')
    X_test = xx_test

    # Y-data
    yy_train = train[1]
    yy_train = yy_train.astype('float32')
    Y_train = yy_train

    yy_test = test[1]
    yy_test = yy_test.astype('float32')
    Y_test = yy_test



    print('x_train shape:', X_train.shape)
    print('y_train shape:', Y_train.shape)
    print('x_test shape:', X_test.shape)
    print('y_test shape:', Y_test.shape)
    print(X_train.shape[0], 'input samples')
    print(Y_train.shape[0], 'label samples')

    model.compile(loss=NMSE_IRS,
                  optimizer=Adam(0.001),
                  metrics=[NMSE_IRS])                #This line compiles the model using the NMSE_IRS loss function, Adam optimizer with a learning rate of 0.001, and NMSE_IRS metric.

    history = LossHistory()  #An instance of the LossHistory class is created to track the loss and accuracy during training.

    callbacks_list = [
        # this callback will stop the training when there is no improvement in the validation loss
        keras.callbacks.EarlyStopping(
            monitor='val_loss', min_delta=0, patience=5, verbose=1, mode='min'),
        # save checkpoint
        keras.callbacks.ModelCheckpoint(
            filepath='Model_210106.h5',  # 文件路径
            verbose=1,
            save_best_only=True,
            mode='min'),
        history]

    start_time = time.perf_counter()   #The start time is recorded using time.perf_counter() for measuring the training time.




    model.fit(X_train, Y_train,
              batch_size=batch_size,
              epochs=epochs,
              verbose=2,
              validation_data=(X_test, Y_test),
              callbacks=callbacks_list)

#By calling model.fit, the model will be trained using the specified configuration and the training progress will be displayed based on the verbosity level. The training will stop early if there is no improvement in the validation loss for a certain number of epochs, and the best model based on the validation loss will be saved.


    # print training time cost
    end_time = time.perf_counter()

    elapsed_time_train = end_time - start_time
    print(elapsed_time_train)

    # serialize model to JSON
    model_json = model.to_json()
    with open("Model_210106.json", "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.load_weights('Model_210106.h5')
    model_best = model
    print("Saved best model to disk")

    # print evaluating time cost
    start_time = time.perf_counter()
    score = model_best.evaluate(X_test, Y_test, verbose=1)
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print('Inference time for each sample:', elapsed_time / 20000)
    print('Inference time :', elapsed_time )


    print('Test best epoch NMSE:', score[1])
    history.loss_plot('epoch')

    #The code provided performs the following steps:

    # Prediction. the output is saved as .mat files.
    residual_predict = []
    for test_sample in X_test: #X_test shape: (20000, 8, 8, 2)  test_sample shape:(8, 8, 2)
        test_sample = test_sample[np.newaxis, :] #shape: (1,8,8,2)
        y = model_best.predict(test_sample)  #output shape: (1,8,8,2)
        residual = test_sample - y
        residual_ = np.squeeze(residual) #output shape: (8,8,2)
        residual_predict.append(residual_)  #output shape: (20000,8,8,2)

    predict_np = np.array(residual_predict)
    io.savemat('Model_CDRN_20dB_Residual_Prediction210106.mat', {'data': predict_np})
    print('prediction saved to .mat file')


def ResidualDnCNN(block, depth, image_channels, filters=64, use_bnorm=True):
    input = Input(shape=(None, None, image_channels))
    x = input

    for _ in range(block):
        residual = x
        for _ in range(depth - 1):
            x = Conv2D(filters=filters, kernel_size=(3, 3), strides=(1, 1), padding='same', use_bias=False)(x)
            if use_bnorm:
                x = BatchNormalization(axis=3, momentum=0.0, epsilon=0.0001)(x)
            x = Activation('relu')(x)
        x = Conv2D(filters=image_channels, kernel_size=(3, 3), strides=(1, 1), padding='same', use_bias=False)(x)
        x = Add()([residual, x])

    output = Subtract()([input, x])
    model = Model(inputs=input, outputs=output)
    return model



def main():

    batch_size = 64
    epochs = 10  #change to 400

    model = ResidualDnCNN(block=3, depth=16, image_channels=2, use_bnorm=True)
    model.summary()

    #load .mat data
    data_xtr = sio.loadmat('/content/drive/MyDrive/LOP_4-1/x_train_Rician_CSCG_K10dB_60000_M8_N32_15dB')
    data_ytr = sio.loadmat('/content/drive/MyDrive/LOP_4-1/y_train_Rician_CSCG_K10dB_60000_M8_N32_15dB')
    data_xtest = sio.loadmat('/content/drive/MyDrive/LOP_4-1/x_test_Rician_CSCG_K10dB_20000_M8_N32_15dB')
    data_ytest = sio.loadmat('/content/drive/MyDrive/LOP_4-1/y_test_Rician_CSCG_K10dB_20000_M8_N32_15dB')

    #rename data
    xa_train = data_xtr['x_train']
    ya_train = data_ytr['y_train']

    xa_test = data_xtest['x_test']
    ya_test = data_ytest['y_test']


    train_model(model,
                (xa_train, ya_train),
                (xa_test, ya_test),
                epochs,
                batch_size)

if __name__ == '__main__':
    main()


import scipy.io as sio
from keras.models import load_model

# ... (your code for NMSE_IRS and other functions)

def main():
    # Load the test data from .mat files (similar to the main function in your code)
    #test_data = sio.loadmat('/path/to/test_data.mat')
    data_xtr = sio.loadmat('/content/drive/MyDrive/LOP_4-1/x_train_Rician_CSCG_K10dB_60000_M8_N32_15dB')
    data_ytr = sio.loadmat('/content/drive/MyDrive/LOP_4-1/y_train_Rician_CSCG_K10dB_60000_M8_N32_15dB')

    # Load the saved best model (same as before)
    best_model = load_model('Model_210106.h5', custom_objects={'NMSE_IRS': NMSE_IRS})
    xa_train = data_xtr['x_train']
    ya_train = data_ytr['y_train']

    # Evaluate the model on the test set
    y_pred = best_model.predict(xa_train)

    # Calculate NMSE on the test set using the custom evaluation function
    test_nmse = NMSE_IRS(ya_train, y_pred)
    mean_nmse = np.mean(test_nmse)

    print("Test NMSE:", test_nmse)
    print("Mean NMSE:", mean_nmse)

if __name__ == '__main__':
    main()

"""Images"""

"""PSNR and MSE"""

data_xtr = sio.loadmat('/content/drive/MyDrive/LOP_4-1/x_train_Rician_CSCG_K10dB_60000_M8_N32_15dB')
data_ytr = sio.loadmat('/content/drive/MyDrive/LOP_4-1/y_train_Rician_CSCG_K10dB_60000_M8_N32_15dB')


example_index=0

    # Load the saved best model (same as before)
best_model = load_model('Model_210106.h5', custom_objects={'NMSE_IRS': NMSE_IRS})
xa_train = data_xtr['x_train']
ya_train = data_ytr['y_train']

# Select an example from the test data
input_image = xa_train[example_index]  # Original input image
noisy_image = ya_train[example_index]  # Noisy input image

denoised_image = best_model.predict(input_image[np.newaxis, :])  # Assuming 'model' is your trained denoising model

denoised_image = denoised_image[0]  # Remove the first dimension

print('Input Image Shape:', input_image.shape)
print('Denoised Image Shape:', denoised_image.shape)


import numpy as np
from skimage.metrics import peak_signal_noise_ratio
from skimage.transform import resize  # Import the 'resize' function


import numpy as np
from skimage.metrics import peak_signal_noise_ratio
from skimage.transform import resize

# Assuming 'input_image' and 'denoised_image' are your image tensors
# Check if the dimensions of the images match

import numpy as np
from skimage.metrics import peak_signal_noise_ratio

# Assuming 'input_image' and 'denoised_image' are your image tensors


# Assuming 'original_image' and 'denoised_image' are your image tensors
psnr_value = peak_signal_noise_ratio(input_image, denoised_image)
print(f'PSNR: {psnr_value}')

from skimage.metrics import structural_similarity


mse_value = np.mean((input_image - denoised_image) ** 2)
print(f'MSE: {mse_value}')

import matplotlib.pyplot as plt
import scipy.io as sio
from google.colab import drive
from keras.models import load_model
import numpy as np

# Mount Google Drive
drive.mount('/content/drive')

# Load the test data from .mat files
data_xtr = sio.loadmat('/content/drive/MyDrive/LOP_4-1/x_train_Rician_CSCG_K10dB_60000_M8_N32_15dB')
data_ytr = sio.loadmat('/content/drive/MyDrive/LOP_4-1/y_train_Rician_CSCG_K10dB_60000_M8_N32_15dB')

# Load the saved best model from Google Drive
best_model_path = '/content/drive/MyDrive/LOP_4-1/Model_210106.h5'
best_model = load_model(best_model_path)
xa_train = data_xtr['x_train']
ya_train = data_ytr['y_train']

# Select an example from the test data
example_index = 100
input_image = xa_train[example_index]  # Original input image

# Use your trained model to denoise the image
denoised_image = best_model.predict(input_image[np.newaxis, :])

# Visualize the images
plt.figure(figsize=(8, 4))

# Original input image
plt.subplot(1, 2, 1)
plt.imshow(input_image[:, :, 0], cmap='gray', aspect='equal')
plt.title('Original Image')
plt.axis('off')  # Turn off axis labels

# Denoised image
plt.subplot(1, 2, 2)
plt.imshow(denoised_image[0, :, :, 0], cmap='gray', aspect='equal')
plt.title('Denoised Image')
plt.axis('off')  # Turn off axis labels

plt.tight_layout()
plt.show()