FROM python:3

WORKDIR /app

RUN adduser dbarunner
USER dbarunner
WORKDIR /app

COPY /build/requirements.txt requirements.txt
COPY --chown=dbarunner:dbarunner /build/requirements.txt requirements.txt

COPY /app /app
# ENV PATH="/home/dbapgtools/.local/bin:${PATH}"

COPY --chown=dbarunner:dbarunner . .

RUN pip install --no-cache-dir --user -r requirements.txt
