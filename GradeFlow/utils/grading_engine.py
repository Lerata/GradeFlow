import streamlit as st
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple, Optional
import re
import json
import os

# Load spaCy model (cached)
@st.cache_resource
def load_nlp_model():
    """Load and cache spaCy model"""
    try:
        nlp = spacy.load("en_core_web_sm")
        return nlp
    except OSError:
        st.error("spaCy English model not found. Please install with: python -m spacy download en_core_web_sm")
        return None

# Load grading rubrics
@st.cache_data
def load_rubrics():
    """Load grading rubrics from JSON file"""
    try:
        with open("data/sample_rubrics.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default rubrics if file not found
        return {
            "english": {
                "criteria": {
                    "content": {"weight": 0.4, "max_score": 25},
                    "grammar": {"weight": 0.2, "max_score": 25},
                    "structure": {"weight": 0.2, "max_score": 25},
                    "vocabulary": {"weight": 0.2, "max_score": 25}
                },
                "keywords": ["essay", "literature", "writing", "analysis"]
            },
            "science": {
                "criteria": {
                    "accuracy": {"weight": 0.5, "max_score": 50},
                    "explanation": {"weight": 0.3, "max_score": 30},
                    "methodology": {"weight": 0.2, "max_score": 20}
                },
                "keywords": ["experiment", "hypothesis", "theory", "analysis"]
            },
            "mathematics": {
                "criteria": {
                    "correctness": {"weight": 0.6, "max_score": 60},
                    "method": {"weight": 0.3, "max_score": 30},
                    "presentation": {"weight": 0.1, "max_score": 10}
                },
                "keywords": ["equation", "solve", "calculate", "proof"]
            }
        }

def classify_subject(text: str) -> str:
    """Classify the subject of the answer text"""
    rubrics = load_rubrics()
    
    text_lower = text.lower()
    subject_scores = {}
    
    for subject, data in rubrics.items():
        score = 0
        for keyword in data["keywords"]:
            score += text_lower.count(keyword)
        subject_scores[subject] = score
    
    # Return subject with highest score, default to 'english'
    return max(subject_scores, key=subject_scores.get) if any(subject_scores.values()) else 'english'

def analyze_grammar(text: str, nlp) -> Dict:
    """Analyze grammar and language quality"""
    if not nlp:
        return {"score": 0.5, "issues": ["NLP model not available"]}
    
    doc = nlp(text)
    
    # Count sentences and words
    sentences = list(doc.sents)
    words = [token for token in doc if token.is_alpha]
    
    if not sentences or not words:
        return {"score": 0.0, "issues": ["No valid text found"]}
    
    # Grammar analysis
    issues = []
    grammar_score = 1.0
    
    # Check sentence structure
    avg_sentence_length = len(words) / len(sentences)
    if avg_sentence_length < 5:
        issues.append("Sentences are too short")
        grammar_score -= 0.1
    elif avg_sentence_length > 30:
        issues.append("Sentences are too long")
        grammar_score -= 0.1
    
    # Check for common grammar issues
    pos_tags = [token.pos_ for token in doc]
    
    # Excessive use of certain parts of speech
    if pos_tags.count('PRON') / len(pos_tags) > 0.15:
        issues.append("Overuse of pronouns")
        grammar_score -= 0.05
    
    # Check for spelling issues (simplified)
    misspelled = [token.text for token in doc if token.is_alpha and not token.is_stop and len(token.text) > 3 and token.is_oov]
    if len(misspelled) > len(words) * 0.1:
        issues.append(f"Potential spelling issues: {len(misspelled)} words")
        grammar_score -= 0.1
    
    return {
        "score": max(0.0, grammar_score),
        "issues": issues[:5],  # Limit to 5 issues
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": avg_sentence_length
    }

def analyze_content_quality(text: str, subject: str, nlp) -> Dict:
    """Analyze content quality based on subject"""
    if not nlp:
        return {"score": 0.5, "reasoning": "NLP model not available"}
    
    doc = nlp(text)
    words = [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop]
    
    # Basic content scoring
    content_score = 0.5  # Base score
    reasoning = []
    
    # Length-based scoring
    word_count = len(words)
    if word_count < 50:
        reasoning.append("Answer is too brief")
        content_score -= 0.2
    elif word_count > 300:
        reasoning.append("Comprehensive answer length")
        content_score += 0.1
    
    # Subject-specific analysis
    rubrics = load_rubrics()
    subject_data = rubrics.get(subject, rubrics['english'])
    
    # Check for subject-relevant keywords
    keyword_matches = sum(1 for keyword in subject_data["keywords"] if keyword in text.lower())
    if keyword_matches > 0:
        reasoning.append(f"Contains {keyword_matches} relevant keywords")
        content_score += min(0.2, keyword_matches * 0.05)
    
    # Check for entities and complex concepts
    entities = [ent.label_ for ent in doc.ents]
    if entities:
        reasoning.append(f"Contains {len(entities)} named entities")
        content_score += min(0.15, len(entities) * 0.02)
    
    # Vocabulary diversity
    unique_words = len(set(words))
    if word_count > 0:
        lexical_diversity = unique_words / word_count
        if lexical_diversity > 0.7:
            reasoning.append("Good vocabulary diversity")
            content_score += 0.1
        elif lexical_diversity < 0.4:
            reasoning.append("Limited vocabulary diversity")
            content_score -= 0.1
    
    return {
        "score": min(1.0, max(0.0, content_score)),
        "reasoning": reasoning,
        "word_count": word_count,
        "unique_words": unique_words,
        "entities": len(entities)
    }

def analyze_structure(text: str, nlp) -> Dict:
    """Analyze text structure and organization"""
    if not nlp:
        return {"score": 0.5, "feedback": "NLP model not available"}
    
    doc = nlp(text)
    sentences = list(doc.sents)
    
    structure_score = 0.5
    feedback = []
    
    if len(sentences) < 3:
        feedback.append("Answer needs better paragraph structure")
        structure_score -= 0.2
    elif len(sentences) > 15:
        feedback.append("Well-structured with multiple paragraphs")
        structure_score += 0.1
    
    # Check for transition words/phrases
    transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'additionally', 
                       'consequently', 'nevertheless', 'meanwhile', 'finally', 'in conclusion']
    
    transition_count = sum(1 for word in transition_words if word in text.lower())
    if transition_count > 0:
        feedback.append(f"Good use of {transition_count} transition words")
        structure_score += min(0.15, transition_count * 0.03)
    
    return {
        "score": min(1.0, max(0.0, structure_score)),
        "feedback": feedback,
        "sentence_count": len(sentences)
    }

