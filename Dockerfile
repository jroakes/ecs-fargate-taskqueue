FROM python:3
LABEL maintainer="JR Oakes <jroakes@gmail.com>"

RUN apt-get update && \
    apt-get install python-dev python-pip -y && \
    apt-get clean

WORKDIR /tmp/workdir

COPY /project/ /tmp/workdir

COPY src/ap_helper.py /tmp/workdir
COPY src/handler.py /tmp/workdir
COPY .env /tmp/workdir

RUN pip install spacy
RUN python -m spacy download en_core_web_sm

RUN pip install -r requirements.txt

CMD ["python", "handler.py"]
