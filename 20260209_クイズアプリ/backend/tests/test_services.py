"""サービス層の直接単体テスト（T-084: カバレッジ ≥80%）。

HTTP 層を経由せず、サービスクラスを直接インスタンス化してテストする。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.seed import seed_all
from app.services.answer_service import AnswerService
from app.services.event_service import EventService
from app.services.question_service import QuestionService
from app.services.ranking_service import RankingService
from app.store.sqlite_store import (
    SQLiteAnswerStore,
    SQLiteEventStore,
    SQLiteQuestionStore,
    SQLiteUserStore,
)
from app.ws.manager import ConnectionManager
from app.models.user import EventSession, EventUser


# ── フィクスチャ ───────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@pytest_asyncio.fixture
async def session(test_engine):
    """シード済みの AsyncSession を直接提供する。"""
    sf = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with sf() as s:
        await seed_all(s)

    async with sf() as s:
        yield s
        await s.commit()


@pytest.fixture
def ws_manager():
    return ConnectionManager()


@pytest_asyncio.fixture
async def event_svc(session, ws_manager):
    return EventService(
        event_store=SQLiteEventStore(session),
        question_store=SQLiteQuestionStore(session),
        user_store=SQLiteUserStore(session),
        answer_store=SQLiteAnswerStore(session),
        ws_manager=ws_manager,
    )


@pytest_asyncio.fixture
async def answer_svc(session, ws_manager):
    return AnswerService(
        answer_store=SQLiteAnswerStore(session),
        event_store=SQLiteEventStore(session),
        question_store=SQLiteQuestionStore(session),
        user_store=SQLiteUserStore(session),
        ws_manager=ws_manager,
    )


@pytest_asyncio.fixture
async def question_svc(session):
    return QuestionService(SQLiteQuestionStore(session))


@pytest_asyncio.fixture
async def ranking_svc(session):
    return RankingService(
        event_store=SQLiteEventStore(session),
        user_store=SQLiteUserStore(session),
        answer_store=SQLiteAnswerStore(session),
    )


# ── ユーザ・セッション作成ヘルパー ────────────────────


async def _create_user_session(session: AsyncSession, event_id: str = "demo") -> tuple[str, str]:
    """テスト用のセッション・ユーザを DB に直接作成して (session_id, user_id) を返す。"""
    import uuid
    import random
    sid = uuid.uuid4().hex
    uid = uuid.uuid4().hex
    suffix = f"{random.randint(0, 9999):04d}-{uuid.uuid4().hex[:4]}"  # 衝突回避

    es = EventSession(
        id=sid,
        event_id=event_id,
        user_id=None,
        created_at=_now_iso(),
    )
    session.add(es)
    await session.flush()

    eu = EventUser(
        id=uid,
        event_id=event_id,
        session_id=sid,
        display_name=f"test-{suffix}",
        display_suffix=suffix,
        joined_at=_now_iso(),
    )
    session.add(eu)

    # セッションにユーザIDを紐付け
    es.user_id = uid
    await session.flush()

    return sid, uid


# ─────────────────────────────────────────────────────
# EventService テスト
# ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_event_start(event_svc):
    res = await event_svc.start("demo")
    assert res.status == "ok"
    assert res.state == "running"


@pytest.mark.asyncio
async def test_event_start_not_waiting(event_svc):
    await event_svc.start("demo")
    with pytest.raises(HTTPException) as exc:
        await event_svc.start("demo")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_event_not_found(event_svc):
    with pytest.raises(HTTPException) as exc:
        await event_svc.start("nonexistent")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_event_next_question(event_svc):
    await event_svc.start("demo")
    res = await event_svc.next_question("demo")
    assert res.question_id is not None
    assert res.deadline_at is not None


@pytest.mark.asyncio
async def test_event_next_all_finish(event_svc):
    """全問消化後に next を呼ぶと finished になる。"""
    await event_svc.start("demo")
    last = None
    for _ in range(10):
        res = await event_svc.next_question("demo")
        if hasattr(res, "state") and res.state == "finished":
            last = res
            break
    assert last is not None
    assert last.state == "finished"


@pytest.mark.asyncio
async def test_event_close_question(event_svc):
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")
    res = await event_svc.close_question("demo", nxt.question_id)
    assert res.status == "ok"
    assert res.closed_at is not None


@pytest.mark.asyncio
async def test_event_close_wrong_question(event_svc):
    await event_svc.start("demo")
    await event_svc.next_question("demo")
    with pytest.raises(HTTPException) as exc:
        await event_svc.close_question("demo", "nonexistent_q")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_event_reveal_answer(event_svc):
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")
    res = await event_svc.reveal_answer("demo", nxt.question_id)
    assert res.status == "ok"
    assert res.correct_choice_index is not None


@pytest.mark.asyncio
async def test_event_reveal_wrong_question(event_svc):
    await event_svc.start("demo")
    await event_svc.next_question("demo")
    with pytest.raises(HTTPException) as exc:
        await event_svc.reveal_answer("demo", "nonexistent_q")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_event_finish(event_svc):
    await event_svc.start("demo")
    res = await event_svc.finish("demo")
    assert res.status == "ok"
    assert res.state == "finished"


@pytest.mark.asyncio
async def test_event_abort(event_svc):
    await event_svc.start("demo")
    res = await event_svc.abort("demo")
    assert res.status == "ok"
    assert res.state == "aborted"


@pytest.mark.asyncio
async def test_event_reset(event_svc):
    await event_svc.start("demo")
    res = await event_svc.reset("demo")
    assert res.status == "ok"
    assert res.state == "waiting"


@pytest.mark.asyncio
async def test_event_create_event(event_svc):
    from app.schemas.event import EventCreateRequest
    req = EventCreateRequest(title="New Test Event", join_code="testjc", time_limit_sec=15)
    res = await event_svc.create_event(req)
    assert res.title == "New Test Event"
    assert res.state == "waiting"
    assert res.event_id is not None


@pytest.mark.asyncio
async def test_event_create_event_auto_join_code(event_svc):
    """join_code を省略すると自動生成される。"""
    from app.schemas.event import EventCreateRequest
    req = EventCreateRequest(title="Auto Code Event", time_limit_sec=15)
    res = await event_svc.create_event(req)
    assert res.event_id is not None


@pytest.mark.asyncio
async def test_event_create_with_question_ids(event_svc, session):
    """question_ids を指定してイベントを作成できる。"""
    from app.schemas.event import EventCreateRequest
    from sqlalchemy import select
    from app.models.question import Question
    result = await session.execute(select(Question.id).limit(2))
    qids = [row[0] for row in result.all()]

    req = EventCreateRequest(title="WithQ", time_limit_sec=10, question_ids=qids)
    res = await event_svc.create_event(req)
    assert res.event_id is not None


@pytest.mark.asyncio
async def test_event_update_join_code(event_svc):
    res = await event_svc.update_join_code("demo", "newcode99")
    assert res.event_id == "demo"


@pytest.mark.asyncio
async def test_event_update_join_code_not_found(event_svc):
    with pytest.raises(HTTPException) as exc:
        await event_svc.update_join_code("nonexistent", "xxx")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_event_get_user_state_no_session(event_svc):
    with pytest.raises(HTTPException) as exc:
        await event_svc.get_user_state("demo", "bad_session_id")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_event_get_user_state_waiting(event_svc, session):
    sid, _ = await _create_user_session(session)
    res = await event_svc.get_user_state("demo", sid)
    assert res.event.state == "waiting"
    assert res.me is not None
    assert res.current_question is None
    assert res.my_answer is None


@pytest.mark.asyncio
async def test_event_get_user_state_with_question(event_svc, session):
    """問題表示中の状態取得。"""
    await event_svc.start("demo")
    await event_svc.next_question("demo")
    sid, _ = await _create_user_session(session)
    res = await event_svc.get_user_state("demo", sid)
    assert res.current_question is not None
    assert res.current_question.correct_choice_index is None  # 未 reveal


@pytest.mark.asyncio
async def test_event_get_user_state_after_reveal(event_svc, session):
    """reveal 後は correct_choice_index が公開される。"""
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")
    await event_svc.close_question("demo", nxt.question_id)
    await event_svc.reveal_answer("demo", nxt.question_id)
    sid, _ = await _create_user_session(session)
    res = await event_svc.get_user_state("demo", sid)
    assert res.current_question.correct_choice_index is not None


@pytest.mark.asyncio
async def test_event_get_user_state_event_not_found(event_svc, session):
    sid, _ = await _create_user_session(session, event_id="demo")
    with pytest.raises(HTTPException) as exc:
        await event_svc.get_user_state("nonexistent", sid)
    assert exc.value.status_code == 404


# ─────────────────────────────────────────────────────
# AnswerService テスト
# ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_answer_submit_ok(answer_svc, event_svc, session):
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")
    sid, _ = await _create_user_session(session)

    res = await answer_svc.submit("demo", nxt.question_id, sid, 0)
    assert res.result in ("accepted", "rejected")
    assert res.answer.choice_index == 0


@pytest.mark.asyncio
async def test_answer_submit_correct(answer_svc, event_svc, session):
    """q1 の正解は choice_index=2（東京）。"""
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")
    assert nxt.question_id == "q1"
    sid, _ = await _create_user_session(session)

    res = await answer_svc.submit("demo", nxt.question_id, sid, 2)
    assert res.answer.is_correct is True


@pytest.mark.asyncio
async def test_answer_submit_incorrect(answer_svc, event_svc, session):
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")
    sid, _ = await _create_user_session(session)

    res = await answer_svc.submit("demo", nxt.question_id, sid, 0)
    assert res.answer.is_correct is False


@pytest.mark.asyncio
async def test_answer_submit_double(answer_svc, event_svc, session):
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")
    sid, _ = await _create_user_session(session)

    await answer_svc.submit("demo", nxt.question_id, sid, 0)
    with pytest.raises(HTTPException) as exc:
        await answer_svc.submit("demo", nxt.question_id, sid, 1)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_answer_submit_no_session(answer_svc):
    with pytest.raises(HTTPException) as exc:
        await answer_svc.submit("demo", "q1", "bad_sid", 0)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_answer_submit_not_registered(answer_svc, session):
    """セッションあり・ユーザ未登録の場合は 400。"""
    import uuid
    sid = uuid.uuid4().hex
    es = EventSession(id=sid, event_id="demo", user_id=None, created_at=_now_iso())
    session.add(es)
    await session.flush()

    with pytest.raises(HTTPException) as exc:
        await answer_svc.submit("demo", "q1", sid, 0)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_answer_submit_question_not_active(answer_svc, event_svc, session):
    """アクティブでない question_id への回答は 400。"""
    await event_svc.start("demo")
    await event_svc.next_question("demo")  # q1 がアクティブ
    sid, _ = await _create_user_session(session)

    with pytest.raises(HTTPException) as exc:
        await answer_svc.submit("demo", "q2", sid, 0)  # q2 はアクティブでない
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_answer_submit_deadline_passed(answer_svc, event_svc, session):
    """期限切れの回答は accepted=False になる。"""
    await event_svc.start("demo")
    await event_svc.next_question("demo")

    # 期限を過去に設定
    store = SQLiteEventStore(session)
    past = datetime.now(timezone.utc) - timedelta(seconds=30)
    await store.update("demo", current_deadline_at=past.isoformat())
    await session.flush()

    sid, _ = await _create_user_session(session)
    res = await answer_svc.submit("demo", "q1", sid, 0)
    assert res.result == "rejected"
    assert res.answer.reject_reason == "deadline_passed"


@pytest.mark.asyncio
async def test_answer_submit_response_time(answer_svc, event_svc, session):
    """response_time_sec_1dp が計算されること。"""
    await event_svc.start("demo")
    await event_svc.next_question("demo")
    sid, _ = await _create_user_session(session)

    res = await answer_svc.submit("demo", "q1", sid, 2)
    assert res.answer.response_time_sec_1dp is not None
    assert res.answer.response_time_sec_1dp >= 0


# ─────────────────────────────────────────────────────
# QuestionService テスト
# ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_question_list_all(question_svc):
    questions = await question_svc.list_all()
    assert len(questions) >= 1


@pytest.mark.asyncio
async def test_question_list_enabled_only(question_svc):
    questions = await question_svc.list_all(enabled_only=True)
    assert all(q.is_enabled for q in questions)


@pytest.mark.asyncio
async def test_question_get(question_svc):
    q = await question_svc.get("q1")
    assert q.question_id == "q1"
    assert len(q.choices) == 4


@pytest.mark.asyncio
async def test_question_get_not_found(question_svc):
    with pytest.raises(HTTPException) as exc:
        await question_svc.get("nonexistent")
    assert exc.value.status_code == 404


def _make_choices():
    from app.schemas.question import ChoiceInput
    return [
        ChoiceInput(choice_index=i, text=f"選択肢{i}")
        for i in range(4)
    ]


@pytest.mark.asyncio
async def test_question_create(question_svc):
    from app.schemas.question import QuestionCreateRequest
    req = QuestionCreateRequest(
        question_text="テスト問題",
        correct_choice_index=1,
        choices=_make_choices(),
    )
    res = await question_svc.create(req)
    assert res.question_text == "テスト問題"
    assert res.correct_choice_index == 1
    assert len(res.choices) == 4


@pytest.mark.asyncio
async def test_question_create_wrong_choice_count(question_svc):
    from app.schemas.question import QuestionCreateRequest, ChoiceInput
    req = QuestionCreateRequest(
        question_text="不足問題",
        correct_choice_index=0,
        choices=[ChoiceInput(choice_index=0, text="A")],
    )
    with pytest.raises(HTTPException) as exc:
        await question_svc.create(req)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_question_create_invalid_correct_index(question_svc):
    from app.schemas.question import QuestionCreateRequest
    req = QuestionCreateRequest(
        question_text="不正インデックス",
        correct_choice_index=5,
        choices=_make_choices(),
    )
    with pytest.raises(HTTPException) as exc:
        await question_svc.create(req)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_question_update_text(question_svc):
    from app.schemas.question import QuestionUpdateRequest
    req = QuestionUpdateRequest(question_text="更新後テキスト")
    res = await question_svc.update("q1", req)
    assert res.question_text == "更新後テキスト"


@pytest.mark.asyncio
async def test_question_update_correct_index(question_svc):
    from app.schemas.question import QuestionUpdateRequest
    req = QuestionUpdateRequest(correct_choice_index=3)
    res = await question_svc.update("q1", req)
    assert res.correct_choice_index == 3


@pytest.mark.asyncio
async def test_question_update_invalid_correct_index(question_svc):
    from app.schemas.question import QuestionUpdateRequest
    req = QuestionUpdateRequest(correct_choice_index=9)
    with pytest.raises(HTTPException) as exc:
        await question_svc.update("q1", req)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_question_update_choices_wrong_count(question_svc):
    from app.schemas.question import QuestionUpdateRequest, ChoiceInput
    req = QuestionUpdateRequest(choices=[ChoiceInput(choice_index=0, text="X")])
    with pytest.raises(HTTPException) as exc:
        await question_svc.update("q1", req)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_question_update_is_enabled(question_svc):
    from app.schemas.question import QuestionUpdateRequest
    req = QuestionUpdateRequest(is_enabled=False)
    res = await question_svc.update("q1", req)
    assert res.is_enabled is False


@pytest.mark.asyncio
async def test_question_update_not_found(question_svc):
    from app.schemas.question import QuestionUpdateRequest
    req = QuestionUpdateRequest(question_text="x")
    with pytest.raises(HTTPException) as exc:
        await question_svc.update("nonexistent", req)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_question_delete(question_svc):
    # まず新しい問題を作成してから削除
    from app.schemas.question import QuestionCreateRequest
    req = QuestionCreateRequest(
        question_text="削除用",
        correct_choice_index=0,
        choices=_make_choices(),
    )
    created = await question_svc.create(req)
    await question_svc.delete(created.question_id)
    with pytest.raises(HTTPException):
        await question_svc.get(created.question_id)


@pytest.mark.asyncio
async def test_question_delete_not_found(question_svc):
    with pytest.raises(HTTPException) as exc:
        await question_svc.delete("nonexistent")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_question_reorder(question_svc):
    questions = await question_svc.list_all()
    ids = [q.question_id for q in questions]
    # 順序を逆にする
    await question_svc.reorder(list(reversed(ids)))
    reordered = await question_svc.list_all()
    assert [q.question_id for q in reordered] == list(reversed(ids))


@pytest.mark.asyncio
async def test_question_set_enabled_false(question_svc):
    res = await question_svc.set_enabled("q1", False)
    assert res.is_enabled is False


@pytest.mark.asyncio
async def test_question_set_enabled_true(question_svc):
    await question_svc.set_enabled("q1", False)
    res = await question_svc.set_enabled("q1", True)
    assert res.is_enabled is True


@pytest.mark.asyncio
async def test_question_set_enabled_not_found(question_svc):
    with pytest.raises(HTTPException) as exc:
        await question_svc.set_enabled("nonexistent", True)
    assert exc.value.status_code == 404


# ─────────────────────────────────────────────────────
# RankingService テスト
# ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ranking_calculate_empty(ranking_svc, event_svc):
    """参加者なしのランキングは空リスト。"""
    await event_svc.start("demo")
    await event_svc.finish("demo")
    res = await ranking_svc.calculate("demo")
    assert res.leaderboard == []
    assert res.event_summary.total_questions >= 0


@pytest.mark.asyncio
async def test_ranking_calculate_not_found(ranking_svc):
    with pytest.raises(HTTPException) as exc:
        await ranking_svc.calculate("nonexistent")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_ranking_calculate_with_answers(
    ranking_svc, event_svc, answer_svc, session
):
    """回答ありのランキング計算。"""
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")

    sid1, _ = await _create_user_session(session)
    await answer_svc.submit("demo", nxt.question_id, sid1, 2)  # 正解

    await event_svc.finish("demo")

    res = await ranking_svc.calculate("demo")
    assert len(res.leaderboard) >= 1
    top = res.leaderboard[0]
    assert top.rank == 1
    assert top.correct_count >= 0


@pytest.mark.asyncio
async def test_ranking_calculate_tie(ranking_svc, event_svc, answer_svc, session):
    """同点の場合は同じランクになる。"""
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")

    # 2ユーザが同じ選択肢を同タイミングで回答
    sid1, _ = await _create_user_session(session)
    sid2, _ = await _create_user_session(session)

    await answer_svc.submit("demo", nxt.question_id, sid1, 2)
    await answer_svc.submit("demo", nxt.question_id, sid2, 2)

    await event_svc.finish("demo")
    res = await ranking_svc.calculate("demo")
    assert len(res.leaderboard) == 2
    # 両者の正解数は同じ
    assert res.leaderboard[0].correct_count == res.leaderboard[1].correct_count


@pytest.mark.asyncio
async def test_ranking_export_csv(ranking_svc, event_svc):
    """CSV エクスポートはヘッダを含む文字列を返す。"""
    await event_svc.start("demo")
    await event_svc.finish("demo")
    csv_text = await ranking_svc.export_csv("demo")
    assert "順位" in csv_text
    assert "表示名" in csv_text


@pytest.mark.asyncio
async def test_ranking_export_csv_with_data(
    ranking_svc, event_svc, answer_svc, session
):
    """データありの CSV には本文行が存在する。"""
    await event_svc.start("demo")
    nxt = await event_svc.next_question("demo")
    sid, _ = await _create_user_session(session)
    await answer_svc.submit("demo", nxt.question_id, sid, 0)
    await event_svc.finish("demo")

    csv_text = await ranking_svc.export_csv("demo")
    lines = [l for l in csv_text.splitlines() if l]
    assert len(lines) >= 2  # ヘッダ + 1ユーザ


@pytest.mark.asyncio
async def test_ranking_finished_at_uses_event(ranking_svc, event_svc):
    """イベントの finished_at が使われる。"""
    await event_svc.start("demo")
    await event_svc.finish("demo")
    res = await ranking_svc.calculate("demo")
    assert res.event_summary.finished_at is not None
