# Line 1:  Import os for checking file existence when loading the corpus.
import os

# Line 2:  Import math for cosine similarity calculation.
import math

# Line 3:  Import collections for Counter (used in TF-IDF weighting).
from collections import Counter


# Line 4:  Define the RAGPipeline class that implements retrieve → augment → generate → cite.
class RAGPipeline:
    # Line 5:  Initialize with a corpus directory path and optional top-K retrieval count.
    def __init__(self, corpus_dir="rag/corpus", top_k=2):
        # Line 6:  Store the path to the directory containing document text files.
        self.corpus_dir = corpus_dir
        # Line 7:  Store how many documents to retrieve per query (top-K parameter).
        self.top_k = top_k
        # Line 8:  Initialize the document store as an empty list of (filename, text, vector) tuples.
        self.documents = []
        # Line 9:  Build the vocabulary from all corpus documents (needed for embedding).
        self._vocabulary = {}
        # Line 10:  Load all documents from the corpus directory into memory.
        self._load_corpus()

    # Line 11:  Load all .txt files from the corpus directory and compute their embeddings.
    def _load_corpus(self):
        # Line 12:  Check if the corpus directory exists; if not, start with empty corpus.
        if not os.path.isdir(self.corpus_dir):
            # Line 13:  Print a warning that the corpus directory was not found.
            print(f"  [RAG] WARNING: Corpus directory '{self.corpus_dir}' not found.")
            # Line 14:  Return early with empty document list.
            return
        # Line 15:  Get all .txt files in the corpus directory, sorted for deterministic order.
        files = sorted([f for f in os.listdir(self.corpus_dir) if f.endswith(".txt")])
        # Line 16:  First pass: build vocabulary from all documents (for consistent vector dimensions).
        all_words = []
        # Line 17:  Read each file and collect all words into the global word list.
        for fname in files:
            # Line 18:  Construct the full file path.
            fpath = os.path.join(self.corpus_dir, fname)
            # Line 19:  Read the file content as UTF-8 text.
            with open(fpath, "r", encoding="utf-8") as f:
                # Line 20:  Store the raw text temporarily for vocabulary building.
                text = f.read().strip()
                # Line 21:  Tokenize into lowercase words and extend the global list.
                all_words.extend(self._tokenize(text))
        # Line 22:  Build a sorted unique vocabulary from all collected words.
        self._vocabulary = {
            word: idx for idx, word in enumerate(sorted(set(all_words)))
        }
        # Line 23:  Second pass: compute embeddings for each document using the full vocabulary.
        for fname in files:
            # Line 24:  Construct the full file path again.
            fpath = os.path.join(self.corpus_dir, fname)
            # Line 25:  Read the document text.
            with open(fpath, "r", encoding="utf-8") as f:
                # Line 26:  Get the stripped text content.
                text = f.read().strip()
            # Line 27:  Compute the TF-IDF vector for this document.
            vec = self._embed(text)
            # Line 28:  Store the document tuple (filename, raw text, embedding vector).
            self.documents.append((fname, text, vec))

    # Line 29:  Tokenize text into lowercase words (simple whitespace + punctuation split).
    def _tokenize(self, text):
        # Line 30:  Convert to lowercase and replace non-alphanumeric chars with spaces.
        import re as _re

        # Line 31:  Split on whitespace after normalization to get word tokens.
        cleaned = _re.sub(r"[^a-z0-9\s]", "", text.lower())
        # Line 32:  Return the list of word tokens (filtering out empty strings).
        return [w for w in cleaned.split() if w]

    # Line 33:  Compute a TF-IDF embedding vector for a given text string.
    def _embed(self, text):
        # Line 34:  Get the dimensionality from vocabulary size.
        dim = len(self._vocabulary)
        # Line 35:  Initialize a zero vector of the correct dimension.
        vec = [0.0] * dim
        # Line 36:  Tokenize the input text into words.
        tokens = self._tokenize(text)
        # Line 37:  If no tokens (empty text), return the zero vector.
        if not tokens:
            # Line 38:  Return zeros for empty input.
            return vec
        # Line 39:  Compute term frequency (TF) for each token in this document.
        tf = Counter(tokens)
        # Line 40:  Total number of tokens for normalization.
        total = len(tokens)
        # Line 41:  Compute inverse document frequency (IDF) using corpus statistics.
        idf = self._compute_idf()
        # Line 42:  Fill in the vector with TF-IDF weights for each word in vocabulary.
        for word, idx in self._vocabulary.items():
            # Line 43:  If this word appears in the current text, compute its TF-IDF score.
            if word in tf:
                # Line 44:  TF = (count + 1) / (total + 1) — smoothed to avoid zero division.
                tf_val = (tf[word] + 1) / (total + 1)
                # Line 45:  TF-IDF = TF * IDF for this word.
                vec[idx] = tf_val * idf.get(word, 1.0)
        # Line 46:  Normalize the vector to unit length (enables cosine similarity via dot product).
        mag = math.sqrt(sum(x * x for x in vec))
        # Line 47:  If magnitude is non-zero, divide each component by it.
        if mag > 0:
            # Line 48:  Scale each component to produce a unit vector.
            vec = [x / mag for x in vec]
        # Line 49:  Return the normalized TF-IDF embedding vector.
        return vec

    # Line 50:  Compute IDF values for all words in the vocabulary across the corpus.
    def _compute_idf(self):
        # Line 51:  Count how many documents contain each word (document frequency).
        doc_freq = Counter()
        # Line 52:  Iterate over all stored documents to count word appearances per document.
        for fname, text, vec in self.documents:
            # Line 53:  Tokenize this document and count unique words (set removes duplicates).
            unique_words = set(self._tokenize(text))
            # Line 54:  Increment doc_freq for each unique word in this document.
            for w in unique_words:
                # Line 55:  This word appears in one more document.
                doc_freq[w] += 1
        # Line 56:  Total number of documents in the corpus.
        n_docs = max(len(self.documents), 1)
        # Line 57:  Compute IDF for each word: log(N / df) with smoothing to avoid log(0).
        idf = {}
        # Line 58:  For each word in vocabulary, compute its IDF score.
        for word in self._vocabulary:
            # Line 59:  IDF = log((N + 1) / (df + 1)) — smoothed formula.
            idf[word] = math.log((n_docs + 1) / (doc_freq.get(word, 0) + 1))
        # Line 60:  Return the IDF mapping for all vocabulary words.
        return idf

    # Line 61:  Main retrieval method: given a query, return top-K most similar documents.
    def retrieve(self, query):
        # Line 62:  If corpus is empty, return an empty list (no documents to retrieve from).
        if not self.documents:
            # Line 63:  Return empty results for empty corpus.
            return []
        # Line 64:  Embed the query using the same TF-IDF method as documents.
        query_vec = self._embed(query)
        # Line 65:  Compute cosine similarity between query and each document.
        scored = []
        # Line 66:  Iterate over all documents to score their similarity to the query.
        for fname, text, doc_vec in self.documents:
            # Line 67:  Cosine similarity = dot product of two unit vectors (already normalized).
            similarity = sum(q * d for q, d in zip(query_vec, doc_vec))
            # Line 68:  Store the (similarity_score, filename, text) tuple.
            scored.append((similarity, fname, text))
        # Line 69:  Sort by similarity in descending order (most similar first).
        scored.sort(key=lambda x: x[0], reverse=True)
        # Line 70:  Take the top-K results.
        top_results = scored[: self.top_k]
        # Line 71:  Return only the (filename, text) pairs without the score (for context injection).
        return [(fname, text) for _, fname, text in top_results]

    # Line 72:  Build the augmented context string from retrieved documents (for prompt injection).
    def build_context(self, query):
        # Line 73:  Retrieve the top-K documents for this query.
        results = self.retrieve(query)
        # Line 74:  If no results, return empty string (no context to inject).
        if not results:
            # Line 75:  Return empty context when nothing was retrieved.
            return ""
        # Line 76:  Concatenate retrieved document texts with source markers for citation.
        parts = []
        # Line 77:  For each retrieved document, add its text with a source label.
        for fname, text in results:
            # Line 78:  Format as "[source: filename] text" for traceable citations.
            parts.append(f"[source: {fname}] {text}")
        # Line 79:  Join all parts with newlines to form the full context block.
        return "\n".join(parts)
