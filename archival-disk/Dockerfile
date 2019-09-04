FROM clowder/pyclowder:2

MAINTAINER Mike Lambert <lambert8@illinois.edu>

ENV RABBITMQ_QUEUE="ncsa.archival.disk" \
    RABBITMQ_URI="" \
    RABBITMQ_EXCHANGE="clowder" \
    MAIN_SCRIPT="disk-archival.py"

COPY requirements.txt entrypoint.sh disk-archival.py extractor_info.json /home/clowder/

RUN apt-get update && apt-get -y install python-dev \
    python-pip \
    software-properties-common && \
    apt-add-repository ppa:ubuntugis/ppa && \
    pip install --upgrade pip==9.0.3 && \
    pip install -r /home/clowder/requirements.txt

ENTRYPOINT ["/home/clowder/entrypoint.sh"]
CMD ["extractor"]
