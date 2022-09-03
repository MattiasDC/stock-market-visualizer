FROM python:3.10-slim-buster

RUN apt-get update \
 && apt-get install -y --no-install-recommends git gcc libc6-dev \
 && rm -rf /var/lib/apt/lists/*
 
RUN mkdir -p /app

# set working directory
WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
COPY setup.cfg .

COPY ./stock_market_visualizer ./stock_market_visualizer
COPY ./default_configs ./default_configs

RUN pip install -e . --no-cache-dir


RUN apt-get purge -y --auto-remove git gcc libc6-dev \
 && apt-get purge -y --auto-remove

EXPOSE 8000
CMD ["python", "stock_market_visualizer/app/main.py", "--host", "0.0.0.0"]