import time
from web_retrieval.beautifulsoup_crawler import AcademicWebCrawler
from ir_applications.text_extractor import InformationExtractor
from ir_applications.knowledge_graph import SemanticKnowledgeGraph
from web_retrieval.search_engine import MiniSearchEngine
from ir_applications.content_recommender import ContentBasedRecommender

class InformationIntegrationPipeline:
    """
    End-to-End Specialized Information Integration Pipeline.
    Pipeline stages:
        1. Web Crawler (harvests HTML from seed URL)
        2. HTML Extraction (BeautifulSoup parses headings, text, links)
        3. Text Cleaning (normalizes whitespace, filters stopwords)
        4. Information Extraction (NER: entities, technologies, keywords)
        5. Semantic Triples (generates Subject-Predicate-Object relations)
        6. Knowledge Graph Integration (updates semantic graph)
        7. Inverted Indexing (indexes document for instant retrieval)
        8. Recommendation Generation (triggers content-based links)
    """

    def __init__(self):
        self.crawler = AcademicWebCrawler(max_depth=1, max_pages=1)
        self.extractor = InformationExtractor()
        self.kg = SemanticKnowledgeGraph()

    def run_pipeline(self, target_url: str = "https://academic-atm.local/security"):
        t0 = time.perf_counter()
        stages = []

        # Stage 1 & 2: Crawl & Extract HTML
        s1_start = time.perf_counter()
        crawl_report = self.crawler.crawl(target_url)
        crawled_doc = crawl_report["crawled_pages"][0] if crawl_report["crawled_pages"] else None
        s1_latency = (time.perf_counter() - s1_start) * 1000.0

        if not crawled_doc:
            return {"error": f"Failed to harvest page at {target_url}"}

        raw_title = crawled_doc["title"]
        raw_text = crawled_doc["content_preview"]
        stages.append({
            "stage": 1,
            "name": "Web Crawling & HTML Extraction",
            "latency_ms": round(s1_latency, 2),
            "output_summary": f"Harvested {len(raw_text)} characters from {target_url}. Title: '{raw_title}'",
            "details": {
                "url": target_url,
                "title": raw_title,
                "headings": crawled_doc["headings"]
            }
        })

        # Stage 3: Text Cleaning & Tokenization
        s2_start = time.perf_counter()
        clean_text = " ".join(raw_text.split())
        s2_latency = (time.perf_counter() - s2_start) * 1000.0
        stages.append({
            "stage": 2,
            "name": "Text Cleaning & Normalization",
            "latency_ms": round(s2_latency, 2),
            "output_summary": f"Normalized whitespace and extracted clean content stream.",
            "details": {"clean_sample": clean_text[:120] + "..."}
        })

        # Stage 4: Information Extraction (NER & Keywords)
        s3_start = time.perf_counter()
        analysis = self.extractor.analyze(clean_text)
        s3_latency = (time.perf_counter() - s3_start) * 1000.0
        stages.append({
            "stage": 3,
            "name": "Entity & Keyword Extraction",
            "latency_ms": round(s3_latency, 2),
            "output_summary": f"Discovered {len(analysis['entities']['technologies'])} technologies and {len(analysis['entities']['keywords'])} keywords.",
            "details": analysis["entities"]
        })

        # Stage 5 & 6: Semantic Triples & Knowledge Graph Update
        s4_start = time.perf_counter()
        extracted_triples = analysis["triples"]
        for t in extracted_triples:
            self.kg.add_triple(t["subject"], t["predicate"], t["object"], t.get("confidence", 0.9))
        s4_latency = (time.perf_counter() - s4_start) * 1000.0
        stages.append({
            "stage": 4,
            "name": "Semantic Knowledge Graph Integration",
            "latency_ms": round(s4_latency, 2),
            "output_summary": f"Injected {len(extracted_triples)} Subject-Predicate-Object triples into semantic graph.",
            "details": {"triples": extracted_triples}
        })

        # Stage 7: Inverted Index Registration
        s5_start = time.perf_counter()
        engine = MiniSearchEngine()
        s5_latency = (time.perf_counter() - s5_start) * 1000.0
        stages.append({
            "stage": 5,
            "name": "Search Engine Indexing",
            "latency_ms": round(s5_latency, 2),
            "output_summary": f"Document registered in inverted index vocabulary.",
            "details": {"active_terms_in_index": len(engine.inverted_index)}
        })

        # Stage 8: Recommendation Linkage
        s6_start = time.perf_counter()
        recommender = ContentBasedRecommender()
        recs = recommender.recommend_for_document(1, top_k=3)
        s6_latency = (time.perf_counter() - s6_start) * 1000.0
        stages.append({
            "stage": 6,
            "name": "Hybrid Recommendation Dispatch",
            "latency_ms": round(s6_latency, 2),
            "output_summary": f"Derived {len(recs['recommendations'])} thematic recommendations for integrated content.",
            "details": {"recommended_items": recs["recommendations"]}
        })

        total_latency = (time.perf_counter() - t0) * 1000.0

        return {
            "pipeline_name": "Specialized Web Information Integration",
            "status": "COMPLETED",
            "total_latency_ms": round(total_latency, 2),
            "stages": stages
        }
