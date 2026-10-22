# Scrapy Items Definition
import scrapy

class ATMSecurityItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    category = scrapy.Field()
    headings = scrapy.Field()
    summary = scrapy.Field()
    crawled_at = scrapy.Field()
