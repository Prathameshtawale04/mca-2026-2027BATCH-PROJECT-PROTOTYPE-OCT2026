import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from config import Config
from database.db import execute_sql, query_all

# Pre-packaged local HTML simulation for offline academic testing
DEMO_HTML_PAGES = {
    "https://academic-atm.local/security": """
        <html>
            <head><title>Biometric ATM Security Architecture</title></head>
            <body>
                <h1>ATM Biometrics and Face Recognition</h1>
                <p>Modern automated teller machines incorporate computer vision algorithms like LBPH and deep face embeddings to authenticate banking clients securely.</p>
                <h2>Multi-Factor Verification</h2>
                <p>Combining facial biometrics with PIN verification prevents unauthorized cash withdrawals and card skimming vulnerabilities.</p>
                <a href="https://academic-atm.local/retrieval">Information Retrieval in Banking</a>
                <a href="https://academic-atm.local/cryptography">Banking Cryptography</a>
            </body>
        </html>
    """,
    "https://academic-atm.local/retrieval": """
        <html>
            <head><title>Information Retrieval Systems in FinTech</title></head>
            <body>
                <h1>Intelligent Document Retrieval</h1>
                <p>Information retrieval systems index financial regulations, transaction ledgers, and audit logs using inverted indexes and PageRank scoring.</p>
                <h2>Search Engines and PageRank</h2>
                <p>Graph-based link ranking algorithms determine structural importance of documents across banking intranets.</p>
                <a href="https://academic-atm.local/security">Return to Security</a>
                <a href="https://academic-atm.local/semantic">Semantic Web Triples</a>
            </body>
        </html>
    """,
    "https://academic-atm.local/cryptography": """
        <html>
            <head><title>Banking Cryptography & PIN Hashing</title></head>
            <body>
                <h1>PBKDF2 and SHA-256 PIN Security</h1>
                <p>ATM PIN credentials must never be stored in plaintext. Systems utilize PBKDF2 with salt and 100000 iterations to withstand brute-force attacks.</p>
                <a href="https://academic-atm.local/security">Back to Security</a>
            </body>
        </html>
    """,
    "https://academic-atm.local/semantic": """
        <html>
            <head><title>Semantic Web Knowledge Graphs in ATM IR</title></head>
            <body>
                <h1>RDF Triples and Entity Extraction</h1>
                <p>Automated Information Extraction maps subject predicate object triples to build rich semantic knowledge representations.</p>
                <a href="https://academic-atm.local/retrieval">Back to Retrieval</a>
            </body>
        </html>
    """
}

class AcademicWebCrawler:
    """
    Academic Web Crawler using BeautifulSoup4.
    Adheres to safety parameters:
    - Frontier Queue
    - Visited Set
    - Depth Limit
    - Max Pages Limit
    - Polite Request Delays
    - Handles offline simulation for *.local URLs and real web fetching with timeouts.
    """

    def __init__(self, max_depth: int = 2, max_pages: int = 5, polite_delay: float = 0.5):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.polite_delay = polite_delay
        self.headers = {"User-Agent": Config.CRAWLER_USER_AGENT}

    def _fetch_page(self, url: str):
        # Check if URL belongs to offline academic demo
        if url in DEMO_HTML_PAGES:
            return DEMO_HTML_PAGES[url], 200

        try:
            resp = requests.get(url, headers=self.headers, timeout=4.0)
            if "text/html" in resp.headers.get("Content-Type", ""):
                return resp.text, resp.status_code
            return None, resp.status_code
        except Exception as e:
            return None, 500

    def parse_html(self, html_content: str, current_url: str):
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Title
        title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled Document"
        
        # Headings
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
        
        # Paragraphs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
        content_text = " ".join(paragraphs)

        # Links
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            if parsed.scheme in ("http", "https"):
                links.append(full_url)

        return {
            "title": title,
            "headings": headings,
            "paragraphs": paragraphs[:5],
            "content_text": content_text,
            "links": list(set(links))
        }

    def crawl(self, seed_url: str = "https://academic-atm.local/security"):
        frontier = deque([(seed_url, 0)]) # (url, depth)
        visited = set()
        crawled_results = []
        discovered_links = []

        while frontier and len(crawled_results) < self.max_pages:
            url, depth = frontier.popleft()
            if url in visited:
                continue
            if depth > self.max_depth:
                continue

            visited.add(url)
            html, status_code = self._fetch_page(url)
            
            if not html or status_code != 200:
                continue

            parsed_data = self.parse_html(html, url)
            
            # Record in database
            try:
                execute_sql(
                    """
                    INSERT INTO crawl_pages (url, title, content_text, status_code, depth)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        title = excluded.title,
                        content_text = excluded.content_text,
                        depth = excluded.depth,
                        crawled_at = CURRENT_TIMESTAMP
                    """,
                    (url, parsed_data["title"], parsed_data["content_text"], status_code, depth)
                )
            except Exception:
                pass

            crawled_results.append({
                "url": url,
                "depth": depth,
                "status_code": status_code,
                "title": parsed_data["title"],
                "headings": parsed_data["headings"],
                "content_preview": parsed_data["content_text"][:150] + "...",
                "out_links_count": len(parsed_data["links"])
            })

            for target in parsed_data["links"]:
                discovered_links.append({"source": url, "target": target})
                try:
                    execute_sql(
                        "INSERT INTO links (source_url, target_url) VALUES (?, ?)",
                        (url, target)
                    )
                except Exception:
                    pass

                if target not in visited:
                    frontier.append((target, depth + 1))

            time.sleep(self.polite_delay)

        return {
            "seed_url": seed_url,
            "total_crawled": len(crawled_results),
            "pages_visited": list(visited),
            "frontier_remaining": len(frontier),
            "crawled_pages": crawled_results,
            "links_graph": discovered_links[:25]
        }
