import scrapy
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup 
from bizscraper.items import BizscraperItem
from bizscraper.settings import BIZ_REGIONS, SCRAPER_API
from bizscraper.utils import cleanItem

class BizbuysellScraper(scrapy.Spider):
  crawlera_enabled = False

  name = "bizbuysell"
  base_url = 'https://www.bizbuysell.com'
  initial_keys = ['Asking Price', 'Cash Flow', 'Gross Revenue', 'Multiple', 'EBITDA', 'FF&E', 'Inventory', 'Established', 'Rent', 'Real Estate']
  detail_keys = ["Employees", "Real Estate","Building SF","Facilities","Competition","Growth & Expansion","Support & Training", "Reason for Selling","Business Website","Location","Lease Expiration","Furniture, Fixtures, & Equipment (FF&E)","Financing", "Inventory","Franchise","Home-Based"]
  start = 1

  def __init__(self, *args, **kwargs):
    super(BizbuysellScraper, self).__init__(*args, **kwargs) 
    if kwargs.get('start'):
      self.start = int(kwargs.get('start'))

  def start_requests(self):
      print(self.start)
      for i in range(self.start * 6, (self.start + 1) * 6):
        state_url = 'https://www.bizbuysell.com/{}-businesses-for-sale'.format(BIZ_REGIONS[i].replace(' ','-').replace('/', '-'))
        yield scrapy.Request(url=SCRAPER_API + state_url, callback=self.parse_state, method="GET", meta={'state_url': state_url})

  def parse_state(self, response):
    soup = BeautifulSoup(response.body, features="html.parser")
    page_count = 1
    if soup.find('div', class_='pagination'):
      listings = soup.find('div', class_='pagination').findAll('li')
      page_count = int(listings[len(listings) - 2].text.strip())
    for page in range(1, page_count + 1):
      page_url = '{}/{}/'.format(response.meta['state_url'], page)
      yield scrapy.Request(url=SCRAPER_API + page_url, callback=self.parse_page, method="GET")

  def parse_page(self, response):
    soup = BeautifulSoup(response.body, features="html.parser")
    rows = soup.findAll('a', class_='listingResult')
    for row in rows:
      detail_url = self.base_url + row.attrs['href']
      yield scrapy.Request(url=SCRAPER_API + detail_url, callback=self.parse_detail, method="GET", meta={'detail_url': detail_url, 'location': row.find('p', class_='info').text})
  
  def parse_detail(self, response):
    soup = BeautifulSoup(response.body, features="html.parser")
    if soup.find('h1', class_='bfsTitle'):
      

      information_group = soup.findAll('div', class_='specs')
      info = {}

      for key in self.initial_keys:
        info[key] = None
      for information in information_group:
        for piece in information.findAll('p'):
          key = piece.find('span', class_='title').text.strip().replace(':', '')
          info[key] = piece.find('b').text.strip()

      detailed_info = soup.find('dl', class_='listingProfile_details')
      flag = True
      detailed_info_list = {}
      for key in self.detail_keys:
        detailed_info_list[key] = None
      key = ''
      if detailed_info:
        for row in detailed_info.findAll():
          if '<dt>' in str(row):
            flag = True
            key = row.text
          if '<dd>' in str(row) and flag == True:
            flag = False
            detailed_info_list[key.replace(':', '')] = row.text


      item = BizscraperItem()
      item['Source'] = self.name
      
      item['Listing_URL'] = response.meta['detail_url']
      item['Listing_Title'] = soup.find('h1', class_='bfsTitle').text.strip()
      item['Listing_Description'] = soup.find('div', class_='businessDescription').text.strip()
      item['Seller_Financing'] = False
      if soup.find('div', {'id': 'seller-financing'}):
        item['Seller_Financing'] = True

      item['Asking_Price'] = cleanItem(info['Asking Price'])
      item['Cash_Flow'] = cleanItem(info['Cash Flow'])
      if item['Asking_Price'] and item['Cash_Flow'] and item['Cash_Flow'] > 0:
        item['Multiple'] = round(item['Asking_Price']/item['Cash_Flow'], 3)
      item['Gross_Revenue'] = cleanItem(info['Gross Revenue'])
      item['EBITDA'] = cleanItem(info['EBITDA'])
      item['FF_E'] = cleanItem(info['FF&E'])
      item['Inventory'] = cleanItem(info['Inventory'])

      item['Year_Established'] = info['Established']
      item['Employee_Count'] = detailed_info_list['Employees']
      item['Website'] = detailed_info_list['Business Website']
      item['Scraped_At'] = datetime.now()
      
      if soup.find('div', {'id': 'others'}):
        others = soup.find('div', {'id': 'others'}).findAll('a')
        if len(others) > 0:
          item['Category'] = others[0].text.replace('for Sale', '').strip()
      if response.meta['location'] and response.meta['location'] != '':
        if len(response.meta['location'].split(',')) == 2:
          item['Location_County'] = response.meta['location'].split(',')[0].strip()
          item['Location_State'] = response.meta['location'].split(',')[1].strip()
        else:
          item['Location_State'] = response.meta['location'].split(',')[0].strip()
      # print(item)
      yield item