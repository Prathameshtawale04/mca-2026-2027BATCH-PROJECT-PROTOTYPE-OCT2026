import scrapy
from datetime import datetime

class SecuritySpider(scrapy.Spider):
    """
    Scrapy spider for harvesting cybersecurity and biometric ATM documentation.
    Can be run via:
        cd web_retrieval/scrapy_crawler
        scrapy crawl security_spider -o output.json
    """
    name = "security_spider"
    allowed_domains = ["academic-atm.local", "example.com"]
    start_urls = [
        "https://academic-atm.local/security",
        "https://example.com"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1.0,
        "DEPTH_LIMIT": 2
    }

    def parse(self, response):
        self.logger.info(f"Scraping URL: {response.url}")
        
        title = response.css("title::text").get(default="").strip()
        headings = response.css("h1::text, h2::text").getall()
        paragraphs = response.css("p::text").getall()
        summary = " ".join([p.strip() for p in paragraphs if p.strip()])[:250]

        yield {
            "title": title,
            "url": response.url,
            "category": "ATM_Cybersecurity",
            "headings": [h.strip() for h in headings if h.strip()],
            "summary": summary,
            "crawled_at": datetime.now().isoformat()
        }

        # Follow local or allowed hyperlinks
        for href in response.css("a::attr(href)").getall():
            yield response.follow(href, callback=self.parse)
