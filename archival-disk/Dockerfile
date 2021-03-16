#
# Uncomment when pyclowder uses Python 3+
#
#FROM clowder/pyclowder:2

FROM python:3

MAINTAINER Mike Lambert <lambert8@illinois.edu>

ENV RABBITMQ_QUEUE="ncsa.archival.disk" \
    RABBITMQ_URI="" \
    RABBITMQ_EXCHANGE="clowder" \
    MAIN_SCRIPT="disk-archival.py"

WORKDIR /home/clowder
COPY requirements.txt /home/clowder/

RUN apt-get -qq update && \
    apt-get -qq install --no-install-recommends \
      software-properties-common && \
    pip install pyclowder && \
    pip install -r /home/clowder/requirements.txt

COPY entrypoint.sh disk-archival.py extractor_info.json /home/clowder/

ENTRYPOINT ["/home/clowder/entrypoint.sh"]
CMD ["extractor"]
