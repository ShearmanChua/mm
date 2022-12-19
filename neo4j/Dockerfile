FROM neo4j:5.2.0

RUN apt-get update
RUN apt-get -y install python3-pip vim git
RUN apt-get -y install libfreetype-dev libfreetype6 libfreetype6-dev

RUN pip install -U pip
RUN pip install fastapi pandas requests fsspec neo4j && pip install "uvicorn[standard]"
RUN pip install git+https://github.com/deepset-ai/haystack.git#egg=farm-haystack[colab]


# ADD build /build
# WORKDIR /build
# RUN make
