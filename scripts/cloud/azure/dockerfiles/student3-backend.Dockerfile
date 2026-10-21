FROM python:3.10-slim

WORKDIR /app

COPY student-3/backend-service/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY student-3/backend-service/ /app/
COPY student-3/prompts/ /prompts/

ENV PROMPT_ROOT=/prompts

EXPOSE 5000

CMD ["python", "app.py"]
