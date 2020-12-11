import scrapy
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup 
from bizscraper.items import BizscraperItem
from bizscraper.utils import cleanItem, getCategory



class WebsitecloserScraper(scrapy.Spider):
    
    name = "websitecloser"
    start_urls = [
        'https://www.websiteclosers.com/businesses-for-sale/'
    ]
    keys = ['Asking Price', 'Cash Flow', 'Gross Income', "Multiple", 'Year Established', 'Employees']
    ajax_url = 'https://www.websiteclosers.com/wp-admin/admin-ajax.php?action=ajax_req'
    def parse(self, response):
      soup = BeautifulSoup(response.body, features="html.parser")
      last_link = soup.find('div', class_='wp-pagenavi').find('a', class_='last')
      page_count = int(last_link.text.replace('.', '').strip())
      print(page_count)
      frmdata = {
        'taxonomy': 'businesses-category',
        'slug': 'businesses-for-sale',
        'post_type_id': '9',
        'select': '?shortby=&order=',
        's_name': '',
        'from': '',
        'to': ''
      }
      for page in range(1, page_count + 1):
        frmdata['page'] = str(page)
        print(frmdata['page'])
        yield scrapy.FormRequest(url=self.ajax_url, callback=self.parse_page, formdata=(frmdata))
    
    def parse_page(self, response):
      soup = BeautifulSoup(json.loads(response.body)['content'], features="html.parser")
      rows = soup.findAll('div', class_='post_item')
      print('=============', len(rows))
      count = 0
      for row in rows:
        count = count + 1
        item = BizscraperItem()
        item['Source'] = self.name
        item['Listing_Title'] = row.find('a', class_='post_title').text.strip()
        item['Category'] = item['Listing_Title'].strip()
        item['Listing_URL'] = row.find('a', class_='post_title').attrs['href']
        item['Scraped_At'] = datetime.now()
        yield scrapy.Request(url=item['Listing_URL'], callback=self.parse_detail, method="GET", meta={'item': item})
     
    def parse_detail(self, response):
      item = response.meta['item']
      soup = BeautifulSoup(response.body, features="html.parser")
      info = {}
      for row in soup.find('div', class_='sb-table').findAll('div', class_='line'):
        info[row.find('div', class_='left').text.strip()] = row.find('div', class_='right').text.strip()
      info['Multiple'] = ''


      item['Asking_Price'] = cleanItem(info['Asking Price'])
      if 'Cash Flow' in info:
        item['Cash_Flow'] = cleanItem(info['Cash Flow'])
      else:
        item['Cash_Flow'] = None

      if item['Asking_Price'] and item['Cash_Flow'] and item['Cash_Flow'] > 0:
        item['Multiple'] = round(item['Asking_Price']/item['Cash_Flow'], 3)
      else:
        item['Multiple'] = ''
      for key in self.keys:
        if key not in info:
          info[key] = None

      item['Gross_Revenue'] = cleanItem(info['Gross Income'])
      # item['Multiple'] = info['Multiple']
      item['Year_Established'] = info['Year Established']
      item['Employee_Count'] = info['Employees']
      item['Listing_Description'] = soup.find('div', class_='cfx').text.strip()
      yield item

        