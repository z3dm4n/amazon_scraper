#!/usr/bin/env python3

##
#
# Sending price alerts for amazon.de articles straight to your inbox
#
# Insert your mail addr, server, user and pass in the code, edit the amazon_input.json
# or amazon_input.csv to your liking, add a cronjob and wait for the mails to come.
#
# Sample crontab(5):
# */10 * * * * cd /path/to/amazon_scraper && ./amazon_scraper.py --json &> /dev/null
#
# Author: z3dm4n
# Mail: erik__at__z3dm4n.net
# Date: 01/01/18
#
##

import csv
import json
import os
import requests
import smtplib
import sys
from lxml import html
from time import sleep

def parse(url):
    # https://gist.github.com/scrapehero/0b8b4aeea00ff3abf3bc72a9e9d26849
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) \
            Gecko/20100101 Firefox/57.0'}
    page = requests.get(url, headers=headers)

    for i in range(5):
        sleep(1)
        try:
            doc = html.fromstring(page.content)
            XPATH_NAME = '//h1[@id="title"]//text()'
            XPATH_SALE_PRICE = '//span[contains(@id,"ourprice") or contains(@id,"saleprice")]/text()'
            XPATH_ORIGINAL_PRICE = '//td[contains(text(),"List Price") or contains(text(),"M.R.P")\
                    or contains(text(),"Price")]/following-sibling::td/text()'
            XPATH_CATEGORY = '//a[@class="a-link-normal a-color-tertiary"]//text()'
            XPATH_AVAILABILITY = '//div[@id="availability"]//text()'
            RAW_NAME = doc.xpath(XPATH_NAME)
            RAW_SALE_PRICE = doc.xpath(XPATH_SALE_PRICE)
            RAW_CATEGORY = doc.xpath(XPATH_CATEGORY)
            RAW_ORIGINAL_PRICE = doc.xpath(XPATH_ORIGINAL_PRICE)
            RAW_AVAILABILITY = doc.xpath(XPATH_AVAILABILITY)

            NAME = ' '.join(''.join(RAW_NAME).split()) if RAW_NAME else None
            SALE_PRICE = ' '.join(''.join(RAW_SALE_PRICE).split()).strip() if RAW_SALE_PRICE else None
            CATEGORY = ' > '.join([i.strip() for i in RAW_CATEGORY]) if RAW_CATEGORY else None
            ORIGINAL_PRICE = ''.join(RAW_ORIGINAL_PRICE).strip() if RAW_ORIGINAL_PRICE else None
            AVAILABILITY = ''.join(RAW_AVAILABILITY).strip() if RAW_AVAILABILITY else None

            if not ORIGINAL_PRICE:
                ORIGINAL_PRICE = SALE_PRICE
            if not NAME:
                raise ValueError('Captcha?')

            data = {'NAME':NAME,
                    'SALE_PRICE':SALE_PRICE,
                    'CATEGORY':CATEGORY,
                    'ORIGINAL_PRICE':ORIGINAL_PRICE,
                    'AVAILABILITY':AVAILABILITY,
                    'URL':url,
                   }

            return data

        except Exception as e:
            print(e)

def send(url):
    USER = 'info@example.com' # XXX
    PASSWD = ''
    FROM = 'Firstname Lastname <info@example.com>'
    TO = ['myaddr@gmail.com'] # must be a list
    SUBJECT = 'Amazon-Preisalarm'
    text = url

    # Prepare actual message
    msg = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ', '.join(TO), SUBJECT, text)

    try:
        print('Sending mail...')
        server = smtplib.SMTP('mx.example.com', 587)
        server.ehlo()
        server.starttls()
        server.login(USER, PASSWD)
        server.sendmail(FROM, TO, msg)
        server.quit()
    except:
        print('Error: Failed to send mail.')
        sys.exit(1)

def read_asin_from_csv(csvInputFile):
    f = open(csvInputFile, 'r', newline='')
    csvReader = csv.DictReader(f, delimiter=';')
    print('Reading ' + csvInputFile + '...')
    asinList = []
    for row in csvReader:
        asinList.append(row['ASIN'])
    f.close()
    return asinList

def write_csv_header(csvOutputFile):
    if os.path.isfile(csvOutputFile):
        os.remove(csvOutputFile)
    f = open(csvOutputFile, 'w', newline='')
    fieldnames = ['NAME',
                  'SALE_PRICE',
                  'CATEGORY',
                  'ORIGINAL_PRICE',
                  'AVAILABILITY',
                  'URL']
    csvWriter = csv.DictWriter(f, delimiter=';', fieldnames=fieldnames)
    csvWriter.writeheader()
    print('Writing CSV header to ' + csvOutputFile + '...')
    f.close()

def write_csv(csvOutputFile, data):
    f = open(csvOutputFile, 'a', newline='')
    fieldnames = ['NAME',
                  'SALE_PRICE',
                  'CATEGORY',
                  'ORIGINAL_PRICE',
                  'AVAILABILITY',
                  'URL']
    csvWriter = csv.DictWriter(f, delimiter=';', fieldnames=fieldnames)
    csvWriter.writerow({'NAME': data['NAME'],
                        'SALE_PRICE': data['SALE_PRICE'],
                        'CATEGORY': data['CATEGORY'],
                        'ORIGINAL_PRICE': data['ORIGINAL_PRICE'],
                        'AVAILABILITY': data['AVAILABILITY'],
                        'URL': data['URL']})
    print('Writing to ' + csvOutputFile + '...')
    f.close()

