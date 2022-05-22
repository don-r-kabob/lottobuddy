# Features

#### Dashboard

1. Net premium sold today
2. Net # of units for both calls and puts
3. BP/NLV summary
4. Order's used today (includes futures)
5. List of outstanding premium and marks by expiration date
	- Does not include closed positions (i.e. buybacks)
6. 20 positions closest to being ITM

#### Red alert

1. List of all positions <40% OTM

# Setup

What you will need:

- TDA API Account (step 1)
  
  	- Both the API key for the app you register and the callback url
- PM Account number
- Docker (step 2)

1. Create an account for TDA API
	- Create an app, name doesn't matter
	- Create a callback uri 
		- use "https://localhost" if you don't have a better one, it won't matter, just need to be something
2. If you want to use docker
   - Download docker desktop and install for your OS (https://www.docker.com/products/docker-desktop)


## Docker instructions

Note you will need to use the full path to the directory with
the configuration file and API access token these instructions will
assume that you are putting them in the "config" folder in the same directory

These commands are for *nix systems. If anyone could help me with windows instructions I would appreciate it
I will gladly make/maintain batch scripts for windows once I can test out what should be in it

1. Download docker desktop
2. Pull the container

	docker pull donrkabob/lottobuddy:latest

3. Create the config file (TDA api app key/url)

		mkdir config
		docker run -p 5000:5000 -v `pwd`/config:/config donrkabob/lottobuddy:latest --setup --tdaconfig /config/tda-config.json --configfile /config/lotto_config.json
   	
4. Set up API access refresh token

		docker run -p 5000:5000 -v `pwd`/config:/config donrkabob/lottobuddy:latest --newtoken --tdaconfig /config/tda-config.json --configfile /config/lotto_config.json

5. Run the thing!

		docker run -p 5000:5000 -v `pwd`/config:/config donrkabob/lottobuddy:latest --newtoken --tdaconfig /config/tda-config.json --configfile /config/lotto_config.json
		
		

	

## No docker cause i'm cool instructions:

the libraries you need are in the docker file and they will maintain the most up to date requirements.

### General linux instruction

Install libraries

		pip3 install pandas
		pip3 install tda-api flask

With these installed you can run:

	python3 flask_buddy.py --setup
	python3 flask_buddy.py --newtoken
	python3 flask_buddy.py 

### Step-by-step Mac instructions

1. Do you have git installed?
	- Try the command: 
	  
			which git
	
	- See if you have python3
	
			which python3
	
	- If it return nothing then it is not install otherwise it will print a system path
	- If it gives you an error you don't and let's install command line tools from apple 
	  	
			xcode-select --install
	
2. OK - do you need pip? If running "pip3" does not work then below will install pip

		curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
		sudo python3 get-pip.py

3. Install packages
	
		pip3 install --user pandas
		pip3 install --user tda-api flask

4. Clone repo

		git clone https://github.com/don-r-kebab/lottobuddy.git

5. Move into that directory

		cd lottobuddy

6. Set up config file

		python3 flask_buddy.py --setup

7. Create token file

		python3 flask_buddy.py --newtoken

8. Run it!

		python3 flask_buddy.py

## Using

Most of the data is all on the dashboard. There is a link strip on top 
- "STATS": The Main Dashboard
- "RED_ALERT": list all positions < 40% OTM

## File Formats

config file (json)

	{
		"apikey": "<API key>", 
		"callbackuri": "<callback url provided to TD API>", 
		"accountnum": "<account number>", 
		"tokenpath": "<API token file path>"
	}

tokenpath will be set automatically, but can be changed manually either by hand
in the config file or by command line option if desired.