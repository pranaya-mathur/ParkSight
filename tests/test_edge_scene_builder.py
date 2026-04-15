"""Edge scene pipeline without loading YOLO weights."""
from unittest.mock import MagicMock

from edge.scene_builder import SceneBuilder
from edge.slot_engine import SlotEngine


def test_scene_builder_mock_camera_and_inference(monkeypatch):
    mock_cv = MagicMock()
    mock_cv.run_inference.return_value = []
    monkeypatch.setattr("edge.scene_builder.CVInference", lambda *a, **kwargs: mock_cv)

    sb = SceneBuilder(
        camera_configs=[{"id": "CAM-TEST", "source": "MOCK"}],
        engine=SlotEngine(),
    )
    scenes = sb.build_scenes(reserved_slots=set())

    assert len(scenes) == 1
    assert scenes[0]["camera_id"] == "CAM-TEST"
    assert "slots" in scenes[0] and len(scenes[0]["slots"]) == 10
    assert "hazards" in scenes[0]
    assert "confidence" in scenes[0]
    mock_cv.run_inference.assert_called()
