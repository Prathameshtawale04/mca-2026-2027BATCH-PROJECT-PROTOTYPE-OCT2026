import math
import re
from collections import defaultdict, Counter

DEFAULT_CORPUS = """
Biometric ATM security uses face recognition to authenticate users during transactions.
Face recognition uses Local Binary Patterns Histograms to extract biometric features.
Information retrieval systems index documents to provide relevant search results.
The query likelihood language model ranks documents based on generation probability.
Cybersecurity in banking prevents fraudulent withdrawals and unauthorized access.
Web crawlers navigate hyperlinks to index web pages for modern search engines.
PageRank calculates the structural importance of web pages through link analysis.
Multi-factor authentication combines face verification, PIN entry, and account numbers.
Collaborative filtering recommends relevant security documents based on user ratings.
Semantic knowledge graphs represent entities and relationships using subject predicate object triples.
Divergence from randomness ranks information using probabilistic divergence models.
MapReduce processes large document collections across parallel computing nodes.
"""

class NGramLanguageModel:
    def __init__(self, corpus_text: str = None):
        self.corpus = corpus_text or DEFAULT_CORPUS
        self.sentences = self._preprocess_corpus(self.corpus)
        self.vocab = set()
        
        self.unigram_counts = Counter()
        self.bigram_counts = defaultdict(Counter)
        self.trigram_counts = defaultdict(Counter)
        self.total_tokens = 0
        
        self._train()

    def _tokenize(self, text: str):
        return re.findall(r'[a-zA-Z0-9]+', text.lower())

    def _preprocess_corpus(self, text: str):
        raw_sentences = re.split(r'[\.\n\?!]+', text)
        sentences = []
        for s in raw_sentences:
            tokens = self._tokenize(s)
            if tokens:
                sentences.append(tokens)
        return sentences

    def _train(self):
        for sentence in self.sentences:
            tokens = ["<s>", "<s>"] + sentence + ["</s>"]
            self.vocab.update(sentence)
            
            for t in sentence:
                self.unigram_counts[t] += 1
                self.total_tokens += 1
                
            for i in range(1, len(tokens)):
                w_prev = tokens[i - 1]
                w_curr = tokens[i]
                self.bigram_counts[w_prev][w_curr] += 1
                
            for i in range(2, len(tokens)):
                w_prev2 = tokens[i - 2]
                w_prev1 = tokens[i - 1]
                w_curr = tokens[i]
                self.trigram_counts[(w_prev2, w_prev1)][w_curr] += 1

        self.vocab_size = len(self.vocab) + 2  # Including <s> and </s>

    def unigram_prob(self, word: str, laplace: bool = True):
        count = self.unigram_counts.get(word.lower(), 0)
        if laplace:
            return (count + 1) / (self.total_tokens + self.vocab_size)
        return count / self.total_tokens if self.total_tokens > 0 else 0.0

    def bigram_prob(self, prev_word: str, word: str, laplace: bool = True):
        prev = prev_word.lower()
        curr = word.lower()
        bigram_count = self.bigram_counts[prev][curr]
        context_count = sum(self.bigram_counts[prev].values())
        if laplace:
            return (bigram_count + 1) / (context_count + self.vocab_size)
        return bigram_count / context_count if context_count > 0 else 0.0

    def trigram_prob(self, w1: str, w2: str, w3: str, laplace: bool = True):
        context = (w1.lower(), w2.lower())
        curr = w3.lower()
        trigram_count = self.trigram_counts[context][curr]
        context_count = sum(self.trigram_counts[context].values())
        if laplace:
            return (trigram_count + 1) / (context_count + self.vocab_size)
        return trigram_count / context_count if context_count > 0 else 0.0

    def evaluate_sentence(self, sentence_str: str):
        tokens = self._tokenize(sentence_str)
        if not tokens:
            return {
                "tokens": [],
                "unigram": {"log_prob": 0, "prob": 0, "perplexity": 0},
                "bigram": {"log_prob": 0, "prob": 0, "perplexity": 0},
                "trigram": {"log_prob": 0, "prob": 0, "perplexity": 0}
            }

        N = len(tokens)
        
        # 1. Unigram evaluation
        uni_log_prob = 0.0
        for w in tokens:
            p = self.unigram_prob(w)
            uni_log_prob += math.log(p)
        uni_perplexity = math.exp(-uni_log_prob / N) if N > 0 else 0.0

        # 2. Bigram evaluation
        padded_bi = ["<s>"] + tokens + ["</s>"]
        bi_log_prob = 0.0
        for i in range(1, len(padded_bi)):
            p = self.bigram_prob(padded_bi[i - 1], padded_bi[i])
            bi_log_prob += math.log(p)
        bi_perplexity = math.exp(-bi_log_prob / (N + 1))

        # 3. Trigram evaluation
        padded_tri = ["<s>", "<s>"] + tokens + ["</s>"]
        tri_log_prob = 0.0
        for i in range(2, len(padded_tri)):
            p = self.trigram_prob(padded_tri[i - 2], padded_tri[i - 1], padded_tri[i])
            tri_log_prob += math.log(p)
        tri_perplexity = math.exp(-tri_log_prob / (N + 1))

        return {
            "sentence": sentence_str,
            "tokens": tokens,
            "token_count": N,
            "vocabulary_size": self.vocab_size,
            "unigram": {
                "log_prob": round(uni_log_prob, 4),
                "prob_scientific": f"{math.exp(uni_log_prob):.4e}",
                "perplexity": round(uni_perplexity, 2)
            },
            "bigram": {
                "log_prob": round(bi_log_prob, 4),
                "prob_scientific": f"{math.exp(bi_log_prob):.4e}",
                "perplexity": round(bi_perplexity, 2)
            },
            "trigram": {
                "log_prob": round(tri_log_prob, 4),
                "prob_scientific": f"{math.exp(tri_log_prob):.4e}",
                "perplexity": round(tri_perplexity, 2)
            }
        }
