"""
Machine Learning models for automated grading
This module contains the core ML models and training utilities
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split
import pickle
import os
from typing import Dict, List, Tuple, Optional
import spacy

class EssayGradingModel:
    """
    Model for grading essay-type questions
    Uses TF-IDF features and ensemble methods
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        self.is_trained = False
        self.feature_names = []
        
    def extract_features(self, texts: List[str]) -> np.ndarray:
        """Extract features from text using TF-IDF and linguistic features"""
        # TF-IDF features
        tfidf_features = self.vectorizer.fit_transform(texts) if not self.is_trained else self.vectorizer.transform(texts)
        
        # Additional linguistic features
        linguistic_features = []
        nlp = spacy.load("en_core_web_sm") if spacy.util.is_package("en_core_web_sm") else None
        
        for text in texts:
            features = []
            
            # Basic text statistics
            word_count = len(text.split())
            sentence_count = text.count('.') + text.count('!') + text.count('?')
            avg_word_length = np.mean([len(word) for word in text.split()])
            
            features.extend([word_count, sentence_count, avg_word_length])
            
            # Advanced linguistic features (if spaCy is available)
            if nlp:
                doc = nlp(text)
                
                # Part-of-speech ratios
                pos_counts = {}
                for token in doc:
                    pos_counts[token.pos_] = pos_counts.get(token.pos_, 0) + 1
                
                total_tokens = len(doc)
                noun_ratio = pos_counts.get('NOUN', 0) / max(total_tokens, 1)
                verb_ratio = pos_counts.get('VERB', 0) / max(total_tokens, 1)
                adj_ratio = pos_counts.get('ADJ', 0) / max(total_tokens, 1)
                
                features.extend([noun_ratio, verb_ratio, adj_ratio])
                
                # Named entities
                entity_count = len(doc.ents)
                features.append(entity_count)
            else:
                # Fallback features if spaCy not available
                features.extend([0.0, 0.0, 0.0, 0])
            
            linguistic_features.append(features)
        
        # Combine TF-IDF and linguistic features
        linguistic_array = np.array(linguistic_features)
        combined_features = np.hstack([tfidf_features.toarray(), linguistic_array])
        
        return combined_features
    
    def train(self, texts: List[str], scores: List[float]) -> Dict:
        """Train the grading model"""
        if len(texts) != len(scores):
            raise ValueError("Texts and scores must have same length")
        
        # Extract features
        X = self.extract_features(texts)
        y = np.array(scores)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        metrics = {
            'train_mse': mean_squared_error(y_train, train_pred),
            'test_mse': mean_squared_error(y_test, test_pred),
            'train_mae': mean_absolute_error(y_train, train_pred),
            'test_mae': mean_absolute_error(y_test, test_pred),
            'train_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        return metrics
    
    def predict(self, texts: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """Predict scores for given texts"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X = self.extract_features(texts)
        predictions = self.model.predict(X)
        
        # Calculate confidence based on model variance
        if hasattr(self.model, 'estimators_'):
            # For RandomForest, use prediction variance as confidence
            all_predictions = np.array([tree.predict(X) for tree in self.model.estimators_])
            confidence = 1 / (1 + np.var(all_predictions, axis=0))
        else:
            # Default confidence
            confidence = np.ones(len(predictions)) * 0.8
        
        return predictions, confidence
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        model_data = {
            'vectorizer': self.vectorizer,
            'model': self.model,
            'is_trained': self.is_trained,
            'feature_names': self.feature_names
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vectorizer = model_data['vectorizer']
        self.model = model_data['model']
        self.is_trained = model_data['is_trained']
        self.feature_names = model_data.get('feature_names', [])

class MathGradingModel:
    """
    Model for grading mathematical answers
    Uses pattern matching and symbolic evaluation
    """
    
    def __init__(self):
        self.answer_patterns = {}
        self.scoring_rules = {}
    
    def add_answer_pattern(self, question_id: str, correct_answers: List[str], partial_credit_rules: Dict):
        """Add answer patterns for a specific question"""
        self.answer_patterns[question_id] = {
            'correct_answers': correct_answers,
            'partial_credit': partial_credit_rules
        }
    
    def grade_mathematical_answer(self, answer: str, question_id: str) -> Dict:
        """Grade a mathematical answer"""
        if question_id not in self.answer_patterns:
            return self._grade_generic_math(answer)
        
        patterns = self.answer_patterns[question_id]
        correct_answers = patterns['correct_answers']
        
        # Clean and normalize answer
        clean_answer = self._clean_math_answer(answer)
        
        # Check exact matches
        for correct in correct_answers:
            if clean_answer == self._clean_math_answer(correct):
                return {
                    'score': 100.0,
                    'confidence': 0.95,
                    'feedback': 'Correct answer',
                    'method': 'exact_match'
                }
        
        # Check partial credit
        partial_score = 0.0
        feedback_items = []
        
        for rule_name, rule_data in patterns['partial_credit'].items():
            if self._check_partial_rule(clean_answer, rule_data):
                partial_score += rule_data.get('points', 0)
                feedback_items.append(rule_data.get('feedback', f'Partial credit: {rule_name}'))
        
        return {
            'score': min(100.0, partial_score),
            'confidence': 0.7,
            'feedback': '; '.join(feedback_items) if feedback_items else 'Incorrect answer',
            'method': 'partial_credit'
        }
    
    def _clean_math_answer(self, answer: str) -> str:
        """Clean and normalize mathematical answer"""
        import re
        
        # Remove whitespace
        clean = re.sub(r'\s+', '', answer.lower())
        
        # Normalize common mathematical expressions
        clean = clean.replace('×', '*')
        clean = clean.replace('÷', '/')
        clean = clean.replace('−', '-')
        
        # Remove common prefixes
        clean = re.sub(r'^(answer:?|solution:?|result:?)', '', clean)
        
        return clean
    
    def _check_partial_rule(self, answer: str, rule_data: Dict) -> bool:
        """Check if answer matches partial credit rule"""
        import re
        
        rule_type = rule_data.get('type', 'contains')
        pattern = rule_data.get('pattern', '')
        
        if rule_type == 'contains':
            return pattern in answer
        elif rule_type == 'regex':
            return bool(re.search(pattern, answer))
        elif rule_type == 'numeric_range':
            try:
                value = float(re.search(r'-?\d+\.?\d*', answer).group())
                min_val = rule_data.get('min', float('-inf'))
                max_val = rule_data.get('max', float('inf'))
                return min_val <= value <= max_val
            except:
                return False
        
        return False
    
    def _grade_generic_math(self, answer: str) -> Dict:
        """Grade mathematical answer without specific patterns"""
        import re
        
        score = 0.0
        feedback = []
        
        # Check for mathematical elements
        has_numbers = bool(re.search(r'\d+', answer))
        has_operations = bool(re.search(r'[+\-*/=]', answer))
        has_variables = bool(re.search(r'[a-z]', answer.lower()))
        
        if has_numbers:
            score += 20
            feedback.append('Contains numerical values')
        
        if has_operations:
            score += 30
            feedback.append('Shows mathematical operations')
        
        if has_variables:
            score += 20
            feedback.append('Uses variables appropriately')
        
        # Length-based scoring
        word_count = len(answer.split())
        if word_count >= 10:
            score += 20
            feedback.append('Provides detailed working')
        elif word_count >= 5:
            score += 10
            feedback.append('Shows some working')
        
        return {
            'score': min(100.0, score),
            'confidence': 0.6,
            'feedback': '; '.join(feedback) if feedback else 'Minimal mathematical content',
            'method': 'generic_math'
        }

class GradingModelManager:
    """
    Manager class for all grading models
    Handles model selection and coordination
    """
    
    def __init__(self):
        self.essay_model = EssayGradingModel()
        self.math_model = MathGradingModel()
        self.models_loaded = False
        self.model_dir = "trained_models"
    
    def initialize_models(self):
        """Initialize and load pre-trained models"""
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Try to load existing models
        essay_model_path = os.path.join(self.model_dir, "essay_model.pkl")
        if os.path.exists(essay_model_path):
            try:
                self.essay_model.load_model(essay_model_path)
            except Exception as e:
                print(f"Failed to load essay model: {e}")
        
        # Initialize math model with common patterns
        self._initialize_math_patterns()
        
        self.models_loaded = True
    
    def _initialize_math_patterns(self):
        """Initialize common mathematical answer patterns"""
        # Example patterns for common math problems
        self.math_model.add_answer_pattern(
            "algebra_basic",
            ["x=2", "x=2.0", "2"],
            {
                "correct_variable": {
                    "type": "contains",
                    "pattern": "x=",
                    "points": 30,
                    "feedback": "Correct variable identification"
                },
                "numeric_close": {
                    "type": "numeric_range",
                    "min": 1.8,
                    "max": 2.2,
                    "points": 50,
                    "feedback": "Answer is close to correct value"
                }
            }
        )
    
    def grade_answer(self, answer_text: str, subject: str, question_type: str = "essay") -> Dict:
        """
        Grade an answer using appropriate model
        """
        if not self.models_loaded:
            self.initialize_models()
        
        if subject.lower() == "mathematics" or question_type == "math":
            return self.math_model.grade_mathematical_answer(answer_text, "generic")
        else:
            # Use essay model for other subjects
            try:
                if self.essay_model.is_trained:
                    predictions, confidence = self.essay_model.predict([answer_text])
                    return {
                        'score': float(predictions[0]),
                        'confidence': float(confidence[0]),
                        'feedback': 'AI-generated score',
                        'method': 'ml_model'
                    }
                else:
                    # Fallback to simple scoring if model not trained
                    return self._simple_essay_score(answer_text)
            except Exception as e:
                return {
                    'score': 50.0,
                    'confidence': 0.3,
                    'feedback': f'Scoring error: {str(e)}',
                    'method': 'error_fallback'
                }
    
    def _simple_essay_score(self, text: str) -> Dict:
        """Simple rule-based essay scoring as fallback"""
        words = text.split()
        word_count = len(words)
        
        # Base score from length
        if word_count < 50:
            score = 40 + (word_count / 50) * 20
        elif word_count < 200:
            score = 60 + ((word_count - 50) / 150) * 25
        else:
            score = 85 + min(10, (word_count - 200) / 100 * 10)
        
        # Adjust for basic quality indicators
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        if sentence_count > 0:
            avg_sentence_length = word_count / sentence_count
            if 10 <= avg_sentence_length <= 25:
                score += 5  # Good sentence length
        
        # Check for transition words
        transition_words = ['however', 'therefore', 'moreover', 'furthermore', 'additionally']
        transition_count = sum(1 for word in transition_words if word in text.lower())
        score += min(5, transition_count * 2)
        
        return {
            'score': min(100.0, max(0.0, score)),
            'confidence': 0.7,
            'feedback': 'Rule-based scoring',
            'method': 'simple_rules'
        }
    
    def train_essay_model(self, training_data: List[Dict]) -> Dict:
        """
        Train the essay grading model with provided data
        Expected format: [{'text': str, 'score': float}, ...]
        """
        texts = [item['text'] for item in training_data]
        scores = [item['score'] for item in training_data]
        
        metrics = self.essay_model.train(texts, scores)
        
        # Save trained model
        model_path = os.path.join(self.model_dir, "essay_model.pkl")
        self.essay_model.save_model(model_path)
        
        return metrics
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        return {
            'essay_model_trained': self.essay_model.is_trained,
            'math_patterns_loaded': len(self.math_model.answer_patterns),
            'models_loaded': self.models_loaded,
            'model_directory': self.model_dir
        }
