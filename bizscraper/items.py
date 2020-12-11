# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BizscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    Source = scrapy.Field()
    Origin_Category = scrapy.Field()
    Category = scrapy.Field()
    Listing_Title = scrapy.Field()
    Listing_Description = scrapy.Field()
    Listing_URL = scrapy.Field()
    Seller_Financing = scrapy.Field()
    Asking_Price = scrapy.Field()
    Cash_Flow = scrapy.Field()
    Gross_Revenue = scrapy.Field()
    Multiple = scrapy.Field()
    EBITDA = scrapy.Field()
    FF_E = scrapy.Field()
    Inventory = scrapy.Field()
    Location_State = scrapy.Field()
    Location_County = scrapy.Field()
    Year_Established = scrapy.Field()
    Employee_Count = scrapy.Field()
    Website = scrapy.Field()
    Scraped_At = scrapy.Field()
    pass
