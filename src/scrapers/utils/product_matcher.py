"""
Product name matching utility using local models
"""
import re
import numpy as np
from sentence_transformers import SentenceTransformer

class ProductMatcher:
    def __init__(self, threshold=0.7, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the product matcher with a threshold and model
        
        Args:
            threshold: Similarity threshold (0.0 to 1.0) for accepting matches
            model_name: Sentence transformer model to use
        """
        self.threshold = threshold
        try:
            self.model = SentenceTransformer(model_name)
            self.model_loaded = True
            
        except Exception as e:
            print(f"Warning: Could not load SentenceTransformer model: {e}")
            print("Falling back to rule-based matching")
            self.model_loaded = False
            
        # Product categories and domains for filtering
        self.product_categories = {
            'sunglasses', 'glasses', 'eyewear', 
            'thermos', 'bottle', 'flask', 'container',
            'mug', 'cup', 'tumbler', 'drinkware',
            'stole', 'scarf', 'wrap', 'shawl',
            'stand', 'holder', 'mount', 'dock'
        }
        
        # Words that indicate the product is likely not what we want
        self.exclusion_terms = {
            'case', 'cover', 'pouch', 'bag', 'sleeve',
            'charger', 'cable', 'adapter', 'power bank',
            'cleaner', 'wipes', 'cloth', 'kit', 'repair',
            't-shirt', 'shirt', 'clothing', 'apparel', 'wear',
            'keychain', 'accessory', 'decoration'
        }
        
    def preprocess_text(self, text):
        """Clean and standardize text for comparison"""
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Replace special characters with spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
        
    def is_same_category(self, target_name, scraped_name):
        """Check if two product names belong to the same category"""
        target = self.preprocess_text(target_name)
        scraped = self.preprocess_text(scraped_name)
        
        # Extract likely product categories from each name
        target_categories = set()
        scraped_categories = set()
        
        for category in self.product_categories:
            if category in target:
                target_categories.add(category)
            if category in scraped:
                scraped_categories.add(category)
                
        # If we have categories for both and they don't intersect, products are different
        if target_categories and scraped_categories and not target_categories.intersection(scraped_categories):
            return False
            
        # Check for exclusion terms that indicate different product types
        for term in self.exclusion_terms:
            if term not in target and term in scraped:
                return False
                
        return True
        
    def calculate_similarity(self, target_name, scraped_name):
        """Calculate similarity between target and scraped product names"""
        # First check if they belong to same category
        if not self.is_same_category(target_name, scraped_name):
            return 0.0
            
        # Preprocess names
        target = self.preprocess_text(target_name)
        scraped = self.preprocess_text(scraped_name)
        
        # If model is loaded, use semantic similarity
        if self.model_loaded:
            # Generate embeddings
            embeddings = self.model.encode([target, scraped])
            # Calculate cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
            return float(similarity)
        else:
            # Fallback to rule-based matching
            return self._fallback_similarity(target, scraped)
            
    def _fallback_similarity(self, target, scraped):
        """Fallback similarity calculation using rules when model isn't available"""
        # Convert to sets of words for comparison
        target_words = set(target.split())
        scraped_words = set(scraped.split())
        
        # Calculate Jaccard similarity (intersection over union)
        if not target_words or not scraped_words:
            return 0.0
            
        intersection = len(target_words.intersection(scraped_words))
        union = len(target_words.union(scraped_words))
        
        return intersection / union if union > 0 else 0.0
        
    def is_valid_match(self, target_name, scraped_name):
        """Determine if scraped_name is a valid match for target_name"""
        similarity = self.calculate_similarity(target_name, scraped_name)
        return similarity >= self.threshold, similarity 