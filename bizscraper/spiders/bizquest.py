import scrapy
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup 
from bizscraper.items import BizscraperItem
from bizscraper.settings import US_STATE_ABBREV, US_STATE_SHORT, SCRAPER_API
from bizscraper.utils import cleanItem

class BizquestScraper(scrapy.Spider):
    crawlera_enabled = False

    name = "bizquest"
    base_url = 'https://www.bizquest.com'
    initial_keys = ['Asking Price', 'Cash Flow', 'Gross Revenue', 'Multiple', 'EBITDA', 'FF&E', 'Inventory']
    detail_keys = ['Location', 'Year Established', 'Number of Employees', 'Website', 'Real Estate', 'Rent', 'Lease Expiration', 'Facilities', 'Growth & Expansion', 'Home Based']
    start = 0

    def __init__(self, *args, **kwargs):
      super(BizquestScraper, self).__init__(*args, **kwargs) 
      if kwargs.get('start'):
        self.start = int(kwargs.get('start'))

    def start_requests(self):
      print(self.start)
      for i in range(self.start * 6, (self.start + 1) * 6):
        state_url = '{}/businesses-for-sale-in-{}-{}'.format(self.base_url, US_STATE_ABBREV[US_STATE_SHORT[i]].replace(' ', '-'), US_STATE_SHORT[i])
        yield scrapy.Request(url=SCRAPER_API + state_url, callback=self.parse_state, method="GET", meta={'state_url': state_url})

    def parse_state(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      page_count = 1
      if soup.find('ul', class_='pagination'):
        links = soup.find('ul', class_='pagination').findAll('a')
        if len(links) > 2:
          page_count = int(links[-2].text)
      for page in range(1, page_count + 1):
        page_url = '{}/page-{}'.format(response.meta['state_url'], page)
        yield scrapy.Request(url=SCRAPER_API + page_url, callback=self.parse_page, method="GET")

    def parse_page(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      rows = soup.findAll('div', class_='spotlight')
      for row in rows:
        if 'srfranchise' not in row.attrs['class']:
          item = BizscraperItem()
          item['Source'] = self.name
          item['Listing_Title'] = row.find('b', class_='title').find('a').text.strip()
          item['Listing_URL'] = row.find('b', class_='title').find('a').attrs['href']
          item['Listing_Description'] = row.find('p', class_='desc').text.strip()
          item['Scraped_At'] = datetime.now()

          yield scrapy.Request(url=SCRAPER_API + item['Listing_URL'], callback=self.parse_detail, method="GET", meta={'item': item})
    
    def parse_detail(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      
      initial_info = {}
      initial_wrapper = soup.find('div', class_='col-md-3')
      initial_key = ''
      for key in self.initial_keys:
        initial_info[key] = None
      for item in initial_wrapper.findAll('b'):
        flag = True
        for key in self.initial_keys:
          if key in item.text:
            initial_key = key
            flag = False
            break
        if flag:
          initial_info[initial_key] = item.text.strip().replace('included in asking price', ' included in asking price')
      
      
      initial_info['Asking Price'] = cleanItem(initial_info['Asking Price'])
      initial_info['Cash Flow'] = cleanItem(initial_info['Cash Flow'])

      if initial_info['Asking Price'] and initial_info['Cash Flow'] and initial_info['Cash Flow'] > 0:
        initial_info['Multiple'] = round(initial_info['Asking Price']/initial_info['Cash Flow'], 3)

      detail_info = {}
      detail_wrapper = soup.findAll('dl', class_='dl-horizontal')[0]
      detail_key = ''
      for key in self.detail_keys:
        detail_info[key] = None
      for row in detail_wrapper.findAll():
        if '<dt>' in str(row):
          flag = True
          key = row.text.strip()
        if '<dd>' in str(row) and flag == True:
          flag = False
          detail_info[key.replace(':', '')] = row.text.strip()

      item = response.meta['item']
      item['Seller_Financing'] = False
      if soup.find('div', class_='financing') and 'Seller Financing' in soup.find('div', class_='financing').text:
        item['Seller_Financing'] = True

      breadcrumbs = soup.find('ol', {'id': 'crumbs'}).findAll('li')
      item['Category'] = None
      if len(breadcrumbs) > 2:
        item['Category'] = breadcrumbs[2].text.replace('Businesses for Sale', '').strip()

      item['Asking_Price'] = initial_info['Asking Price']
      item['Cash_Flow'] = initial_info['Cash Flow']
      item['Gross_Revenue'] = cleanItem(initial_info['Gross Revenue'])
      item['EBITDA'] = cleanItem(initial_info['EBITDA'])
      item['FF_E'] = cleanItem(initial_info['FF&E'])
      item['Inventory'] = cleanItem(initial_info['Inventory'])
      item['Multiple'] = initial_info['Multiple']

      item['Year_Established'] = detail_info['Year Established']
      item['Employee_Count'] = detail_info['Number of Employees']
      item['Website'] = detail_info['Website']

      if detail_info['Location']:
        if len(detail_info['Location'].split(',')) == 2:
          item['Location_County'] = detail_info['Location'].split(',')[0].strip()
          item['Location_State'] = detail_info['Location'].split(',')[1].strip()
        else:
          item['Location_State'] = detail_info['Location'].split(',')[0].strip()
      yield item