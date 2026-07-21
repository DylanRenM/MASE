"""FeatureEncoder 单元测试。"""

import numpy as np
import pytest
from core.feature_encoder import FEATURE_FIELDS, FeatureEncoder, VECTOR_DIMENSION


class TestFeatureEncoder:
    """FeatureEncoder 测试套件。"""

    @pytest.fixture
    def encoder(self):
        return FeatureEncoder()

    @pytest.fixture
    def sample_features(self):
        return {
            "frontend_pages": 2,
            "backend_interfaces": 1,
            "db_change": "是",
            "external_dependency": "否",
            "async_processing": "否",
            "transaction_required": "否",
            "business_branches": 3,
            "permission_control": "是",
            "data_migration": "否",
            "cache_design": "否",
        }

    def test_encode_returns_10d_vector(self, encoder, sample_features):
        """encode 返回 (10,) 形状的 float32 向量。"""
        v = encoder.encode(sample_features)
        assert v.shape == (10,)
        assert v.dtype == np.float32

    def test_encode_batch_returns_Nx10_matrix(self, encoder, sample_features):
        """encode_batch 返回 (N, 10) 形状的矩阵。"""
        features_list = [sample_features] * 5
        m = encoder.encode_batch(features_list)
        assert m.shape == (5, 10)
        assert m.dtype == np.float32

    def test_all_values_in_range_0_1(self, encoder, sample_features):
        """所有编码值在 [0, 1] 范围内。"""
        v = encoder.encode(sample_features)
        assert np.all(v >= 0.0)
        assert np.all(v <= 1.0)

    def test_bool_feature_yes_is_1(self, encoder):
        """"是" 编码为 1.0。"""
        features = {
            "frontend_pages": 0, "backend_interfaces": 0,
            "db_change": "是",
            "external_dependency": "否", "async_processing": "否",
            "transaction_required": "否", "business_branches": 1,
            "permission_control": "否", "data_migration": "否",
            "cache_design": "否",
        }
        v = encoder.encode(features)
        assert v[2] == 1.0  # db_change 在索引2

    def test_bool_feature_no_is_0(self, encoder):
        """"否" 编码为 0.0。"""
        features = {
            "frontend_pages": 0, "backend_interfaces": 0,
            "db_change": "否",
            "external_dependency": "否", "async_processing": "否",
            "transaction_required": "否", "business_branches": 1,
            "permission_control": "否", "data_migration": "否",
            "cache_design": "否",
        }
        v = encoder.encode(features)
        assert v[2] == 0.0

    def test_frontend_pages_normalized(self, encoder):
        """前端页面数 3 编码为 1.0。"""
        features = {
            "frontend_pages": 3, "backend_interfaces": 0,
            "db_change": "否", "external_dependency": "否",
            "async_processing": "否", "transaction_required": "否",
            "business_branches": 1, "permission_control": "否",
            "data_migration": "否", "cache_design": "否",
        }
        v = encoder.encode(features)
        assert v[0] == 1.0

    def test_business_branches_1_is_0(self, encoder):
        """业务分支数1编码为0.0。"""
        features = {
            "frontend_pages": 0, "backend_interfaces": 0,
            "db_change": "否", "external_dependency": "否",
            "async_processing": "否", "transaction_required": "否",
            "business_branches": 1, "permission_control": "否",
            "data_migration": "否", "cache_design": "否",
        }
        v = encoder.encode(features)
        assert v[6] == 0.0

    def test_business_branches_5_is_1(self, encoder):
        """业务分支数5编码为1.0。"""
        features = {
            "frontend_pages": 0, "backend_interfaces": 0,
            "db_change": "否", "external_dependency": "否",
            "async_processing": "否", "transaction_required": "否",
            "business_branches": 5, "permission_control": "否",
            "data_migration": "否", "cache_design": "否",
        }
        v = encoder.encode(features)
        assert v[6] == 1.0

    def test_missing_field_raises(self, encoder):
        """缺少字段时抛出 ValueError。"""
        features = {"frontend_pages": 1}  # 不完整
        with pytest.raises(ValueError):
            encoder.encode(features)

    def test_vector_dimension_constant(self):
        """VECTOR_DIMENSION 等于 FEATURE_FIELDS 长度。"""
        assert VECTOR_DIMENSION == len(FEATURE_FIELDS)
        assert VECTOR_DIMENSION == 10
