import scrapy
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup 
from bizscraper.items import BizscraperItem
from bizscraper.utils import cleanItem


class FeinternationalScraper(scrapy.Spider):

    name = "feinternational"
    start_urls = [
        'https://feinternational.com/buy-a-website/'
    ]
    def parse(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      for row in soup.find('div', {'id': 'tabs-1'}).findAll('div', class_='listing'):
        item = BizscraperItem()
        item['Source'] = self.name
        item['Listing_Title'] = row.find('h2', class_='listing-title').text.strip()
        item['Listing_URL'] = row.find('h2', class_='listing-title').find('a').attrs['href']
        item['Listing_Description'] = row.find('div', class_='listing-description').find('p').text.strip()
        item['Asking_Price'] = cleanItem(row.find('dd', class_='listing-overview-item--asking-price').text.strip())
        item['Cash_Flow'] = cleanItem(row.find('dd', class_='listing-overview-item--yearly-profit').text.strip())
        item['Scraped_At'] = datetime.now()
        item['Gross_Revenue'] = cleanItem(row.find('dd', class_='listing-overview-item--yearly-revenue').text.strip())
        item['Category'] = item['Listing_Title'].split(' -')[0].strip()
        if item['Asking_Price'] and item['Cash_Flow'] and item['Cash_Flow'] > 0:
          item['Multiple'] = round(item['Asking_Price']/item['Cash_Flow'], 3)
          
        yield item