FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /code/requirements.txt

RUN pip install --upgrade pip

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

WORKDIR /app/code

COPY . /app/code

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8092", "--reload"]