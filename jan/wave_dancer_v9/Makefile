.PHONY: model_short_training model_long_training clean_model clean_data default data submission

# Name of the data file
FILE=#replays-20170930-sample.zip

# Halite binary address - please change here if you're not using MacOS
HALITE_BINARY_ADDRESS=https://halite.io/assets/downloads/Halite2_Windows.zip

# There is nothing special about this seed (other that it's the 1 milionth prime) .
SEED=15485863

SOURCES_FOR_TRAINING= tsmlstarterbot/common.py \
	tsmlstarterbot/neural_net.py tsmlstarterbot/parsing.py \
	tsmlstarterbot/train.py
SOURCES_FOR_MULTIPLAYER_TRAINING= tsmlstarterbot/common.py \
		tsmlstarterbot/neural_net_4player.py tsmlstarterbot/parsing.py \
		tsmlstarterbot/train_4player.py
SOURCES_FOR_TWOPLAYER_TRAINING= tsmlstarterbot/common.py \
				tsmlstarterbot/neural_net_2player.py tsmlstarterbot/parsing.py \
				tsmlstarterbot/train_2player.py

default: model_multi_training

model_dual_training: models/model_dual_training.ckpt.meta

model_multi_training: models/model_multi_training.ckpt.meta

model_long_training: models/model_long_training.ckpt.meta

model_short_training: models/model_short_training.ckpt.meta

models/model_dual_training.ckpt.meta: E:/CleanedData2/${FILE} ${SOURCES_FOR_TWOPLAYER_TRAINING}
		mkdir -p models/
		python -m tsmlstarterbot.train_2player --model_name model_dual_training --data E:/CleanedData2/${FILE}  --games_limit 1000 --steps 5000 --seed ${SEED}

models/model_multi_training.ckpt.meta: E:/CleanedData/${FILE} ${SOURCES_FOR_MULTIPLAYER_TRAINING}
	mkdir -p models/
	python -m tsmlstarterbot.train_4player --model_name model_multi_training --data E:/CleanedData/${FILE}  --games_limit 150 --steps 5000 --seed ${SEED}
models/model_long_training.ckpt.meta: data/${FILE} ${SOURCES_FOR_TRAINING}
	mkdir -p models/
	python -m tsmlstarterbot.train --model_name model_long_training --data C:/Users/2015/Halite2ML/data/${FILE} --games_limit 1000 --steps 5000 --seed ${SEED}

models/model_short_training.ckpt.meta: data/${FILE} ${SOURCES_FOR_TRAINING}
	mkdir -p models/
	python -m tsmlstarterbot.train --model_name model_short_training --data data/${FILE} --games_limit 10 --steps 500 --seed ${SEED}

clean_model:
	rm -rf models

clean_data:
	rm -rf data

real_clean: clean_model clean_data
	rm -f submission.zip
	rm -f bin/halite

data: data/${FILE}

data/${FILE}:
	mkdir -p data
	curl https://storage.googleapis.com/ml-bot-data/${FILE} -o C:/Users/2015/Halite2ML/data/${FILE}

bin/halite:
	curl $(HALITE_BINARY_ADDRESS) -o C:/Users/2015/Halite2ML/data/halite_binary.zip
	unzip halite_binary.zip -d bin
	rm -rf halite_binary.zip

compare: bin/compare.sh MyBotShortTraining.py MyBot.py model_short_training model_long_training bin/halite
	bin/compare.sh MyBotShortTraining.py MyBot.py

submission:
	zip -r submission.zip MyBot.py LANGUAGE hlt/ tsmlstarterbot/ models/
