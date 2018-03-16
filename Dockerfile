FROM node:9.5-wheezy
MAINTAINER camelopardalis

# update the packages
RUN apt-get -y update \
    && apt-get install -y python make build-essential libssl-dev \
        zlib1g-dev libbz2-dev

# install python 3.6
RUN wget https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tgz \
    && tar xvf Python-3.6.4.tgz \
    && cd Python-3.6.4 \
    && ./configure \
    && make \
    && make install

RUN python3 -m ensurepip --upgrade


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# install packages to cache
COPY package.json /usr/src/app
RUN npm install

RUN mkdir -p bot-engines
COPY bot-engines/requirements.txt /usr/src/app/bot-engines/requirements.txt
# install prereq ta-lib for python deps
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && tar xvf ta-lib-0.4.0-src.tar.gz && cd ta-lib && ./configure --prefix=/usr && make && make install
RUN pip3 install -r /usr/src/app/bot-engines/requirements.txt

# install gcloud
COPY camelopardalis-service-key.json /
RUN export CLOUD_SDK_REPO="cloud-sdk-wheezy" \
    && export CLOUDSDK_CORE_DISABLE_PROMPTS=1 \
    && echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
    && apt-get update && apt-get install google-cloud-sdk \
    && gcloud auth activate-service-account --key-file /camelopardalis-service-key.json \
    && gcloud config set project camelopardalis-467-1

COPY . /usr/src/app

ENV GOOGLE_APPLICATION_CREDENTIALS=/camelopardalis-service-key.json
ENV PORT=80
EXPOSE ${PORT}
CMD ["npm", "run", "start"]
