FROM python:3.12

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r ./requirements.txt

COPY src/ ./python/src/
COPY __main__.py ./python/main.py

CMD ["python", "python/main.py"]