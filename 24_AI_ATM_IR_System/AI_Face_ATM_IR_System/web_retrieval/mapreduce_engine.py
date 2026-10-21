import re
from collections import defaultdict

class MapReduceEngine:
    """
    Local MapReduce Framework Simulation for Inverted Indexing & Term Frequency.
    Pipeline:
        Input Documents
            ↓ (Map Phase)
        Key-Value Pairs (term, (doc_id, 1))
            ↓ (Shuffle & Sort Phase)
        Grouped by Key: term -> [(doc_id, 1), (doc_id, 1), ...]
            ↓ (Reduce Phase)
        Aggregated Postings: term -> {doc_id: total_tf, ...}
    """

    @staticmethod
    def tokenize(text: str):
        return re.findall(r'[a-zA-Z0-9]+', text.lower())

    def mapper(self, doc_id: int, content: str):
        """
        Maps a document to a stream of (term, (doc_id, 1)) pairs.
        """
        tokens = self.tokenize(content)
        intermediate = []
        for t in tokens:
            intermediate.append((t, (doc_id, 1)))
        return intermediate

    def shuffle_and_sort(self, map_outputs: list):
        """
        Groups intermediate pairs by key (term).
        """
        grouped = defaultdict(list)
        for term, payload in map_outputs:
            grouped[term].append(payload)
        return sorted(grouped.items(), key=lambda x: x[0])

    def reducer(self, term: str, payloads: list):
        """
        Aggregates payloads for a single term into doc frequencies and total term count.
        """
        doc_frequencies = defaultdict(int)
        total_occurrences = 0
        for doc_id, count in payloads:
            doc_frequencies[doc_id] += count
            total_occurrences += count

        return {
            "term": term,
            "total_occurrences": total_occurrences,
            "document_frequency": len(doc_frequencies),
            "postings": [
                {"doc_id": d_id, "tf": tf}
                for d_id, tf in sorted(doc_frequencies.items())
            ]
        }

    def execute(self, documents: list):
        """
        Executes full MapReduce pipeline on list of documents.
        Each doc must be a dict with 'doc_id' and 'content' or 'text'.
        """
        # 1. Map Phase
        all_map_pairs = []
        mapper_stats = []
        for doc in documents:
            d_id = doc.get("doc_id", 0)
            text = doc.get("content", doc.get("text", ""))
            pairs = self.mapper(d_id, text)
            all_map_pairs.extend(pairs)
            mapper_stats.append({
                "doc_id": d_id,
                "title": doc.get("title", f"Doc {d_id}"),
                "pairs_emitted": len(pairs)
            })

        # 2. Shuffle & Sort Phase
        grouped = self.shuffle_and_sort(all_map_pairs)

        # 3. Reduce Phase
        reduced_results = []
        for term, payloads in grouped:
            reduced = self.reducer(term, payloads)
            reduced_results.append(reduced)

        # Sort reduced results by total_occurrences descending
        reduced_results.sort(key=lambda x: x["total_occurrences"], reverse=True)

        return {
            "total_input_docs": len(documents),
            "total_map_pairs_emitted": len(all_map_pairs),
            "unique_terms_reduced": len(reduced_results),
            "mapper_stats": mapper_stats,
            "sample_map_pairs": all_map_pairs[:20],
            "reduced_index": reduced_results[:50]  # Top 50 terms
        }
