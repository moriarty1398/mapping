from typing import List
import re
from collections import Counter

class TextProcessor:
    def __init__(self):
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except Exception as e:
            print(f"SpaCy model loading failed: {e}")
            self.nlp = None
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text using fallback if spaCy isn't available"""
        if self.nlp:
            # SpaCy-based extraction
            doc = self.nlp(text)
            keywords = [token.text.lower() for token in doc 
                       if token.pos_ in ['NOUN', 'VERB'] and not token.is_stop]
        else:
            # Fallback: simple word frequency-based extraction
            words = re.findall(r'\b\w+\b', text.lower())
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
            words = [w for w in words if w not in stop_words and len(w) > 2]
            # Get most common words
            keywords = [word for word, _ in Counter(words).most_common(5)]
        
        return list(set(keywords))

    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word (simplified version)"""
        # Simple fallback without WordNet
        return [word]  # Return just the original word if no synonyms available

    def classify_question_type(self, question: str) -> str:
        """Determine the type of question using simple pattern matching"""
        question = question.lower().strip()
        
        # Simple rule-based classification
        if question.startswith(('what', 'which')):
            return 'definition'
        elif question.startswith('how'):
            return 'process'
        elif question.startswith('why'):
            return 'explanation'
        elif question.startswith('when'):
            return 'temporal'
        elif question.startswith('where'):
            return 'location'
        elif question.startswith(('who', 'whom')):
            return 'person'
        else:
            return 'general'

    def extract_entities(self, text: str) -> List[str]:
        """Extract potential entities using fallback if spaCy isn't available"""
        if self.nlp:
            # SpaCy-based extraction
            doc = self.nlp(text)
            return [ent.text for ent in doc.ents]
        else:
            # Fallback: simple capitalized words heuristic
            words = re.findall(r'\b[A-Z][a-z]+\b', text)
            return list(set(words)) 

    def split_into_passages(self, text: str, max_length: int = 500) -> List[str]:
        """Split text into manageable passages"""
        # First try to split by double newlines (paragraphs)
        passages = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # If passages are too long, split them further
        final_passages = []
        for passage in passages:
            if len(passage) <= max_length:
                final_passages.append(passage)
            else:
                # Split by sentences if passage is too long
                sentences = [s.strip() for s in re.split(r'[.!?]+', passage) if s.strip()]
                current_passage = []
                current_length = 0
                
                for sentence in sentences:
                    if current_length + len(sentence) > max_length and current_passage:
                        final_passages.append(' '.join(current_passage))
                        current_passage = [sentence]
                        current_length = len(sentence)
                    else:
                        current_passage.append(sentence)
                        current_length += len(sentence)
                
                if current_passage:
                    final_passages.append(' '.join(current_passage))
        
        return final_passages

    def calculate_passage_relevance(self, passage: str, keywords: List[str], entities: List[str]) -> float:
        """Calculate relevance score for a passage"""
        score = 0.0
        passage_lower = passage.lower()
        
        # Keyword matching
        for keyword in keywords:
            if keyword.lower() in passage_lower:
                score += 1.0
        
        # Entity matching
        for entity in entities:
            if entity in passage:
                score += 2.0  # Weight entities more heavily
        
        # Normalize by passage length to avoid favoring longer passages
        score = score / (len(passage.split()) + 1)  # Add 1 to avoid division by zero
        
        return score 