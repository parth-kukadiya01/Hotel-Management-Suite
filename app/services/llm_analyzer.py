import json
from typing import Dict, Any
from openai import OpenAI
from app.config import settings
from app.schemas import LLMAnalysisResult
from app.models import SentimentType, UrgencyType


class LLMAnalyzer:
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    def analyze_review(self, review_text: str) -> LLMAnalysisResult:
        
        prompt = self._create_analysis_prompt(review_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert hotel review analyzer. Analyze reviews and return structured JSON data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return self._parse_llm_response(result)
            
        except Exception as e:
            # Fallback to basic analysis if LLM fails
            print(f"LLM analysis failed: {e}")
            return self._fallback_analysis(review_text)
    
    def _create_analysis_prompt(self, review_text: str) -> str:
        return f"""Analyze the following hotel review and provide a JSON response with these fields:

1. sentiment: Classify as "Positive", "Negative", or "Neutral"
2. topics: List of topics from: ["Cleanliness", "Service", "Amenities", "Location", "Value"]
3. urgency: Classify as "Critical" or "Standard"
   - Critical: mentions safety concerns, health issues (food poisoning, bed bugs), severe cleanliness problems, theft, discrimination, or violence
   - Standard: everything else
4. reasoning: Brief explanation of your classification

Review text: "{review_text}"

Return ONLY valid JSON in this exact format:
{{
    "sentiment": "Positive|Negative|Neutral",
    "topics": ["topic1", "topic2"],
    "urgency": "Critical|Standard",
    "reasoning": "explanation"
}}"""
    
    def _parse_llm_response(self, result: Dict[str, Any]) -> LLMAnalysisResult:
        sentiment = result.get("sentiment", "Neutral")
        topics = result.get("topics", [])
        urgency = result.get("urgency", "Standard")
        reasoning = result.get("reasoning", "")
        
        try:
            sentiment_enum = SentimentType(sentiment)
        except ValueError:
            sentiment_enum = SentimentType.NEUTRAL
        
        try:
            urgency_enum = UrgencyType(urgency)
        except ValueError:
            urgency_enum = UrgencyType.STANDARD
        
        valid_topics = ["Cleanliness", "Service", "Amenities", "Location", "Value"]
        filtered_topics = [t for t in topics if t in valid_topics]
        
        return LLMAnalysisResult(
            sentiment=sentiment_enum,
            topics=filtered_topics if filtered_topics else ["Service"],
            urgency=urgency_enum,
            reasoning=reasoning
        )
    
    def _fallback_analysis(self, review_text: str) -> LLMAnalysisResult:
        text_lower = review_text.lower()
        
        # Simple sentiment analysis
        positive_words = ["great", "excellent", "amazing", "wonderful", "fantastic", "love"]
        negative_words = ["bad", "terrible", "horrible", "awful", "worst", "dirty"]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = SentimentType.POSITIVE
        elif neg_count > pos_count:
            sentiment = SentimentType.NEGATIVE
        else:
            sentiment = SentimentType.NEUTRAL
        
        # Simple urgency detection
        critical_keywords = [
            "bed bugs", "bedbugs", "food poisoning", "theft", "stolen",
            "safety", "dangerous", "discrimination", "assault", "violence"
        ]
        urgency = UrgencyType.CRITICAL if any(kw in text_lower for kw in critical_keywords) else UrgencyType.STANDARD
        
        # Default topics
        topics = ["Service"]
        if "clean" in text_lower or "dirty" in text_lower:
            topics.append("Cleanliness")
        if "location" in text_lower:
            topics.append("Location")
        
        return LLMAnalysisResult(
            sentiment=sentiment,
            topics=topics,
            urgency=urgency,
            reasoning="Fallback analysis due to LLM error"
        )


# Singleton instance
llm_analyzer = LLMAnalyzer()