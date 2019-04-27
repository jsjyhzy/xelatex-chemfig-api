FROM ubuntu:18.04

COPY app /app

WORKDIR /app

RUN apt update && apt upgrade -y &&\
apt install python3-pip -y &&\
pip3 install -r requirements.txt &&\
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys D6BC243565B2087BC3F897C9277A7293F59E4889 &&\
echo "deb http://miktex.org/download/ubuntu bionic universe" | tee -a /etc/apt/sources.list.d/miktex.list &&\
apt-get update &&\
apt install miktex pdf2svg -y &&\
miktexsetup finish &&\
initexmf --set-config-value [MPM]AutoInstall=1

RUN mpm --install xecjk &&\
mpm --install chemfig

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8

ENTRYPOINT [ "uvicorn", "main:app", "--host=0.0.0.0", "--port=80" ]