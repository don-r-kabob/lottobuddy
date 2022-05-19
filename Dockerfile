FROM flask
MAINTAINER	don.r.kabob

RUN echo "Making stuff"
RUN /usr/bin/bash -c "mkdir -p /lottobuddy/templates"

ADD flask_buddy.py /lottobuddy/
ADD templates/ /lottobuddy/templates/

EXPOSE 5000 5000
ENTRYPOINT ["python3", "/lottobuddy/flask_buddy.py", "--configfile",  "/config/lotto_config.json", "--tdaconfig" , "/config/tda-config.json"]
VOLUME "/config"
