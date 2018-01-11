# amazon_scraper

Sending price alerts for amazon.de articles straight to your inbox

Insert your mail addr, server, user and pass in the code, edit the amazon_input.json or 
amazon_input.csv to your liking, add a cronjob and wait for the mails to come.

Sample crontab(5):

`*/10 * * * * cd /path/to/amazon_scraper && ./amazon_scraper.py --json &> /dev/null`
