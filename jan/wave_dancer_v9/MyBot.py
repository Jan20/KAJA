import tsmlstarterbot

# Load the model from the models directory. Models directory is created during training.
# Run "make" to download data and train.
tsmlstarterbot.Bot(location4="model_multi_training.ckpt",location2="model_dual_training.ckpt", name="HappyAccident").play()
