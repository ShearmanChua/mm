FROM nvcr.io/nvidia/pytorch:20.12-py3

RUN apt-get update
RUN apt-get -y install python3-pip vim git
RUN apt-get -y install libfreetype-dev libfreetype6 libfreetype6-dev

RUN pip install -U pip
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install -U spacy-cleaner
RUN python3 -m spacy download en_core_web_sm

RUN mkdir /evaluation && mkdir /evaluation/notebooks && mkdir /evaluation/src mkdir /evaluation/data
WORKDIR /evaluation
