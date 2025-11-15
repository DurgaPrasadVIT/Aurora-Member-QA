from typing import List, Optional, Tuple, Set
import logging
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


logger = logging.getLogger("aurora_app")


class QASystem:
    """
    TF-IDF based QA system with:
    - member-name awareness (full name and first/last name matching)
    - ambiguity handling when multiple members share a name token
    - topic consistency checks using keyword overlap & synonym groups
    - clean, user-friendly answer formatting.

    It prefers:
    - matching the member name mentioned in the question
    - matching topic words between question and answer

    If the data does not clearly support an answer, it returns:
        "The information is not available in the member messages."
    """

    def __init__(self) -> None:
        self.vectorizer = None  # type: ignore[assignment]
        self.doc_matrix = None  # type: ignore[assignment]
        self.documents: List[str] = []
        self.user_names: List[Optional[str]] = []

        # Basic stopwords for overlap checks (not exhaustive, just enough)
        self.stopwords: Set[str] = {
            "the", "a", "an", "and", "or", "but", "if", "then", "else",
            "is", "am", "are", "was", "were", "be", "been", "being",
            "to", "of", "in", "on", "at", "for", "with", "by", "from",
            "as", "it", "this", "that", "these", "those",
            "do", "does", "did", "doing",
            "have", "has", "had", "having",
            "i", "you", "he", "she", "we", "they", "them", "him", "her",
            "my", "your", "his", "their", "our",
            "me", "us",
            "what", "when", "where", "why", "how",
            "many", "much",
            "please", "can", "could", "would", "should",
            "member", "user", "message", "timestamp", "id", "user_id",
        }

        # Synonym groups for important topics
        self.topic_groups: List[Set[str]] = [
            # cars / vehicles
            {"car", "cars", "vehicle", "vehicles", "garage", "truck", "suv", "sedan"},
            # restaurants / dining
            {
                "restaurant", "restaurants", "dinner", "lunch", "brunch",
                "cafe", "bistro", "eat", "food", "dining", "table", "reservation",
            },
            # travel / London
            {"trip", "travel", "flight", "vacation", "holiday", "london", "journey"},
        ]

    # ---------- internal helpers ----------

    @staticmethod
    def _extract_user_name(doc: str) -> Optional[str]:
        """
        Documents from build_documents look like:
            "User: <name> | Timestamp: ... | Message: ... | id: ... | user_id: ..."
        This returns <name> if present.
        """
        prefix = "User:"
        if not doc.startswith(prefix):
            return None

        rest = doc[len(prefix):].lstrip()
        sep = " |"
        end_idx = rest.find(sep)
        if end_idx == -1:
            name = rest.strip()
        else:
            name = rest[:end_idx].strip()

        return name or None

    @staticmethod
    def _parse_doc_fields(doc: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse document string into (user_name, timestamp, message).
        We ignore ids and other technical fields for answer formatting.
        """
        user_name: Optional[str] = None
        timestamp: Optional[str] = None
        message: Optional[str] = None

        parts = [p.strip() for p in doc.split("|")]

        for part in parts:
            if part.startswith("User:"):
                user_name = part[len("User:"):].strip()
            elif part.startswith("Timestamp:"):
                timestamp = part[len("Timestamp:"):].strip()
            elif part.startswith("Message:"):
                message = part[len("Message:"):].strip()

        return user_name or None, timestamp or None, message or None

    def _tokenize(self, text: str) -> Set[str]:
        """
        Lowercase, simple word tokenization, remove basic stopwords.
        """
        tokens = re.findall(r"\w+", text.lower())
        return {t for t in tokens if t not in self.stopwords}

    def _topic_overlap_ok(
        self,
        question: str,
        answer_doc: str,
        user_name: Optional[str],
    ) -> bool:
        """
        Check if the answer_doc is topically consistent with the question.

        We require:
        - some overlap between content words (excluding stopwords and member name), OR
        - overlap through one of the synonym groups (cars, restaurants, travel)
        """
        q_tokens = self._tokenize(question)
        a_tokens = self._tokenize(answer_doc)

        # Remove the member name tokens from both sides, so we don't "overlap"
        # just because of the name.
        if user_name:
            name_parts = re.findall(r"\w+", user_name.lower())
            for np in name_parts:
                q_tokens.discard(np)
                a_tokens.discard(np)

        # Direct content overlap
        direct_overlap = q_tokens & a_tokens
        if direct_overlap:
            return True

        # Topic-group overlap (e.g., question talks about cars, answer mentions vehicles)
        for group in self.topic_groups:
            if (q_tokens & group) and (a_tokens & group):
                return True

        # No meaningful overlap
        return False

    # ---------- public API ----------

    def build(self, docs: List[str]) -> None:
        """
        Build the TF-IDF index over the provided documents and extract user names.
        """
        self.documents = docs or []
        if not self.documents:
            logger.warning("QASystem.build called with no documents.")
            self.vectorizer = None
            self.doc_matrix = None
            self.user_names = []
            return

        logger.info("Building TF-IDF index for %d documents...", len(self.documents))

        # Extract user names from each document
        self.user_names = [self._extract_user_name(d) for d in self.documents]

        # Unigram + bigram features, English stopwords for the vectorizer
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
        )
        self.doc_matrix = self.vectorizer.fit_transform(self.documents)

        logger.info("QASystem index built over %d documents.", len(self.documents))

    def answer(self, question: str) -> str:
        """
        Return a clean, user-friendly answer with safeguards:
        - if no data/index: explain that there is no data
        - if question is empty: return a friendly message
        - restrict docs to the member name mentioned in the question
          (using full-name first, then first/last name tokens with ambiguity handling)
        - use stricter similarity if we couldn't confidently tie to one member
        - ensure there is topic overlap between question and answer
        - format the answer as: "Member: ... | Timestamp: ... | Message: ..."
        """
        if (
            not self.documents
            or self.vectorizer is None
            or self.doc_matrix is None
        ):
            return (
                "I don't have any member messages to answer from yet. "
                "Please try again later."
            )

        question = question.strip()
        if not question:
            return "Question has no meaningful content."

        q_lower = question.lower()
        q_tokens = self._tokenize(question)

        # ---------- 1) Candidate docs by member name ----------

        candidate_indices = list(range(len(self.documents)))
        restricted_by_name = False  # track if we have a clear member match

        # 1a) Try strict full-name match first
        full_match_indices: List[int] = []
        for idx, name in enumerate(self.user_names):
            if name and name.lower() in q_lower:
                full_match_indices.append(idx)

        if full_match_indices:
            candidate_indices = full_match_indices
            restricted_by_name = True
        else:
            # 1b) Fall back to token-based matching (first/last name),
            #     but handle ambiguity when multiple distinct members share the token.
            matches_by_full_name: dict[str, List[int]] = {}

            for idx, name in enumerate(self.user_names):
                if not name:
                    continue
                name_tokens = {
                    t for t in re.findall(r"\w+", name.lower()) if len(t) >= 3
                }
                if name_tokens & q_tokens:
                    matches_by_full_name.setdefault(name, []).append(idx)

            if len(matches_by_full_name) == 1:
                # Exactly one distinct member name matches → safe to restrict.
                only_indices = next(iter(matches_by_full_name.values()))
                candidate_indices = only_indices
                restricted_by_name = True
            else:
                # 0 or multiple distinct member names → ambiguous.
                # Do NOT restrict by name; rely on topic similarity instead.
                candidate_indices = list(range(len(self.documents)))
                restricted_by_name = False

        # ---------- 2) TF-IDF similarity ----------

        q_vec = self.vectorizer.transform([question])
        scores = linear_kernel(q_vec, self.doc_matrix).flatten()

        # Zero scores for docs not in candidates
        if candidate_indices and len(candidate_indices) < len(self.documents):
            allowed = set(candidate_indices)
            for i in range(len(scores)):
                if i not in allowed:
                    scores[i] = 0.0

        best_idx = int(scores.argmax())
        best_score = float(scores[best_idx])

        logger.info(
            "Best similarity score for query: %.4f (restricted_by_name=%s)",
            best_score,
            restricted_by_name,
        )

        # Use a stricter threshold when we're not sure about the member
        min_score = 0.05 if restricted_by_name else 0.15

        # Very weak similarity → don't answer
        if best_score <= 0.0 or best_score < min_score:
            return "The information is not available in the member messages."

        best_doc = self.documents[best_idx]
        user_name, timestamp, message = self._parse_doc_fields(best_doc)

        # ---------- 3) Topic-consistency check ----------

        if not self._topic_overlap_ok(question, best_doc, user_name):
            return "The information is not available in the member messages."

        # ---------- 4) Format a clean answer ----------

        if not user_name and not timestamp and not message:
            # Fall back to raw document if parsing failed badly
            return best_doc

        parts = []
        if user_name:
            parts.append(f"Member: {user_name}")
        if timestamp:
            parts.append(f"Timestamp: {timestamp}")
        if message:
            parts.append(f"Message: {message}")

        if parts:
            return " | ".join(parts)

        # Last resort
        return best_doc
