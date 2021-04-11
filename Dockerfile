FROM python:3.9.4

WORKDIR /usr/src/chess-bot

RUN pip install poetry
COPY . .

RUN poetry config virtualenvs.create false \
 && poetry install --no-dev --no-interaction

COPY --from=tomasfarias/cgf:0.2.3 /bin/cgf /usr/local/bin/cgf
COPY --from=tomasfarias/c2g:0.2.1 /c2g /usr/local/bin/c2g

RUN chmod +x /usr/local/bin/cgf && chmod +x /usr/local/bin/c2g

CMD ["chess-bot", "--debug"]
