FROM python:3.10

WORKDIR /app

RUN apt update
RUN apt install -y awscli
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin

RUN adduser dbarunner
USER dbarunner
WORKDIR /app

COPY /build/requirements.txt requirements.txt
COPY --chown=dbarunner:dbarunner /build/requirements.txt requirements.txt

COPY /app /app
# ENV PATH="/home/dbapgtools/.local/bin:${PATH}"

COPY --chown=dbarunner:dbarunner . .

RUN pip install --no-cache-dir --user -r requirements.txt
