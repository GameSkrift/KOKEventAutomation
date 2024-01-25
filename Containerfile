FROM python:latest as builder

LABEL \
  org.opencontainers.image.author="Sheldon Knuth <sheruost@duck.com>" \
  org.opencontainers.image.licenses=GPL-3.0 \
  com.github.GameSkrift="KOKEventAutomation" \
  version="0.1" \
  description="provide game event automation by RESTful requests."

# Create a new user
RUN useradd \
  --uid 1000 \
  --home-dir /app \
  --create-home \
  --shell /bin/bash \
  runner

USER runner 
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY \
  --chown=runner:runner \
  --chmod=700 \
  . .

FROM builder
ENTRYPOINT ["python3", "MultiverseDating.py"]