def read_wishprice_from_csv(csvInputFile):
    f = open(csvInputFile, 'r')
    print('Reading WISH_PRICE from ' + csvInputFile + '...')
    wishList = []
    csvReader = csv.DictReader(f, delimiter=';')
    for row in csvReader:
        wishList.append(row['WISH_PRICE'].replace(',', '.'))
        # replaces , with . in WISH_PRICE
    f.close()
    return wishList

def read_saleprice_from_csv(csvOutputFile):
    f = open(csvOutputFile, 'r')
    print('Reading SALE_PRICE from ' + csvOutputFile + '...')
    saleList = []
    csvReader = csv.DictReader(f, delimiter=';')
    for row in csvReader:
        saleList.append(row['SALE_PRICE'][4:].replace(',', '.'))
        #removes EUR from SALE_Price and replaces , with .
    f.close()
    return saleList

def read_asin_from_json(jsonInputFile):
    f = open(jsonInputFile, 'r')
    print('Reading ' + jsonInputFile + '...')
    asinList = []
    jsonReader = json.load(f)
    for row in jsonReader:
        asinList.append(row['ASIN'])
    f.close()
    return asinList

def write_json(jsonOutputFile, extractedData):
    f = open(jsonOutputFile, 'w', newline='')
    json.dump(extractedData, f, indent=4)
    print('Writing to ' + jsonOutputFile + '...')
    f.close()

def read_wishprice_from_json(jsonInputFile):
    f = open(jsonInputFile, 'r')
    print('Reading WISH_PRICE from ' + jsonInputFile + '...')
    wishList = []
    jsonReader = json.load(f)
    for row in jsonReader:
        wishList.append(row['WISH_PRICE'].replace(',', '.'))
        # replaces , with . in WISH_PRICE
    f.close()
    return wishList

def read_saleprice_from_json(jsonOutputFile):
    f = open(jsonOutputFile, 'r')
    print('Reading SALE_PRICE from ' + jsonOutputFile + '...')
    saleList = []
    jsonReader = json.load(f)
    for row in jsonReader:
        saleList.append(row['SALE_PRICE'][4:].replace(',', '.'))
        #removes EUR from SALE_Price and replaces , with .
    f.close()
    return saleList

def compare(inputFile, outputFile, urlList):
    if sys.argv[1] == '--csv':
        wishList = read_wishprice_from_csv(inputFile)
        saleList = read_saleprice_from_csv(outputFile)
        print('Comparing prices...')
        for (wishPrice, salePrice, url) in zip(wishList, saleList, urlList):
            # Fixing numbers >= 1.000,00
            # https://stackoverflow.com/questions/7106417/convert-decimal-mark
            if float(salePrice.replace(".", "", salePrice.count(".") -1)) <= \
                    float(wishPrice.replace(".", "", wishPrice.count(".") -1)):
                send(url)
    elif sys.argv[1] == '--json':
        wishList = read_wishprice_from_json(inputFile)
        saleList = read_saleprice_from_json(outputFile)
        print('Comparing prices...')
        for (wishPrice, salePrice, url) in zip(wishList, saleList, urlList):
            # Fixing numbers >= 1.000,00
            # https://stackoverflow.com/questions/7106417/convert-decimal-mark
            if float(salePrice.replace(".", "", salePrice.count(".") -1)) <= \
                    float(wishPrice.replace(".", "", wishPrice.count(".") -1)):
                send(url)

def main():
    csvInputFile = 'amazon_input.csv'
    csvOutputFile = 'amazon_output.csv'
    jsonInputFile = 'amazon_input.json'
    jsonOutputFile = 'amazon_output.json'

    if len(sys.argv) != 2:
        print('Error: usage: {0} --json|--csv'.format(sys.argv[0]))
        sys.exit(1)
    elif sys.argv[1] == '--csv':
        ##CSV part:
        if not csvInputFile or not os.path.isfile(csvInputFile):
            print('Error ' + csvInputFile + ' is missing.')
            sys.exit(1)
        write_csv_header(csvOutputFile)
        urlList = []
        asinList = read_asin_from_csv(csvInputFile)
        for asin in asinList:
            url = 'http://www.amazon.de/dp/' + asin
            urlList.append(url)
            print('Processing: ' + url)
            data = parse(url)
            write_csv(csvOutputFile, data)
            sleep(1)
        compare(csvInputFile, csvOutputFile, urlList)
    elif sys.argv[1] == '--json':
        ##Json part:
        if not jsonInputFile or not os.path.isfile(jsonInputFile):
            print('Error ' + jsonInputFile + ' is missing.')
            sys.exit(1)
        urlList = []
        extractedData = []
        asinList = read_asin_from_json(jsonInputFile)
        for asin in asinList:
            url = 'http://www.amazon.de/dp/' + asin
            urlList.append(url)
            print('Processing: ' + url)
            extractedData.append(parse(url))
            write_json(jsonOutputFile, extractedData)
            sleep(1)
        compare(jsonInputFile, jsonOutputFile, urlList)
    else:
        print('Error: usage: {0} --json|--csv'.format(sys.argv[0]))
        sys.exit(1)

if __name__ == '__main__':
    main()
