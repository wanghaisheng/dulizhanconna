import scrapy
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup 
from bizscraper.settings import SCRAPER_API
from bizscraper.items import BizscraperItem
from bizscraper.utils import cleanItem


class ExchangemarketplaceScraper(scrapy.Spider):
    name = "exchangemarketplace"
    category_urls = [
      'https://exchangemarketplace.com/shops?categoryIds=1',
      'https://exchangemarketplace.com/shops?categoryIds=2',
      'https://exchangemarketplace.com/shops?categoryIds=3',
      'https://exchangemarketplace.com/shops?categoryIds=4',
      'https://exchangemarketplace.com/shops?categoryIds=5',
      'https://exchangemarketplace.com/shops?categoryIds=6',
      'https://exchangemarketplace.com/shops?categoryIds=7',
      'https://exchangemarketplace.com/shops?categoryIds=8',
      'https://exchangemarketplace.com/shops?categoryIds=9',
      'https://exchangemarketplace.com/shops?categoryIds=10',
      'https://exchangemarketplace.com/shops?categoryIds=11',
      'https://exchangemarketplace.com/shops?categoryIds=12',
      'https://exchangemarketplace.com/shops?categoryIds=13',
      'https://exchangemarketplace.com/shops?categoryIds=14',
      'https://exchangemarketplace.com/shops?categoryIds=15',
      'https://exchangemarketplace.com/shops?categoryIds=16',
      'https://exchangemarketplace.com/shops?categoryIds=18',
      'https://exchangemarketplace.com/shops?categoryIds=1547'
    ]
    categories = {
      'https://exchangemarketplace.com/shops?categoryIds=1': 'Fashion and apparel',
      'https://exchangemarketplace.com/shops?categoryIds=2': 'Gift and collectibles',
      'https://exchangemarketplace.com/shops?categoryIds=3': 'Sports and recreation',
      'https://exchangemarketplace.com/shops?categoryIds=4': 'Toys and games',
      'https://exchangemarketplace.com/shops?categoryIds=5': 'Stationery and office supplies',
      'https://exchangemarketplace.com/shops?categoryIds=6': 'Services and Consulting',
      'https://exchangemarketplace.com/shops?categoryIds=7': 'Pets and animals',
      'https://exchangemarketplace.com/shops?categoryIds=8': 'Music',
      'https://exchangemarketplace.com/shops?categoryIds=9': 'Home and furniture',
      'https://exchangemarketplace.com/shops?categoryIds=10': 'Health and beauty',
      'https://exchangemarketplace.com/shops?categoryIds=11': 'Food and drink',
      'https://exchangemarketplace.com/shops?categoryIds=12': 'Electronics and gadgets',
      'https://exchangemarketplace.com/shops?categoryIds=13': 'Construction and industrial',
      'https://exchangemarketplace.com/shops?categoryIds=14': 'Books and magazines',
      'https://exchangemarketplace.com/shops?categoryIds=15': 'Automotive',
      'https://exchangemarketplace.com/shops?categoryIds=16': 'Arts and photography',
      'https://exchangemarketplace.com/shops?categoryIds=18': 'Starter Stores',
      'https://exchangemarketplace.com/shops?categoryIds=1547': 'General'
    }
    base_url = 'https://exchangemarketplace.com'
    
    def start_requests(self):
      for url in self.category_urls:
        yield scrapy.Request(url='{}{}'.format(SCRAPER_API, url), callback=self.parse_category, method="GET")

    def parse_category(self, response):
      parent_url = response.url.replace(SCRAPER_API, '')
      print('==================={}==================='.format(response.url))
      soup = BeautifulSoup(response.body, features="html.parser")
      if soup.find('span', class_='last'):
        last_link = soup.find('span', class_='last').find('a').attrs['href']
        page_count = int(last_link.split('page=')[1])
        print(page_count)
        for page in range(0, page_count):
          yield scrapy.Request(url='{}{}&page={}'.format(SCRAPER_API, parent_url, page + 1), callback=self.parse_list, meta={'category': self.categories[parent_url]}, method="GET")
      else:
        yield scrapy.Request(url='{}{}'.format(SCRAPER_API, parent_url), callback=self.parse_list, meta={'category': self.categories[parent_url]}, method="GET")

    def parse_list(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      for row in soup.findAll('li', class_='_3B5De'):
        item_link = row.find('a', class_='_2OuU9')
        item = BizscraperItem()
        item['Source'] = self.name
        item['Listing_Title'] = item_link.text.strip()
        item['Listing_URL'] = self.base_url + item_link.attrs['href']
        item['Listing_Description'] = row.find('div', class_='_3u-CT').find('p').text.strip()
        item['Gross_Revenue'] = cleanItem(row.findAll('div', class_='_3llXt')[0].text.strip())
        item['Scraped_At'] = datetime.now() 
        if item['Gross_Revenue']:
          item['Gross_Revenue'] = item['Gross_Revenue'] * 12
        if 'k' in row.findAll('div', class_='_3llXt')[0].text.strip():
          item['Gross_Revenue'] = item['Gross_Revenue'] * 1000
        
        item['Cash_Flow'] = cleanItem(row.findAll('div', class_='_3llXt')[1].text.strip())
        if item['Cash_Flow']:
          item['Cash_Flow'] = item['Cash_Flow'] * 12
        if 'k' in row.findAll('div', class_='_3llXt')[1].text.strip():
          item['Cash_Flow'] = item['Cash_Flow'] * 1000


        item['Inventory'] = cleanItem(row.findAll('div', class_='_3llXt')[2].text.strip())
        if item['Inventory']:
          item['Inventory'] = item['Inventory'] * 12
        if 'k' in row.findAll('div', class_='_3llXt')[2].text.strip():
          item['Inventory'] = item['Inventory'] * 1000
        
        item['Asking_Price'] = cleanItem(row.find('div', class_='_1Pa0r').find('div', class_='_1uCwB').text.strip())

        if item['Asking_Price'] and item['Cash_Flow'] and item['Cash_Flow'] > 0:
          item['Multiple'] = round(item['Asking_Price']/item['Cash_Flow'], 3)
        item['Category'] = 'ecommerce'

        # print(item)
        yield item
        # yield scrapy.Request(url=SCRAPER_API + item['Listing_URL'], callback=self.parse_detail, meta={'item': item}, method="GET")

    # def parse_detail(self, response):
    #   item = response.meta['item']
    #   soup = BeautifulSoup(response.body, features="html.parser")
    #   description = ''
    #   for section in soup.find('section', {'id': 'BusinessStory'}).findAll('div'):
    #     if section.find('h2'):
    #       description = description + section.find('h2').text + '\n'
    #     else:
    #       if section.find('h3'):
    #         description = description + section.find('h3').text + '\n'
    #       if section.find('span'):
    #         description = description + section.find('span').text + '\n'
    #   item['Category'] = soup.findAll('li', class_='_1hSZ3')[1].text.strip()
    #   item['Listing_Description'] = description
    #   print(item)