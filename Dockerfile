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


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# install packages to cache
COPY package.json /usr/src/app
RUN npm install

COPY . /usr/src/app
EXPOSE 3000
CMD ["npm", "run", "start"]

