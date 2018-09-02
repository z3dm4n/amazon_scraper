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
# Version: 0.1.1
#
##

import csv
import json
import os
import random
import smtplib
import sys
from time import sleep
from lxml import html
import requests

def parse(url):
    # https://gist.github.com/scrapehero/0b8b4aeea00ff3abf3bc72a9e9d26849
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) \
            Gecko/20100101 Firefox/57.0'}
    page = requests.get(url, headers=headers)

    for i in range(20):
        sleep(random.randint(1, 3))
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
    SUBJECT = 'amazon price alarm'
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

def read_asin_from_csv(csv_input_file):
    f = open(csv_input_file, 'r', newline='')
    csv_reader = csv.DictReader(f, delimiter=';')
    print('Reading ' + csv_input_file + '...')
    asin_list = []
    for row in csv_reader:
        asin_list.append(row['ASIN'])
    f.close()
    return asin_list

def write_csv_header(csv_output_file):
    if os.path.isfile(csv_output_file):
        os.remove(csv_output_file)
    f = open(csv_output_file, 'w', newline='')
    fieldnames = ['NAME',
                  'SALE_PRICE',
                  'CATEGORY',
                  'ORIGINAL_PRICE',
                  'AVAILABILITY',
                  'URL']
    csv_writer = csv.DictWriter(f, delimiter=';', fieldnames=fieldnames)
    csv_writer.writeheader()
    print('Writing CSV header to ' + csv_output_file + '...')
    f.close()

def write_csv(csv_output_file, data):
    f = open(csv_output_file, 'a', newline='')
    fieldnames = ['NAME',
                  'SALE_PRICE',
                  'CATEGORY',
                  'ORIGINAL_PRICE',
                  'AVAILABILITY',
                  'URL']
    csv_writer = csv.DictWriter(f, delimiter=';', fieldnames=fieldnames)
    csv_writer.writerow({'NAME': data['NAME'],
                         'SALE_PRICE': data['SALE_PRICE'],
                         'CATEGORY': data['CATEGORY'],
                         'ORIGINAL_PRICE': data['ORIGINAL_PRICE'],
                         'AVAILABILITY': data['AVAILABILITY'],
                         'URL': data['URL']})
    print('Writing to ' + csv_output_file + '...')
    f.close()

def read_wishprice_from_csv(csv_input_file):
    f = open(csv_input_file, 'r')
    print('Reading WISH_PRICE from ' + csv_input_file + '...')
    wish_list = []
    csv_reader = csv.DictReader(f, delimiter=';')
    for row in csv_reader:
        wish_list.append(row['WISH_PRICE'].replace(',', '.'))
        # replaces , with . in WISH_PRICE
    f.close()
    return wish_list

def read_saleprice_from_csv(csv_output_file):
    f = open(csv_output_file, 'r')
    print('Reading SALE_PRICE from ' + csv_output_file + '...')
    sale_list = []
    csv_reader = csv.DictReader(f, delimiter=';')
    for row in csv_reader:
        sale_list.append(row['SALE_PRICE'][4:].replace(',', '.'))
        #removes EUR from SALE_Price and replaces , with .
    f.close()
    return sale_list

def read_asin_from_json(json_input_file):
    f = open(json_input_file, 'r')
    print('Reading ' + json_input_file + '...')
    asin_list = []
    json_reader = json.load(f)
    for row in json_reader:
        asin_list.append(row['ASIN'])
    f.close()
    return asin_list

def write_json(json_output_file, extracted_data):
    f = open(json_output_file, 'w', newline='')
    json.dump(extracted_data, f, indent=4)
    print('Writing to ' + json_output_file + '...')
    f.close()

def read_wishprice_from_json(json_input_file):
    f = open(json_input_file, 'r')
    print('Reading WISH_PRICE from ' + json_input_file + '...')
    wish_list = []
    json_reader = json.load(f)
    for row in json_reader:
        wish_list.append(row['WISH_PRICE'].replace(',', '.'))
        # replaces , with . in WISH_PRICE
    f.close()
    return wish_list

def read_saleprice_from_json(json_output_file):
    f = open(json_output_file, 'r')
    print('Reading SALE_PRICE from ' + json_output_file + '...')
    sale_list = []
    json_reader = json.load(f)
    for row in json_reader:
        sale_list.append(row['SALE_PRICE'][4:].replace(',', '.'))
        #removes EUR from SALE_Price and replaces , with .
    f.close()
    return sale_list

def compare(input_file, output_file, url_list):
    if sys.argv[1] == '--csv':
        wish_list = read_wishprice_from_csv(input_file)
        sale_list = read_saleprice_from_csv(output_file)
        print('Comparing prices...')
        for (wish_price, sale_price, url) in zip(wish_list, sale_list, url_list):
            # Fixing numbers >= 1.000,00
            # https://stackoverflow.com/questions/7106417/convert-decimal-mark
            if float(sale_price.replace(".", "", sale_price.count(".") -1)) <= \
                    float(wish_price.replace(".", "", wish_price.count(".") -1)):
                send(url)
    elif sys.argv[1] == '--json':
        wish_list = read_wishprice_from_json(input_file)
        sale_list = read_saleprice_from_json(output_file)
        print('Comparing prices...')
        for (wish_price, sale_price, url) in zip(wish_list, sale_list, url_list):
            # Fixing numbers >= 1.000,00
            # https://stackoverflow.com/questions/7106417/convert-decimal-mark
            if float(sale_price.replace(".", "", sale_price.count(".") -1)) <= \
                    float(wish_price.replace(".", "", wish_price.count(".") -1)):
                send(url)

def main():
    csv_input_file = 'amazon_input.csv'
    csv_output_file = 'amazon_output.csv'
    json_input_file = 'amazon_input.json'
    json_output_file = 'amazon_output.json'

    if len(sys.argv) != 2:
        print('Error: usage: {0} --json|--csv'.format(sys.argv[0]))
        sys.exit(1)
    elif sys.argv[1] == '--csv':
        ##CSV part:
        if not csv_input_file or not os.path.isfile(csv_input_file):
            print('Error ' + csv_input_file + ' is missing.')
            sys.exit(1)
        write_csv_header(csv_output_file)
        url_list = []
        asin_list = read_asin_from_csv(csv_input_file)
        for asin in asin_list:
            url = 'http://www.amazon.de/dp/' + asin
            url_list.append(url)
            print('Processing: ' + url)
            data = parse(url)
            write_csv(csv_output_file, data)
            sleep(1)
        compare(csv_input_file, csv_output_file, url_list)
    elif sys.argv[1] == '--json':
        ##Json part:
        if not json_input_file or not os.path.isfile(json_input_file):
            print('Error ' + json_input_file + ' is missing.')
            sys.exit(1)
        url_list = []
        extracted_data = []
        asin_list = read_asin_from_json(json_input_file)
        for asin in asin_list:
            url = 'http://www.amazon.de/dp/' + asin
            url_list.append(url)
            print('Processing: ' + url)
            extracted_data.append(parse(url))
            write_json(json_output_file, extracted_data)
            sleep(1)
        compare(json_input_file, json_output_file, url_list)
    else:
        print('Error: usage: {0} --json|--csv'.format(sys.argv[0]))
        sys.exit(1)

if __name__ == '__main__':
    main()
