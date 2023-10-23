install:
	poetry install

unittest:
	poetry run coverage run -m unittest discover
	poetry run coverage report

freeze:
	poetry export --without-hashes --format=requirements.txt > requirements.txt

train:
	poetry run python train.py

evaluate:
	poetry run python evaluate.py