import scrapy
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup 
from bizscraper.items import BizscraperItem
from bizscraper.utils import cleanItem


class IndiemakerScraper(scrapy.Spider):
    name = "indiemaker"
    start_urls = [
        'https://indiemaker.co/listings'
    ]
    base_url = 'https://indiemaker.co'
    custom_cookie = {
      '__cfduid': 'd3a781d7d5c5950e23624eb6dff1c0f7a1596728067',
      '_ga': 'GA1.2.1304017140.1596728090',
      '_hjid': 'ed6c51bb-1774-48f3-b103-e61d89a9c938',
      '_hjIncludedInSample': 1,
      '_gid': 'GA1.2.913581655.1596905959',
      '_hjAbsoluteSessionInProgress': 1,
      '__stripe_mid': 'fd047f25-9e39-471d-8909-a62b73712fafbcda0d', 
      '__stripe_sid': '6f7af29c-9741-460f-8577-c4e58d756ebccf4bd2',
      '_gat_gtag_UA_156764216_1': 1, 
      '_vagrant_data_session': 'JsRubT%2FvX43HFU%2FGaf6Syd2dAzMhO%2F2V6CEedVvCJtXeDI%2Ba8HdXVDpGDeVvcia0TCOorz97jAw0OWs2mE6ibefnwg1wf7AJ9oxDLEpChsIkgG6Tl4gJAMSkWOJh6hFd989lARgm5Iy30eA4HjrCZsK9Y53AmfzL%2BShcrDdimd8gIp%2FZvmn1QofEMOc6yaHE8%2FOjMYadh9mSWdFYqR2UwuledQeuPSxzAbPJXY11nB11MYIw1QybTs4p0by9wneY5qhmb269ognbIJs1e%2BCsP8kgiHDpQkHXcYi6FQwi8SA44lKeNpGTNzWOTorrTU0F5b1O5oA%3D--h5UOaltwasXLHm4G--ekEvhmKGjzMdcIZTXNWP0g%3D%3D'
    }
   
    def parse(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      last_link = soup.find('span', class_='last').find('a').attrs['href']
      page_count = int(last_link.split('=')[1])
      print(page_count)
      for page in range(0, page_count):
        yield scrapy.Request(url='{}/listings?page={}'.format(self.base_url, page+1), callback=self.parse_list, method="GET")
      
    def parse_list(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      for row in soup.findAll('div', class_='listing-row'):
        item_link = row.find('h2')
        item = BizscraperItem()
        item['Source'] = self.name
        item['Listing_Title'] = item_link.text.strip()
        item['Listing_URL'] = self.base_url + item_link.find('a').attrs['href']
        item['Category'] = row.find('div', class_='stats').find('span', class_='bold').text.strip()
        if item['Category'] == 'Domain':
          continue
        if row.find('div', class_='domain-pricing'):
          item['Asking_Price'] = cleanItem(row.find('div', class_='domain-pricing').find('p').text.strip().replace('K', '000'))
        elif row.find('div', class_='regular-pricing'):
          item['Asking_Price'] = cleanItem(row.find('div', class_='regular-pricing').find('p').text.strip().replace('K', '000'))
        yield scrapy.Request(url=item['Listing_URL'], cookies=self.custom_cookie, callback=self.parse_detail, meta={'item': item}, method="GET")

    def parse_detail(self, response):
      item = response.meta['item']
      soup = BeautifulSoup(response.body, features="html.parser")
      item['Cash_Flow'] = None
      item['Gross_Revenue'] = None
      item['Multiple'] = None
      item['Scraped_At'] = datetime.now() 
      print(item['Listing_URL'])
      if soup.find('div', class_='premium-blocks'):
        blocks = soup.find('div', class_='premium-blocks').findAll('div')
        for block in blocks:
          block_title = block.find('h3').text
          if 'Monthly Revenue' in block_title:
            item['Gross_Revenue'] = cleanItem(block.find('span').text.strip()) * 12
          elif 'Monthly Profit' in block_title:
            item['Cash_Flow'] = cleanItem(block.find('span').text.strip()) * 12
        print('-------------', item['Gross_Revenue'], item['Cash_Flow'], '-------------')
        if item['Asking_Price'] and item['Cash_Flow'] and item['Cash_Flow'] > 0:
          item['Multiple'] = round(item['Asking_Price']/item['Cash_Flow'], 3)

      item['Listing_Description'] = ''
      if len(soup.findAll('div', class_='content-container')) > 0:
        description_container = soup.findAll('div', class_='content-container')[0]
        description = ''
        if len(description_container.findAll('p')) == 0:
          description = description_container.text.strip().replace('Listing Details', '').strip()
        else:
          for line in description_container.findAll('p'):
            description = description + line.text + '\n'
        item['Listing_Description'] = description

      for link in soup.find('div', class_='pad-3').findAll('a'):
        if 'Visit Website' in link.attrs['title']:
          item['Website'] = link.attrs['href']
      # print(item)
      yield item