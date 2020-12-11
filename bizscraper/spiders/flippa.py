import scrapy
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup 
from bizscraper.settings import SCRAPER_API
from bizscraper.items import BizscraperItem
from bizscraper.utils import cleanItem


class FlippaScraper(scrapy.Spider):
    name = "flippa"
    start_urls = [
        'https://flippa.com/search'
    ]
    base_url = 'https://flippa.com/'
    page_url= 'https://flippa.com/search?search_template=most_relevant&page%5Bnumber%5D={}&filter%5Bsale_method%5D=auction,classified&filter%5Bstatus%5D=open&filter%5Bproperty_type%5D=website,established_website,starter_site,fba,ios_app,android_app'
    def parse(self, response):
      state = response.body.split('const STATE = ')[1].split('const DEFAULT_SEARCH_PARAMS = ')[0].strip()[:-1]
      print(json.loads(state))
      totalResults = int(str(response.body).split('const STATE = ')[1].split('const DEFAULT_SEARCH_PARAMS = ')[0].strip().replace('\\', '').replace('\n', '')[:-1].split('"totalResults":')[1].split('}}')[0])
      print(totalResults)
      for page in range(0, int(totalResults / 25) + 1):
      # for page in range(0, page_count):
        yield scrapy.Request(url=SCRAPER_API + self.page_url.format(page), callback=self.parse_list, method="GET")
      
    def parse_list(self, response):
      state = response.body.split('const STATE = ')[1].split('const DEFAULT_SEARCH_PARAMS = ')[0].strip()[:-1]
      # print(state)
      for row in json.loads(state)['listings']:
        item = BizscraperItem()
        item['Source'] = self.name
        item['Listing_Title'] = row['property_name']
        item['Listing_URL'] = row['listing_url']
        item['Category'] = row['monetization']
        item['Asking_Price'] = row['price']
        item['Listing_Description'] = row['summary']
        item['Scraped_At'] = datetime.now() 
        if 'profit_average' in row and row['profit_average']:
          item['Cash_Flow'] = row['profit_average'] * 12
        if item['Asking_Price'] and 'Cash_Flow' in item and item['Cash_Flow'] != 0:
          item['Multiple'] = round(item['Asking_Price']/item['Cash_Flow'], 3)
        yield item