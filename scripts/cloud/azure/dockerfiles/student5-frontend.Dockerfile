FROM python:3.12-slim

WORKDIR /app

COPY student-5/frontend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir \
    -r requirements.txt \
    requests==2.32.5

COPY student-5/frontend/templates/ ./templates/
COPY student-5/frontend/static/ ./static/

COPY scripts/cloud/azure/adapters/student5-app.py ./app.py

EXPOSE 8005

CMD ["python", "app.py"]
