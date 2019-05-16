FROM ubuntu:18.04
COPY . /tiler
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y --no-install-recommends \
    apt-utils \
    python3.6 \
    python3-pip
RUN pip3 install setuptools
WORKDIR /tiler
RUN pip3 install -r requirements.txt