def grade_mathematical_answer(text: str) -> Dict:
    """Grade mathematical answers"""
    # Extract numbers and mathematical expressions
    numbers = re.findall(r'-?\d+\.?\d*', text)
    equations = re.findall(r'[x-z]\s*[=+\-*/]\s*[\dx+\-*/\s]+', text, re.IGNORECASE)
    
    score = 0.3  # Base score for attempting
    feedback = []
    
    if numbers:
        feedback.append(f"Contains {len(numbers)} numerical values")
        score += min(0.2, len(numbers) * 0.05)
    
    if equations:
        feedback.append(f"Shows {len(equations)} mathematical expressions")
        score += min(0.3, len(equations) * 0.1)
    
    # Check for mathematical keywords
    math_keywords = ['equation', 'solve', 'calculate', 'answer', 'result', 'therefore', 'equals']
    keyword_count = sum(1 for keyword in math_keywords if keyword in text.lower())
    
    if keyword_count > 0:
        feedback.append(f"Uses {keyword_count} mathematical terms")
        score += min(0.2, keyword_count * 0.04)
    
    return {
        "score": min(1.0, score),
        "feedback": feedback,
        "numbers_found": len(numbers),
        "equations_found": len(equations)
    }

def calculate_final_grade(analysis_results: Dict, subject: str) -> Dict:
    """Calculate final grade based on analysis results"""
    rubrics = load_rubrics()
    subject_criteria = rubrics.get(subject, rubrics['english'])["criteria"]
    
    total_score = 0
    max_possible = 0
    breakdown = {}
    
    for criterion, config in subject_criteria.items():
        if criterion in analysis_results:
            criterion_score = analysis_results[criterion]["score"] * config["max_score"]
            total_score += criterion_score
            breakdown[criterion] = {
                "score": criterion_score,
                "max_score": config["max_score"],
                "percentage": analysis_results[criterion]["score"] * 100
            }
        max_possible += config["max_score"]
    
    # Calculate percentage and letter grade
    percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
    
    if percentage >= 90:
        letter_grade = "A"
    elif percentage >= 80:
        letter_grade = "B"
    elif percentage >= 70:
        letter_grade = "C"
    elif percentage >= 60:
        letter_grade = "D"
    else:
        letter_grade = "F"
    
    return {
        "total_score": round(total_score, 2),
        "max_possible": max_possible,
        "percentage": round(percentage, 2),
        "letter_grade": letter_grade,
        "breakdown": breakdown
    }

