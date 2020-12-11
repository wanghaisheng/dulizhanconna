# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import csv
import time
import datetime
import psycopg2
from scrapy import signals
from scrapy.exporters import CsvItemExporter
from bizscraper.settings import PGSQL_HOST, PGSQL_DBNAME, PGSQL_USERNAME, PGSQL_PASSWORD, KEYS
from bizscraper.utils import getCategory


class BizscraperPipeline(object):
	source_list = {}
	category_list = {}
	def __init__(self):
		self.connection = None
		self.cur = None
	@classmethod
	def from_crawler(cls, crawler):
		pipeline = cls()
		crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
		crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
		return pipeline

	def spider_opened(self, spider):
		self.connection = psycopg2.connect(host=PGSQL_HOST, user=PGSQL_USERNAME, password=PGSQL_PASSWORD, dbname=PGSQL_DBNAME)
		self.cur = self.connection.cursor()
		self.cur.execute("SELECT * FROM source")
		rows = self.cur.fetchall()
		for row in rows:
			self.source_list[row[1]] = row[0]
		print(self.source_list)
		self.cur.execute("SELECT * FROM category")
		rows = self.cur.fetchall()
		for row in rows:
			self.category_list[row[1]] = row[0]
		print(self.category_list)
		
	def spider_closed(self, spider):
		self.cur.close()
		self.connection.close()

	def process_item(self, scraped_item, spider):
		item = scraped_item
		for key in KEYS:
			if key not in item:
				item[key] = None
			elif item[key] == '':
				item[key] = None
		item['Origin_Category'] = item['Category']
		if item['Category']:
			item['Category'] = getCategory(item['Category'])
		
		if item['Category'] in self.category_list:
			item['Category'] = self.category_list[item['Category']]
		else:
			item['Category'] = self.category_list['Non-Classified']
		item['Source'] = self.source_list[item['Source']]
		# Get Business List with same detail URL
		self.cur.execute("SELECT * FROM business WHERE url='{}'".format(item['Listing_URL']))
		rows = self.cur.fetchall()
		business_id = None
		is_new_price = True
		# Check if this business is new or not
		if len(rows) > 0:
			business_id = rows[0][0]
			print(rows[0][18], item['Origin_Category'])
			
			# Get price history for this business
			self.cur.execute("SELECT * FROM price_history WHERE business_id='{}' ORDER BY id DESC LIMIT 1".format(business_id))
			price_rows = self.cur.fetchall()
			# UPDATE Customers
			# SET ContactName = 'Alfred Schmidt', City= 'Frankfurt'
			# WHERE CustomerID = 1;
			
			# Check if the current price is new or not
			if len(price_rows) > 0 and price_rows[0][1] == item['Asking_Price'] and price_rows[0][2] == item['Cash_Flow'] and price_rows[0][3] == item['Multiple']:
				is_new_price = False
				print('======dup====')
				print(price_rows[0])
				print('======dup====')
			else:
				print('======new-price====')
				print(business_id, price_rows)
				print('======new-price====')
			
			if not (rows[0][4] == item['Seller_Financing'] and rows[0][5] == item['EBITDA'] and rows[0][6] == item['FF_E'] and rows[0][7] == item['Inventory'] and rows[0][8] == item['Location_State'] and rows[0][9] == item['Location_County'] and rows[0][10] == item['Year_Established'] and rows[0][11] == item['Employee_Count'] and rows[0][12] == item['Website']) or rows[0][16] != item['Category'] or not rows[0][17] or not rows[0][13]:
				print('==============update business===============')
				self.cur.execute("update business set category_id=%s,seller_financing=%s,ebitda=%s,ff_e=%s,inventory=%s,state=%s,county=%s,established=%s,employee_count=%s,website=%s,updated_at=%s,tag=%s,last_price=%s where url=%s",
				(str(item['Category']),item['Seller_Financing'],item['EBITDA'],item["FF_E"],item['Inventory'],item['Location_State'],item['Location_County'],item['Year_Established'],item['Employee_Count'],item['Website'],item['Scraped_At'], item['Origin_Category'], price_rows[0][0], item['Listing_URL']))
				self.connection.commit()
			# if not is_new_price and not rows[0][19]:
			# 	self.cur.execute("update business set last_price=%s where url=%s", (price_rows[0][0], item['Listing_URL']))
			# 	self.connection.commit()
		else:
			print('======new-business====')
			# Insert new business
			self.cur.execute("insert into business(source_id,category_id,title,description,url,seller_financing,ebitda,ff_e,inventory,state,county,established,employee_count,website,created_at,updated_at, tag) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
			(str(item['Source']),str(item['Category']),item['Listing_Title'],item['Listing_Description'],item['Listing_URL'],item['Seller_Financing'],item['EBITDA'],item["FF_E"],item['Inventory'],item['Location_State'],item['Location_County'],item['Year_Established'],item['Employee_Count'],item['Website'],item['Scraped_At'], item['Scraped_At'], item['Origin_Category']))
			self.connection.commit()

			# Get the business_id of new business
			self.cur.execute("SELECT * FROM business WHERE url='{}'".format(item['Listing_URL']))
			rows = self.cur.fetchall()
			business_id = rows[0][0]
		
		# Insert new price to price history for business if the price or business is new one
		if is_new_price:
			self.cur.execute("insert into price_history(business_id,asking_price,gross_revenue,cash_flow,multiple,created_at) values(%s,%s,%s,%s,%s,%s)", (business_id, item['Asking_Price'], item['Gross_Revenue'], item['Cash_Flow'], item['Multiple'], item['Scraped_At']))
			self.connection.commit()
			self.cur.execute("SELECT * FROM price_history WHERE business_id='{}' ORDER BY id DESC LIMIT 1".format(business_id))
			price_rows = self.cur.fetchall()
			self.cur.execute("update business set last_price=%s where id=%s", (price_rows[0][0], business_id))
			self.connection.commit()

		return scraped_item