from prompts.init_prompt import render_init_prompt
from schemas.init import (
    InitClientContext,
    InitConstraints,
    InitContext,
    InitPayload,
    InitRequest,
    InitSeed,
    InitSession,
    InitSlots,
    InitTime,
)
from schemas.invoke import EventInfo
from events.types import EventType


def _build_init_request() -> InitRequest:
    return InitRequest(
        event=EventInfo(type=EventType.INIT),
        session=InitSession(
            session_id="sess_test_001",
            player_count=1,
            difficulty="NORMAL",
        ),
        time=InitTime(
            hard_limit_seconds=300,
            elapsed_active_seconds=0,
            remaining_seconds=300,
        ),
        seed=InitSeed(
            run_seed="run_test_001",
        ),
        constraints=InitConstraints(
            language="zh",
            content_rating="PG",
            max_chars_scene=220,
            max_chars_option=14,
            forbidden_terms=["骰子", "扑克"],
        ),
        slots=InitSlots(
            tone_bias="温柔诡秘",
            theme_bias="时间",
            npc_bias="守门人",
        ),
        client_context=InitClientContext(
            platform="web",
            locale="zh-CN",
        ),
        payload=InitPayload(),
        context=InitContext(),
    )


def test_render_init_prompt_basic():
    request = _build_init_request()
    prompt = render_init_prompt(request)

    assert isinstance(prompt, str)
    assert "run_test_001" in prompt
    assert "NORMAL" in prompt
    assert "zh" in prompt
    assert "温柔诡秘" in prompt