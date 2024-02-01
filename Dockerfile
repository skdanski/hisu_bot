FROM ubuntu:latest

# copy directories
COPY ./config ./hisu_bot/config
COPY ./src ./hisu_bot/src
COPY ./dependencies.txt ./hisu_bot

# install nodejs, npm, and pm2
RUN apt-get update
RUN apt-get -y install curl
RUN apt -y install nodejs npm
RUN npm install pm2 -g

# install python3 and pip3
ENV TZ=US/Pacific
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update &&  apt install build-essential software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt install python3.11 -y
RUN apt-get -y install python3-pip

# install 3rd party python dependencies
RUN pip3 install -r ./hisu_bot/dependencies.txt
ENV PYTHONPATH=$PYTHONPATH:/hisu_bot/src/modules


# run bot
CMD ["python3", "./hisu_bot/src/hisu.py"]
# CMD ["pm2", "start", "./hisu_bot/src/hisu.py", "--name", "hisu_bot", "--interpreter", "python3"]
# pm2 start ./hisu_bot/src/hisu.py --name hisu_bot --interpreter python3