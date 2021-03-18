FROM python:3.9

WORKDIR /app

COPY requirements-bot.txt ./
RUN pip install --no-cache-dir -r requirements-bot.txt

COPY . .

CMD [ "python", "-m", "bot" ]
