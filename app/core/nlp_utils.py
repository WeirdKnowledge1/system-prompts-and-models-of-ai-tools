import re
import string
from typing import List, Tuple

# Attempt to import scikit-learn components
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None
    cosine_similarity = None
    print("Warning: scikit-learn not found. Semantic similarity features will be disabled.")

# Basic English stop words list (can be expanded or replaced with NLTK's list)
DEFAULT_STOP_WORDS = set([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should", "can",
    "could", "may", "might", "must", "am", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "mine", "yours", "hers", "ours", "theirs", "myself", "yourself",
    "himself", "herself", "itself", "ourselves", "themselves", "and", "but", "or",
    "nor", "for", "so", "yet", "if", "then", "else", "when", "where", "why",
    "how", "what", "which", "who", "whom", "whose", "with", "without", "about",
    "above", "after", "again", "against", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "not", "only", "own", "same",
    "than", "that", "this", "to", "from", "up", "down", "in", "out", "on", "off",
    "over", "under", "further", "here", "there", "through", "while", "of", "at",
    "by", "as", "until", "into", "throughout", "during", "before", "between",
    "among", "s", "t", "don", "just", "too", "very"
])

def preprocess_text_simple(text: str, stop_words: set = None) -> List[str]:
    """
    Simple text preprocessing:
    1. Convert to lowercase.
    2. Remove punctuation.
    3. Tokenize by splitting on whitespace.
    4. Remove stop words.
    Returns a list of processed tokens.
    """
    if not isinstance(text, str):
        return []

    if stop_words is None:
        stop_words = DEFAULT_STOP_WORDS

    # Lowercase
    text = text.lower()

    # Remove punctuation (replace with space to handle cases like "word-word")
    # A more robust way is to handle specific punctuation, but this is simpler.
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)

    # Tokenize (simple split)
    tokens = text.split()

    # Remove stop words and very short tokens (e.g., single characters left from punctuation removal)
    processed_tokens = [
        token for token in tokens if token not in stop_words and len(token) > 1
    ]

    return processed_tokens


def calculate_tfidf_cosine_similarity(text1: str, text2: str) -> float:
    """
    Calculates cosine similarity between two texts using TF-IDF vectors.
    Returns a similarity score between 0.0 and 1.0.
    Returns 0.0 if scikit-learn is not available or an error occurs.
    """
    if not SKLEARN_AVAILABLE:
        print("scikit-learn is required for calculate_tfidf_cosine_similarity but not installed.")
        return 0.0

    if not text1 or not text2: # Handle empty strings to avoid errors in TfidfVectorizer
        return 0.0

    # Preprocess both texts (using the simple version for now)
    # Note: For TF-IDF, it's common to pass raw text to TfidfVectorizer as it has its own
    # tokenizer and preprocessor. However, if we want custom preprocessing like above,
    # we should pass already tokenized text and use a dummy tokenizer/preprocessor for the vectorizer.
    # For simplicity here, we'll let TfidfVectorizer do its default preprocessing.
    # If using our custom `preprocess_text_simple`, the vectorizer should be:
    # TfidfVectorizer(tokenizer=lambda x: x, preprocessor=lambda x: x, token_pattern=None)
    # when passing token lists.
    # But for raw text input, its defaults are reasonable.

    documents = [text1, text2]

    try:
        # Initialize TfidfVectorizer. It handles tokenization, stop word removal (default English), etc.
        # We can pass our own stop_words list if desired: TfidfVectorizer(stop_words=list(DEFAULT_STOP_WORDS))
        vectorizer = TfidfVectorizer(stop_words='english') # Using sklearn's default English stop words

        # Fit and transform the documents to get TF-IDF vectors
        tfidf_matrix = vectorizer.fit_transform(documents)

        # The matrix will have two rows (one for each document)
        # Calculate cosine similarity between the two vectors
        # cosine_similarity returns a matrix, so we need to get the specific value [0,1]
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        similarity_score = similarity_matrix[0][0]

        return similarity_score

    except Exception as e:
        print(f"Error calculating TF-IDF cosine similarity: {e}")
        return 0.0


if __name__ == '__main__':
    print("Testing NLP Utilities...")

    # Test preprocessing
    sample_text_1 = "This is the first sample sentence, for testing purposes!"
    sample_text_2 = "A second sentence is this one, also for sample testing."
    sample_text_3 = "A completely different third text."
    empty_text = ""

    print(f"\nOriginal 1: '{sample_text_1}'")
    tokens1 = preprocess_text_simple(sample_text_1)
    print(f"Processed 1: {tokens1}")

    print(f"\nOriginal 2: '{sample_text_2}'")
    tokens2 = preprocess_text_simple(sample_text_2)
    print(f"Processed 2: {tokens2}")

    print(f"\nOriginal 3: '{sample_text_3}'")
    tokens3 = preprocess_text_simple(sample_text_3)
    print(f"Processed 3: {tokens3}")

    print(f"\nOriginal Empty: '{empty_text}'")
    tokens_empty = preprocess_text_simple(empty_text)
    print(f"Processed Empty: {tokens_empty}")
    assert tokens_empty == []


    if SKLEARN_AVAILABLE:
        print("\nTesting TF-IDF Cosine Similarity (requires scikit-learn)...")

        # More distinct texts for similarity testing
        text_a = "The quick brown fox jumps over the lazy dog."
        text_b = "A fast brown fox leaps above a sleepy dog." # Similar
        text_c = "This is a document about apples and oranges." # Different
        text_d = "The quick brown fox jumps over the lazy dog." # Identical to A
        text_e = "the quick brown fox jumps over the lazy dog" # Identical content, different case/punct

        sim_ab = calculate_tfidf_cosine_similarity(text_a, text_b)
        print(f"Similarity A-B ('{text_a}' vs '{text_b}'): {sim_ab:.4f}")
        assert sim_ab > 0.5 # Expect high similarity

        sim_ac = calculate_tfidf_cosine_similarity(text_a, text_c)
        print(f"Similarity A-C ('{text_a}' vs '{text_c}'): {sim_ac:.4f}")
        assert sim_ac < 0.3 # Expect low similarity

        sim_ad = calculate_tfidf_cosine_similarity(text_a, text_d)
        print(f"Similarity A-D (Identical): {sim_ad:.4f}")
        # Due to vectorization nuances, might not be exactly 1.0 but very close
        assert sim_ad > 0.99

        sim_ae = calculate_tfidf_cosine_similarity(text_a, text_e)
        print(f"Similarity A-E (Identical content, diff case/punct): {sim_ae:.4f}")
        # TfidfVectorizer's default preprocessor handles case and some punctuation.
        assert sim_ae > 0.99

        sim_empty1 = calculate_tfidf_cosine_similarity(text_a, "")
        print(f"Similarity A-Empty: {sim_empty1:.4f}")
        assert sim_empty1 == 0.0

        sim_empty2 = calculate_tfidf_cosine_similarity("", "")
        print(f"Similarity Empty-Empty: {sim_empty2:.4f}")
        assert sim_empty2 == 0.0

        print("TF-IDF Cosine Similarity tests completed.")
    else:
        print("\nSkipping TF-IDF Cosine Similarity tests as scikit-learn is not available.")

    print("\nNLP Utilities self-tests finished.")