def grade_answer(answer_text: str, question_number: int = 1) -> Dict:
    """Main grading function"""
    if not answer_text or not answer_text.strip():
        return {
            "error": "No answer text provided",
            "score": 0,
            "confidence": 0
        }
    
    nlp = load_nlp_model()
    
    # Classify subject
    subject = classify_subject(answer_text)
    
    # Perform different analyses
    analysis_results = {}
    
    if subject == "mathematics":
        analysis_results["correctness"] = grade_mathematical_answer(answer_text)
        analysis_results["method"] = {"score": 0.7}  # Simplified for demo
        analysis_results["presentation"] = {"score": 0.8}  # Simplified for demo
    else:
        # For English and Science subjects
        analysis_results["content"] = analyze_content_quality(answer_text, subject, nlp)
        analysis_results["grammar"] = analyze_grammar(answer_text, nlp)
        analysis_results["structure"] = analyze_structure(answer_text, nlp)
        
        if subject == "science":
            analysis_results["accuracy"] = analysis_results["content"]  # Map content to accuracy
            analysis_results["explanation"] = analysis_results["structure"]  # Map structure to explanation
            analysis_results["methodology"] = {"score": 0.7}  # Simplified
    
    # Calculate final grade
    final_grade = calculate_final_grade(analysis_results, subject)
    
    # Calculate confidence based on text quality and analysis consistency
    confidence = 0.8  # Base confidence
    if analysis_results.get("grammar", {}).get("issues"):
        confidence -= 0.1
    if len(answer_text.split()) < 20:
        confidence -= 0.2
    
    return {
        "question_number": question_number,
        "subject": subject,
        "analysis": analysis_results,
        "grade": final_grade,
        "confidence": max(0.3, min(0.95, confidence)),
        "suggestions": generate_feedback_suggestions(analysis_results, subject)
    }

def generate_feedback_suggestions(analysis_results: Dict, subject: str) -> List[str]:
    """Generate improvement suggestions based on analysis"""
    suggestions = []
    
    # Grammar suggestions
    grammar_analysis = analysis_results.get("grammar", {})
    if grammar_analysis.get("score", 1.0) < 0.7:
        suggestions.append("Focus on improving grammar and sentence structure")
    
    # Content suggestions
    content_analysis = analysis_results.get("content", {})
    if content_analysis.get("word_count", 0) < 100:
        suggestions.append("Provide more detailed explanations and examples")
    
    # Structure suggestions  
    structure_analysis = analysis_results.get("structure", {})
    if structure_analysis.get("score", 1.0) < 0.6:
        suggestions.append("Organize your answer with clear paragraphs and transitions")
    
    # Subject-specific suggestions
    if subject == "mathematics":
        suggestions.append("Show all calculation steps clearly")
        suggestions.append("Include units in your final answer where applicable")
    elif subject == "science":
        suggestions.append("Support your explanations with scientific evidence")
        suggestions.append("Use proper scientific terminology")
    else:  # English
        suggestions.append("Include specific examples to support your arguments")
        suggestions.append("Expand your vocabulary usage")
    
    return suggestions[:3]  # Limit to 3 suggestions
