#!/usr/bin/bash

tag="latest"

configpath=$1
container="donrkabob/lottobuddy:latest"


docker run -p 5000:5000 -v ${configpath}:/config -ti ${container} --setup
