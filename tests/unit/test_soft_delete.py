from fastapi_query_filters.core import create_filter_model
from tests.schemas import (
    StargateArtifactCustomActiveOut,
    StargateArtifactDecommissionedOut,
    StargateArtifactDestroyedOut,
)


def test_soft_delete_config_fields() -> None:
    """Verify that filter model creation preserves soft delete configuration attributes."""
    # 1. Destroyed schema (is_destroyed: bool)
    model1 = create_filter_model(StargateArtifactDestroyedOut)
    config1 = getattr(model1, "_source_filter_config", None)
    assert config1 is not None
    assert getattr(config1, "soft_delete_field", None) == "is_destroyed"
    assert getattr(config1, "soft_delete_active_value", None) is None

    # 2. Decommissioned schema (decommissioned_at: datetime)
    model2 = create_filter_model(StargateArtifactDecommissionedOut)
    config2 = getattr(model2, "_source_filter_config", None)
    assert config2 is not None
    assert getattr(config2, "soft_delete_field", None) == "decommissioned_at"
    assert getattr(config2, "soft_delete_active_value", None) is None

    # 3. Custom active value schema
    model3 = create_filter_model(StargateArtifactCustomActiveOut)
    config3 = getattr(model3, "_source_filter_config", None)
    assert config3 is not None
    assert getattr(config3, "soft_delete_field", None) == "is_destroyed"
    assert getattr(config3, "soft_delete_active_value", None) is True
