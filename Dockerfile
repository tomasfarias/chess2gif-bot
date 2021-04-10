FROM python:3.9.2

WORKDIR /usr/src/chess-bot

RUN pip install poetry
COPY . .

RUN poetry config virtualenvs.create false \
 && poetry install --no-dev --no-interaction

CMD ["chess-bot", "--debug"]
