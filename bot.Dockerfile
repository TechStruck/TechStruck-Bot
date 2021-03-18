FROM python:3.9

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements-bot.txt ./
RUN pip install --no-cache-dir -r requirements-bot.txt

COPY . .

CMD [ "python", "-m", "bot" ]
