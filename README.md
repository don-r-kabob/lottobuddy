This is actually super simple. It's all set up to run in a docker container. I have included the source code
incase you would like to review. Unfortunately permission allow a lot of account privileges. All this is doing is:
    - pulling basic account stats
    - transaction/order history
    - position list

What you will need:

- TDA API Account (step 1)
  
  	- Both the API key for the app you register and the callback url
- PM Account number
- Docker (step 2)

1. Create an account for TDA API
	- Create an app, name doesn't matter
	- Create a callback uri 
		- use "https://localhost" if you don't have a better one, it won't matter, just need to be something
2. Download docker desktop and install for your OS (https://www.docker.com/products/docker-desktop)

Now you can start or stop the server from docker desktop or the command line
- start "docker start lottobuddy"
- stop "docker stop lottobuddy"
- Docker desktop use the play/stop button

## Docker instructions

Note you will need to use the full path to the directory with
the configuration file and API access token these instructions will
assume that you are putting them in the "config" folder in the same directory

1. Download docker desktop
2. Pull the container

	docker pull donrkabob/lottobuddy:latest

3. Create the config file

		mkdir config
		docker run -p 5000:5000 -v `pwd`/config:/config donrkabob/lottobuddy:latest --setup --tdaconfig /config/tda-config.json --configfile /config/lotto_config.json
   	
4. Set up API access refresh token

		docker run -p 5000:5000 -v `pwd`/config:/config donrkabob/lottobuddy:latest --newtoken --tdaconfig /config/tda-config.json --configfile /config/lotto_config.json

5. Run the thing!

   	docker run -p 5000:5000 -v `pwd`/config:/config donrkabob/lottobuddy:latest --newtoken --tdaconfig /config/tda-config.json --configfile /config/lotto_config.json
		
		

	

## No docker cause i'm cool instructions:

the libraries you need are in the docker file and thye will maintain the most up to date requirements.

pip3 install pandas
pip3 install tda-api flask

With these installed you can run:

1. python3 flask_buddy.py --setup
2. python3 flask_buddy.py --newtoken
3. python3 flask_buddy.py --configfile 

### Step-by-step Mac instructions

1. Do you have git installed?
	- Try the command: 
	  
			which git
	  
	- If it gives you an error you don't and let's install command line tools from apple 
	  	
			xcode-select --install
	
2. OK - do you need pip?

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


	

# Using

Most of the data is all on the dashboard. There is a link strip on top 
- "STATS": The Main Dashboard
- "RED_ALERT": list all positions < 40% OTM

# File Formats

config file (json)

	{
		"apikey": "<API key>", 
		"callbackuri": "<callback url provided to TD API>", 
		"accountnum": "<account number>", 
		"tokenpath": "<API token file path>"
	}

tokenpath will be set automatically, but can be changed manually if desired.