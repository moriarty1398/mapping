from typing import List

class DocumentRanker:
    def rank_documents(self, docs: List[dict], question_info: dict) -> List[dict]:
        scored_docs = []
        for doc in docs:
            score = self.calculate_relevance_score(doc, question_info)
            scored_docs.append((score, doc))
        
        return [doc for _, doc in sorted(scored_docs, reverse=True)]
    
    def calculate_relevance_score(self, doc: dict, question_info: dict) -> float:
        score = 0.0
        
        # Keyword matching
        keyword_score = self.keyword_match_score(doc['content'], question_info['keywords'])
        
        # Semantic similarity
        semantic_score = self.semantic_similarity(doc['content'], question_info)
        
        # Entity matching
        entity_score = self.entity_match_score(doc['content'], question_info['entities'])
        
        # Combine scores with weights
        score = (keyword_score * 0.3 + 
                semantic_score * 0.5 + 
                entity_score * 0.2)
        
        return score 