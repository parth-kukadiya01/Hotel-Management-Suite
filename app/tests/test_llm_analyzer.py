import pytest
from unittest.mock import Mock, patch
from app.services.llm_analyzer import LLMAnalyzer
from app.models import SentimentType, UrgencyType


@pytest.fixture
def llm_analyzer():
    """Fixture for LLMAnalyzer instance"""
    return LLMAnalyzer()


@pytest.fixture
def mock_openai_response():
    """Fixture for mocked OpenAI response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = """{
        "sentiment": "Positive",
        "topics": ["Service", "Cleanliness"],
        "urgency": "Standard",
        "reasoning": "Positive review about good service"
    }"""
    return mock_response


@pytest.fixture
def mock_critical_response():
    """Fixture for critical review response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = """{
        "sentiment": "Negative",
        "topics": ["Cleanliness", "Service"],
        "urgency": "Critical",
        "reasoning": "Mentions bed bugs which is a critical health issue"
    }"""
    return mock_response


class TestLLMAnalyzer:
    """Test suite for LLM Analyzer"""
    
    def test_analyze_review_positive(self, llm_analyzer, mock_openai_response):
        """Test analyzing a positive review"""
        with patch.object(llm_analyzer.client.chat.completions, 'create', return_value=mock_openai_response):
            result = llm_analyzer.analyze_review("Great hotel! Staff was very helpful and room was clean.")
            
            assert result.sentiment == SentimentType.POSITIVE
            assert "Service" in result.topics
            assert "Cleanliness" in result.topics
            assert result.urgency == UrgencyType.STANDARD
    
    def test_analyze_review_critical(self, llm_analyzer, mock_critical_response):
        """Test analyzing a critical review"""
        with patch.object(llm_analyzer.client.chat.completions, 'create', return_value=mock_critical_response):
            result = llm_analyzer.analyze_review("Found bed bugs in the room!")
            
            assert result.sentiment == SentimentType.NEGATIVE
            assert result.urgency == UrgencyType.CRITICAL
            assert "Cleanliness" in result.topics
    
    def test_fallback_analysis_on_error(self, llm_analyzer):
        """Test fallback analysis when LLM fails"""
        with patch.object(llm_analyzer.client.chat.completions, 'create', side_effect=Exception("API Error")):
            result = llm_analyzer.analyze_review("Bed bugs everywhere! This is terrible!")
            
            # Should still return a valid result using fallback
            assert result.sentiment in [SentimentType.POSITIVE, SentimentType.NEGATIVE, SentimentType.NEUTRAL]
            assert result.urgency == UrgencyType.CRITICAL  # Should detect bed bugs
            assert len(result.topics) > 0
    
    def test_parse_llm_response_valid(self, llm_analyzer):
        """Test parsing valid LLM response"""
        response = {
            "sentiment": "Negative",
            "topics": ["Service", "Value"],
            "urgency": "Standard",
            "reasoning": "Poor service but not critical"
        }
        
        result = llm_analyzer._parse_llm_response(response)
        
        assert result.sentiment == SentimentType.NEGATIVE
        assert result.topics == ["Service", "Value"]
        assert result.urgency == UrgencyType.STANDARD
    
    def test_parse_llm_response_invalid_sentiment(self, llm_analyzer):
        """Test parsing response with invalid sentiment"""
        response = {
            "sentiment": "InvalidSentiment",
            "topics": ["Service"],
            "urgency": "Standard",
            "reasoning": "Test"
        }
        
        result = llm_analyzer._parse_llm_response(response)
        
        # Should default to NEUTRAL for invalid sentiment
        assert result.sentiment == SentimentType.NEUTRAL
    
    def test_parse_llm_response_invalid_topics(self, llm_analyzer):
        """Test parsing response with invalid topics"""
        response = {
            "sentiment": "Positive",
            "topics": ["InvalidTopic", "Service", "AnotherInvalid"],
            "urgency": "Standard",
            "reasoning": "Test"
        }
        
        result = llm_analyzer._parse_llm_response(response)
        
        # Should filter out invalid topics
        assert "Service" in result.topics
        assert "InvalidTopic" not in result.topics
        assert "AnotherInvalid" not in result.topics
    
    def test_fallback_analysis_positive(self, llm_analyzer):
        """Test fallback analysis for positive review"""
        result = llm_analyzer._fallback_analysis("Amazing hotel! Excellent service and wonderful staff!")
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.urgency == UrgencyType.STANDARD
    
    def test_fallback_analysis_negative(self, llm_analyzer):
        """Test fallback analysis for negative review"""
        result = llm_analyzer._fallback_analysis("Terrible experience. Horrible service and awful room.")
        
        assert result.sentiment == SentimentType.NEGATIVE
    
    def test_fallback_analysis_critical_keywords(self, llm_analyzer):
        """Test fallback detects critical keywords"""
        critical_texts = [
            "Found bed bugs in the sheets",
            "Got food poisoning from restaurant",
            "My wallet was stolen from the room",
            "Very dangerous and unsafe environment"
        ]
        
        for text in critical_texts:
            result = llm_analyzer._fallback_analysis(text)
            assert result.urgency == UrgencyType.CRITICAL, f"Failed to detect critical urgency in: {text}"
    
    def test_create_analysis_prompt(self, llm_analyzer):
        """Test prompt creation"""
        review_text = "Great hotel with excellent service"
        prompt = llm_analyzer._create_analysis_prompt(review_text)
        
        assert review_text in prompt
        assert "sentiment" in prompt.lower()
        assert "topics" in prompt.lower()
        assert "urgency" in prompt.lower()
        assert "JSON" in prompt