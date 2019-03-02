FROM ubuntu:18.04

COPY app /app

WORKDIR /app

RUN apt update && apt upgrade -y &&\
apt install texlive-xetex texlive-science texlive-pictures pdf2svg --no-install-recommends -y &&\
apt install python3-pip -y &&\
pip3 install -r requirements.txt &&\
apt purge python3-pip && apt autoremove

ENTRYPOINT [ "uvicorn", "main:app", "--host=0.0.0.0" ]