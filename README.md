# camelopardalis

If running locally without docker, you will need node v9.5.0 and Python 3.6.  You will also need to specify the configuration (we will not provide credentials to access the live exchanges). The following is an example of an `config.ini` file. This needs to be placed in the `bot-engines/crypto` directory.

For persistence, this project uses google cloud storage. You will need to get service credentials from the google console to build the project. For the submission, a file called `camelopardalis-service-key.json` will be provided. This file should already be placed in the root of the project (directory containing `Dockerfile`). To enable persistence, set the `useCloudStorage` setting to `true` and set the environment variable `GOOGLE_APPLICATION_CREDENTIALS=/camelopardalis-service-key.json`.

```
[hitbtc]
BaseUrl = https://api.hitbtc.com/api/2
Key = KEY
Secret = SECRET
Mock = True
MinutesToTimeout = 5
Wrapper = HitBTCExchange
Strategy = BasicStrategy
Symbols = ETHBTC,LTCBTC,ETCBTC

[bitmex]
BaseUrl = https://testnet.bitmex.com/api/v1
Key = KEY
Secret = SECRET
Mock = False
MinutesToTimeout = 60
Wrapper = BitMEXExchange
Strategy = SignalStrategy
Symbols = XBTUSD,XBTJPY
Indicators = RSI,MACD,STOCHRSI,AROON_OSCILLATOR,MFI,CCI,CMO,MACD_HIST,WILLR
# market configurations: long_cap,short_cap,bin,long_score,short_score,min_volume
XBTUSD = 1000,1000,100,.15,-.15,10
XBTJPY = 1000,1000,100,.15,-.15,10
```

### The easy way:

Download docker from https://www.docker.com/get-docker and then from within the folder containing the Dockerfile, run, `make run-docker`. Navigate to localhost:3000 and you should see the application. Note, if you are on MacOS, you may need to navigate to 192.168.99.100:3000 since Docker is running on another VM.

### The hard way:

The following will need to be done on the command line. This way will run the application from your own machine. 

* First, make sure you have Python 3.6 and node v9.5 installed. 
* Navigate to the source directory. In the directory containing the package.json file, invoke, `npm install`. This will install the node dependencies. 
* Navigate to the bot-exchanges directory, invoke `python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt`. This will install the python dependencies. Modify the config.ini file to contain the appropriate API keys and secrets for the exchanges. 
* Now run, npm run start. This will launch the node process (and the bot processes as well). Now navigate to localhost:3000, you should see the project live at this point.

### Deploying to google cloud:

You may not get to this point, but deploying to google cloud will require some effort.
* First download and initialize the gcloud cli sdk from https://cloud.google.com/sdk/downloads
* Install docker from https://www.docker.com/get-docker
* Run the gcloud project initialization code in the file init_gcp_project.sh
* If you receive errors at this step, you may end up needing to change the PROJECT_NAME variable in init_gcp_project.sh to a unique value.
At this point you will have a project setup on google cloud platform, however you will need to enable billing for this project, refer to https://cloud.google.com/billing/docs/how-to/modify-project
* With billing setup, you can now deploy the docker image to google cloud. Invoke `make create-container-vm` and follow the prompts. The dialogue will give you an IP address that you can use to access the site. (You may need to setup ingress firewalls for your project if the project is exposed on a non-standard port).
