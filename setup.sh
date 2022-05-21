#!/usr/bin/bash

configpath=$1
container="donrkabob/lottobuddy:latest"

docker run -p 5000:5000 -v ${configpath}:/config -ti ${container} --setup --configfile /config/lotto_config.json --tdaconfig /config/tda-config.json
