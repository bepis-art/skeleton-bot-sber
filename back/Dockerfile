FROM python:3.11-alpine3.21
WORKDIR /back
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn","main:app"]
