#!/usr/bin/bash

configpath=$1
container="donrkabob/lottobuddy:latest"


docker run -p 5000:5000 -v ${configpath}:/config -d --name lottobuddy ${container}
