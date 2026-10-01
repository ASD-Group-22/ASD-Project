FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY release1.py .
COPY prompts ./prompts
RUN mkdir -p /app/logs
EXPOSE 8055
CMD ["python", "app.py"]
