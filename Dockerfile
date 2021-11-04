FROM python:3.9-slim-buster

RUN mkdir -p /app

# set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y git
RUN python -m pip install --no-cache-dir --upgrade pip

COPY setup.py .
COPY pyproject.toml .
COPY setup.cfg .

COPY ./stock_market_visualizer ./stock_market_visualizer

RUN pip install -e . --no-cache-dir

EXPOSE 8000
CMD ["python", "stock_market_visualizer/app/main.py", "--host", "0.0.0.0"]