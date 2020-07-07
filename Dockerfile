FROM ubuntu:latest

COPY . .

RUN apt-get update
RUN apt-get install -y python3-pip

RUN pip3 install -r requirements.txt
RUN python3 -m pip install -U discord.py[voice]
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg

EXPOSE 27017

CMD ["python3", "bot_driver.py"]