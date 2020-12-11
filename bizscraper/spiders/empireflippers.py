import scrapy
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup 
from bizscraper.items import BizscraperItem
from bizscraper.utils import cleanItem


class EmpireflippersScraper(scrapy.Spider):
    name = "empireflippers"
    start_urls = [
        'https://empireflippers.com/marketplace/'
    ]
    def parse(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      for item in soup.findAll('div', class_='listing-item'):
        wrapper = item.find('div', class_='row')
        cols = wrapper.findAll('div', class_='col')
       
        item = BizscraperItem()
        item['Source'] = self.name
        item['Listing_Title'] = cols[2].find('h5').text.strip()
        item['Listing_URL'] = cols[2].find('a').attrs['href']
        item['Asking_Price'] = cleanItem(cols[4].text.strip())
        item['Cash_Flow'] = cleanItem(cols[5].text.strip()) * 12
        item['Multiple'] = round(item['Asking_Price']/item['Cash_Flow'], 3)
        item['Scraped_At'] = datetime.now()
        item['Category'] = cols[3].text.strip()
        yield scrapy.Request(url=item['Listing_URL'], callback=self.parse_detail, meta={'item': item}, method="GET")
    
    def parse_detail(self, response):
      item = response.meta['item']
      soup = BeautifulSoup(response.body, features="html.parser")
      if soup.find('div', class_='sites-summary_left'):
        item['Gross_Revenue'] = cleanItem(soup.find('div', class_='sites-summary_left').find('ul').findAll('li')[2].text.strip().replace('Monthly Revenue', '')) * 12
        print('==================================')
        print(item)
        print('===================================')
        item['Listing_Description'] = soup.find('div', class_='sites-summary_left').text.replace(soup.find('div', class_='sites-summary_left').find('ul').text, '')
      yield item
     
