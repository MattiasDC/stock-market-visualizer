FROM python:3.9-buster

RUN mkdir -p /app

# set working directory
WORKDIR /app

# add requirements (to leverage Docker cache)
COPY ./requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt

ENV PYTHONPATH="${PYTHONPATH}:/app"

EXPOSE 8000
COPY . .
CMD ["python", "stock_market_visualizer/app/main.py", "--host", "0.0.0.0"]