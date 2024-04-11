FROM python:3.9-slim

LABEL maintainer="Liz Ing-Simmons <liz.ing-simmons@kcl.ac.uk>"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt gunicorn


COPY . /app

EXPOSE 8000

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000"]
ENTRYPOINT ["./entrypoint.sh"]