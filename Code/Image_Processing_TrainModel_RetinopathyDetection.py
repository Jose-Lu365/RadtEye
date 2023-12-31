""" ///////////////////////////////////////////////////////////////////////////////
//                   Radt Eye
// Date:         14/11/2023
//
// File: Image_Processing_TrainModel_RetinopathyDetection.py
// Description: AI model training for eye issues detection
/////////////////////////////////////////////////////////////////////////////// """

import matplotlib.pyplot as plt 
import numpy as np 
import os 
import tensorflow as tf 

from keras.callbacks import ModelCheckpoint, EarlyStopping

batch_size = 32
epoch = 5000

def load_data(folder_path):
    img_height = 800
    img_width = 800

    train_ds = tf.keras.utils.image_dataset_from_directory(
        folder_path,
        validation_split=0.2,
        subset="training",
        shuffle=True,
        seed=123,
        image_size=(img_height, img_width),
        batch_size=batch_size
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        folder_path,
        validation_split=0.2,
        subset="validation",
        shuffle=True,
        seed=123,
        image_size=(img_height, img_width),
        batch_size=batch_size
    )

    return train_ds, val_ds

def normalized_model(ds):
    # Standarize RGB from 0 to 1
    normalization_layer = tf.keras.layers.Rescaling(1./255)
    normalized_ds = ds.map(lambda x, y: (normalization_layer(x), y))
    return normalized_ds

def augment_model(ds):
    # Function for brightness adjustment
    def adjust_brightness(image):
        # Generate a random value for brightness adjustment between -0.2 and 0.2
        delta = tf.random.uniform([], -0.3, 0.3)
        return tf.image.adjust_brightness(image, delta=delta)

    # Function for random contrast adjustment
    def adjust_contrast(image):
        # Generate a random value for contrast adjustment between 0.8 and 1.2
        contrast_factor = tf.random.uniform([], 0.8, 1.2)
        return tf.image.adjust_contrast(image, contrast_factor=contrast_factor)

    # Data augmentation and normalization
    data_augmentation = tf.keras.Sequential([
        tf.keras.layers.experimental.preprocessing.RandomFlip("horizontal_and_vertical"),
        tf.keras.layers.experimental.preprocessing.RandomRotation(0.2),
        tf.keras.layers.Lambda(adjust_brightness),  # Apply brightness adjustment
        tf.keras.layers.Lambda(adjust_contrast),    # Apply contrast adjustment
    ])

    # Apply augmentation and normalization to the dataset
    augmented_samples = ds.map(lambda x, y: (data_augmentation(x), y))

    # Concatenate the augmented samples with the original dataset
    augmented_ds = ds.concatenate(augmented_samples)

    # Configure the dataset for performance
    augmented_ds = augmented_ds.cache().prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
    
    return normalized_model(augmented_ds)

def build_model(train_normalized_ds, val_normalized_ds):
    AUTOTUNE = tf.data.AUTOTUNE

    train_normalized_ds = train_normalized_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_normalized_ds = val_normalized_ds.cache().prefetch(buffer_size=AUTOTUNE)
    
    num_classes = 6

    model = tf.keras.Sequential([
    tf.keras.layers.Rescaling(1./255),
    tf.keras.layers.Conv2D(32, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(32, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(32, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(num_classes)
    ])

    # lr_schedule = tf.keras.optimizers.schedules.InverseTimeDecay(
    #     0.001,
    #     decay_steps=batch_size*1000,
    #     decay_rate=1,
    #     staircase=False
    # )

    # tf.keras.optimizers.Adam(lr_schedule)

    model.compile(
        optimizer='adam',
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=['accuracy']
    )
    return model

folder_path = '/home/nnds3a/Documents/RadtEye/Database/2Organized'
train_ds, val_ds = load_data(folder_path)

# Class names atributtes aka health status
# class_names = train_ds.class_names
# print(class_names)

# Show samples of the dataset
# plt.figure(figsize=(10, 10))
# for images, labels in train_ds.take(1):
#   for i in range(9):
#     ax = plt.subplot(3, 3, i + 1)
#     plt.imshow(images[i].numpy().astype("uint8"))
#     plt.title(class_names[labels[i]])
#     plt.axis("off")


# Notice the pixel values are now in `[0,1]`.
train_normalized_ds = augment_model(train_ds)
val_normalized_ds = normalized_model(val_ds)

# show
# image_batch, labels_batch = next(iter(train_normalized_ds))
# first_image = image_batch[0]
# Notice the pixel values are now in `[0,1]`.
# print(np.min(first_image), np.max(first_image))

model = build_model(train_normalized_ds, val_normalized_ds)

######################## Train model ######################## https://www.tensorflow.org/tutorials/keras/save_and_load#checkpoint_callback_options

# # Evaluate the model
# loss, acc = model.evaluate(image_batch, labels_batch, verbose=2)
# print("Untrained model, accuracy: {:5.2f}%".format(100 * acc))

# # Loads the weights
# model.load_weights(checkpoint_path)

# # Re-evaluate the model
# loss, acc = model.evaluate(image_batch, labels_batch, verbose=2)
# print("Restored model, accuracy: {:5.2f}%".format(100 * acc))

model_path = "Training/MyModel.keras"
checkpoint_path = "Training/cp.ckpt"
checkpoint_dir = os.path.dirname(checkpoint_path)

# model.load_weights(checkpoint_path) # load checkpoint

# Create a callback that saves the model's weights
keras_callbacks   = [
    ModelCheckpoint(
        checkpoint_path, 
        monitor='val_loss', 
        verbose=1, 
        save_best_only=True, 
        save_weights_only=True,
        mode='min'
    )
]

# Train
model.fit(
    train_normalized_ds,
    validation_data=val_normalized_ds,
    epochs=epoch,
    batch_size=batch_size,
    callbacks=[keras_callbacks]  # Pass callback to training
)

model.save(model_path)

######################## Save complet mode to H5 ########################
# model_final = "/Training/model_Health.h5"
# checkpoint_path = "/Training/"

# model.load_weights(checkpoint_path) # load checkpoint

# model.save(model_final, save_format="h5")