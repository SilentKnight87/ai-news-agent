"""
Unit tests for embeddings service.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestEmbeddingsService:
    """Test cases for EmbeddingsService."""

    @patch('src.services.embeddings.get_settings')
    @patch('src.services.embeddings.SentenceTransformer')
    def test_normalize_embedding(self, mock_transformer, mock_settings):
        """Test embedding normalization."""
        # Mock settings to avoid requiring environment variables
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.embeddings_model = "test-model"
        
        # Mock transformer
        mock_transformer.return_value = MagicMock()
        
        from src.services.embeddings import EmbeddingsService
        service = EmbeddingsService()
        
        # Test normal vector normalization
        embedding = np.array([3.0, 4.0])  # Length 5
        normalized = service._normalize_embedding(embedding)
        
        # Should be unit vector
        assert abs(np.linalg.norm(normalized) - 1.0) < 1e-6
        assert abs(normalized[0] - 0.6) < 1e-6  # 3/5
        assert abs(normalized[1] - 0.8) < 1e-6  # 4/5

    @patch('src.services.embeddings.get_settings')
    @patch('src.services.embeddings.SentenceTransformer')
    def test_normalize_zero_embedding(self, mock_transformer, mock_settings):
        """Test normalization of zero vector."""
        # Mock settings to avoid requiring environment variables
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.embeddings_model = "test-model"
        
        # Mock transformer
        mock_transformer.return_value = MagicMock()
        
        from src.services.embeddings import EmbeddingsService
        service = EmbeddingsService()
        
        zero_embedding = np.array([0.0, 0.0])
        normalized = service._normalize_embedding(zero_embedding)
        
        # Zero vector should remain zero
        assert np.allclose(normalized, [0.0, 0.0])

    @patch('src.services.embeddings.get_settings')
    @patch('src.services.embeddings.SentenceTransformer')
    def test_cosine_similarity(self, mock_transformer, mock_settings):
        """Test cosine similarity calculation."""
        # Mock settings to avoid requiring environment variables
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.embeddings_model = "test-model"
        
        # Mock transformer
        mock_transformer.return_value = MagicMock()
        
        from src.services.embeddings import EmbeddingsService
        service = EmbeddingsService()
        
        # Identical vectors should have similarity 1.0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = service.cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 1e-6

    @patch('src.services.embeddings.get_settings')
    @patch('src.services.embeddings.SentenceTransformer')
    def test_cosine_similarity_orthogonal(self, mock_transformer, mock_settings):
        """Test cosine similarity of orthogonal vectors."""
        # Mock settings to avoid requiring environment variables
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.embeddings_model = "test-model"
        
        # Mock transformer
        mock_transformer.return_value = MagicMock()
        
        from src.services.embeddings import EmbeddingsService
        service = EmbeddingsService()
        
        # Orthogonal vectors should have similarity 0.0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = service.cosine_similarity(vec1, vec2)
        assert abs(similarity) < 1e-6

    @patch('src.services.embeddings.get_settings')
    @patch('src.services.embeddings.SentenceTransformer')
    def test_cache_size(self, mock_transformer, mock_settings):
        """Test cache size reporting."""
        # Mock settings to avoid requiring environment variables
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.embeddings_model = "test-model"
        
        # Mock transformer
        mock_transformer.return_value = MagicMock()
        
        from src.services.embeddings import EmbeddingsService
        service = EmbeddingsService()
        
        # Initially should be 0
        assert service.get_cache_size() == 0

    @patch('src.services.embeddings.get_settings')
    @patch('src.services.embeddings.SentenceTransformer')
    def test_model_info(self, mock_transformer, mock_settings):
        """Test model information retrieval."""
        # Mock settings to avoid requiring environment variables
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.embeddings_model = "test-model"
        
        # Mock transformer
        mock_transformer.return_value = MagicMock()
        
        from src.services.embeddings import EmbeddingsService
        service = EmbeddingsService()
        
        info = service.get_model_info()
        assert "embedding_dimension" in info
        assert info["embedding_dimension"] == 384
        assert "model_loaded" in info