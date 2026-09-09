FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir flask flask-cors sqlalchemy

EXPOSE 6000

CMD ["sh", "-c", "python init_db.py && python app.py"]
