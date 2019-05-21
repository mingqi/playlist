FROM python:2.7-alpine

COPY . /playlist
WORKDIR /playlist
RUN pip install -r requirements.txt
