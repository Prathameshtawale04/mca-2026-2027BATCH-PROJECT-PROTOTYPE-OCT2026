# Scrapy Settings
BOT_NAME = "atm_spider"

SPIDER_MODULES = ["atm_spider.spiders"]
NEWSPIDER_MODULE = "atm_spider.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 1.0
USER_AGENT = "AcademicATMSpider/1.0 (+http://localhost:5000)"

ITEM_PIPELINES = {
    # Optional SQLite persistence pipeline
}
