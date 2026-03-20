from fastapi.testclient import TestClient

from main import app
from events.handlers.init_handler import InitEventHandler

client = TestClient(app)


def _build_init_request() -> dict:
    return {
        "event": {"type": "init"},
        "session": {
            "session_id": "sess_test_001",
            "player_count": 1,
            "difficulty": "NORMAL",
        },
        "time": {
            "hard_limit_seconds": 300,
            "elapsed_active_seconds": 0,
            "remaining_seconds": 300,
        },
        "seed": {
            "run_seed": "run_test_001",
        },
        "constraints": {
            "language": "zh",
            "content_rating": "PG",
            "max_chars_scene": 220,
            "max_chars_option": 14,
            "forbidden_terms": ["骰子", "扑克", "点数", "规则"],
        },
        "slots": {
            "tone_bias": "温柔诡秘",
            "theme_bias": "时间",
            "npc_bias": "守门人",
        },
        "client_context": {
            "platform": "web",
            "locale": "zh-CN",
        },
        "payload": {},
        "context": {},
    }


def _valid_init_output_json() -> str:
    return """
{
  "event": { "type": "init" },
  "ai_state": {
    "world_seed": "run_test_001_time_gatekeeper",
    "title": "时之沙漏的守门人",
    "tone": "温柔诡秘",
    "memory_summary": "玩家在时间停滞的庭院中醒来，面对一位知晓时间秘密的守门人。",
    "arc_progress": 0
  },
  "payload": {
    "mainline": {
      "premise": "时间之沙从沙漏中意外泄露，导致世界的时间流速变得混乱。",
      "player_role": "被时间乱流卷入此地的迷失者",
      "primary_goal": "修复破损的时之沙漏，让时间恢复流动",
      "stakes": "若失败，你将永远困在时间的缝隙中，逐渐被遗忘。"
    },
    "opening": {
      "scene": "你在一座悬浮于星海中的寂静庭院醒来。",
      "npc_line": "沙漏的裂痕正在扩大。"
    },
    "start_hint": {
      "how_to_play_next": "选择一个选项，决定你如何回应守门人。"
    },
    "options": [
      { "id": 1, "text": "询问沙漏位置" },
      { "id": 2, "text": "触碰凝固水珠" },
      { "id": 3, "text": "观察守门人" }
    ]
  },
  "routing": {
    "next_event_type": "DECISION",
    "should_end": false
  },
  "meta": {
    "trace_id": "init_run_test_001_1721234567890"
  }
}
""".strip()


def test_init_success(monkeypatch):
    def fake_complete_prompt(self, prompt: str, **kwargs) -> str:
        return _valid_init_output_json()

    monkeypatch.setattr(
        "services.ai.deepseek_client.DeepSeekProvider.complete_prompt",
        fake_complete_prompt,
    )

    response = client.post("/invoke", json=_build_init_request())
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 0
    assert body["data"]["event"]["type"] == "init"

    payload = body["data"]["payload"]
    assert payload["ai_state"]["arc_progress"] == 0
    assert 2 <= len(payload["options"]) <= 4
    assert payload["routing"]["next_event_type"] == "DECISION"
    assert payload["routing"]["should_end"] is False


def test_init_missing_required_field():
    bad_request = _build_init_request()
    bad_request.pop("session")

    response = client.post("/invoke", json=bad_request)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 1
    assert "session" in body["message"]


def test_init_non_json_model_output(monkeypatch):
    def fake_complete_prompt(self, prompt: str, **kwargs) -> str:
        return "hello world"

    monkeypatch.setattr(
        "services.ai.deepseek_client.DeepSeekProvider.complete_prompt",
        fake_complete_prompt,
    )

    response = client.post("/invoke", json=_build_init_request())
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 1
    assert "No JSON object found" in body["message"]


def test_init_invalid_options_length(monkeypatch):
    def fake_complete_prompt(self, prompt: str, **kwargs) -> str:
        return """
{
  "event": { "type": "init" },
  "ai_state": {
    "world_seed": "a",
    "title": "b",
    "tone": "c",
    "memory_summary": "d",
    "arc_progress": 0
  },
  "payload": {
    "mainline": {
      "premise": "a",
      "player_role": "b",
      "primary_goal": "c",
      "stakes": "d"
    },
    "opening": {
      "scene": "a",
      "npc_line": "b"
    },
    "start_hint": {
      "how_to_play_next": "c"
    },
    "options": [
      { "id": 1, "text": "只有一个选项" }
    ]
  },
  "routing": {
    "next_event_type": "DECISION",
    "should_end": false
  },
  "meta": {
    "trace_id": "t1"
  }
}
""".strip()

    monkeypatch.setattr(
        "services.ai.deepseek_client.DeepSeekProvider.complete_prompt",
        fake_complete_prompt,
    )

    response = client.post("/invoke", json=_build_init_request())
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 1
    assert "options length must be between 2 and 4" in body["message"]


def test_init_invalid_next_event_type(monkeypatch):
    def fake_complete_prompt(self, prompt: str, **kwargs) -> str:
        return """
{
  "event": { "type": "init" },
  "ai_state": {
    "world_seed": "a",
    "title": "b",
    "tone": "c",
    "memory_summary": "d",
    "arc_progress": 0
  },
  "payload": {
    "mainline": {
      "premise": "a",
      "player_role": "b",
      "primary_goal": "c",
      "stakes": "d"
    },
    "opening": {
      "scene": "a",
      "npc_line": "b"
    },
    "start_hint": {
      "how_to_play_next": "c"
    },
    "options": [
      { "id": 1, "text": "选项一" },
      { "id": 2, "text": "选项二" }
    ]
  },
  "routing": {
    "next_event_type": "HELLO",
    "should_end": false
  },
  "meta": {
    "trace_id": "t1"
  }
}
""".strip()

    monkeypatch.setattr(
        "services.ai.deepseek_client.DeepSeekProvider.complete_prompt",
        fake_complete_prompt,
    )

    response = client.post("/invoke", json=_build_init_request())
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 1
    assert "next_event_type" in body["message"]


def test_init_state_saved(monkeypatch):
    InitEventHandler._state_repo._store.clear()

    def fake_complete_prompt(self, prompt: str, **kwargs) -> str:
        return _valid_init_output_json()

    monkeypatch.setattr(
        "services.ai.deepseek_client.DeepSeekProvider.complete_prompt",
        fake_complete_prompt,
    )

    req = _build_init_request()
    session_id = req["session"]["session_id"]

    response = client.post("/invoke", json=req)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 0

    snapshot = InitEventHandler._state_repo.get_snapshot(session_id)
    assert snapshot is not None
    assert snapshot["session_id"] == session_id
    assert snapshot["event_type"] == "init"
    assert "ai_state" in snapshot
    assert "last_output" in snapshot
    assert snapshot["ai_state"]["arc_progress"] == 0