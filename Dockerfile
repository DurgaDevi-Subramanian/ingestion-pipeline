  FROM python:3.11-slim

  RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr libgl1 libglib2.0-0 \
      && rm -rf /var/lib/apt/lists/*

  WORKDIR /code
  COPY requirements-api.txt requirements-docling.txt ./
  RUN pip install --no-cache-dir -r requirements-api.txt
  # CPU-only PyTorch keeps the image far smaller than the default GPU build
  RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
      && pip install --no-cache-dir -r requirements-docling.txt

  RUN useradd -m -u 1000 user
  USER user
  ENV HOME=/home/user
  WORKDIR /home/user/app
  COPY --chown=user app ./app

  ENV TESSERACT_CMD=/usr/bin/tesseract
  EXPOSE 7860
  CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]