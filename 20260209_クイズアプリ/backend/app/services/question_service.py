"""問題 CRUD のビジネスロジック。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.models.question import Question, QuestionChoice
from app.schemas.question import (
    ChoiceResponse,
    QuestionCreateRequest,
    QuestionResponse,
    QuestionUpdateRequest,
)
from app.store.base import BaseQuestionStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_response(q: Question) -> QuestionResponse:
    return QuestionResponse(
        question_id=q.id,
        question_text=q.question_text,
        question_image=q.question_image_path,
        choices=[
            ChoiceResponse(
                choice_index=c.choice_index,
                text=c.text,
                image=c.image_path,
            )
            for c in q.choices
        ],
        correct_choice_index=q.correct_choice_index,
        is_enabled=q.is_enabled,
        sort_order=q.sort_order,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )


class QuestionService:
    def __init__(self, question_store: BaseQuestionStore) -> None:
        self.store = question_store

    async def list_all(self, *, enabled_only: bool = False) -> list[QuestionResponse]:
        questions = await self.store.list(enabled_only=enabled_only)
        return [_to_response(q) for q in questions]

    async def get(self, question_id: str) -> QuestionResponse:
        q = await self.store.get(question_id)
        if not q:
            raise HTTPException(status_code=404, detail="question not found")
        return _to_response(q)

    async def create(self, req: QuestionCreateRequest) -> QuestionResponse:
        if len(req.choices) != 4:
            raise HTTPException(status_code=400, detail="exactly 4 choices required")
        if req.correct_choice_index not in range(4):
            raise HTTPException(
                status_code=400,
                detail="correct_choice_index must be 0-3",
            )

        now = _now_iso()
        qid = uuid.uuid4().hex

        question = Question(
            id=qid,
            question_text=req.question_text,
            question_image_path=req.question_image,
            correct_choice_index=req.correct_choice_index,
            is_enabled=req.is_enabled,
            sort_order=0,
            created_at=now,
            updated_at=now,
        )
        for c in req.choices:
            question.choices.append(
                QuestionChoice(
                    id=uuid.uuid4().hex,
                    question_id=qid,
                    choice_index=c.choice_index,
                    text=c.text,
                    image_path=c.image,
                ),
            )

        await self.store.create(question)
        return _to_response(question)

    async def update(
        self,
        question_id: str,
        req: QuestionUpdateRequest,
    ) -> QuestionResponse:
        q = await self.store.get(question_id)
        if not q:
            raise HTTPException(status_code=404, detail="question not found")

        updates: dict = {}
        if req.question_text is not None:
            updates["question_text"] = req.question_text
        if req.question_image is not None:
            updates["question_image_path"] = req.question_image
        if req.correct_choice_index is not None:
            if req.correct_choice_index not in range(4):
                raise HTTPException(
                    status_code=400,
                    detail="correct_choice_index must be 0-3",
                )
            updates["correct_choice_index"] = req.correct_choice_index
        if req.is_enabled is not None:
            updates["is_enabled"] = req.is_enabled

        if updates:
            updates["updated_at"] = _now_iso()
            await self.store.update(question_id, **updates)

        # 選択肢の更新（全置換）
        if req.choices is not None:
            if len(req.choices) != 4:
                raise HTTPException(
                    status_code=400,
                    detail="exactly 4 choices required",
                )
            q = await self.store.get(question_id)
            # 既存の選択肢を削除して再作成
            q.choices.clear()
            for c in req.choices:
                q.choices.append(
                    QuestionChoice(
                        id=uuid.uuid4().hex,
                        question_id=question_id,
                        choice_index=c.choice_index,
                        text=c.text,
                        image_path=c.image,
                    ),
                )

        q = await self.store.get(question_id)
        return _to_response(q)

    async def delete(self, question_id: str) -> None:
        deleted = await self.store.delete(question_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="question not found")

    async def reorder(self, ordered_ids: list[str]) -> None:
        await self.store.reorder(ordered_ids)

    async def set_enabled(self, question_id: str, enabled: bool) -> QuestionResponse:
        q = await self.store.set_enabled(question_id, enabled)
        if not q:
            raise HTTPException(status_code=404, detail="question not found")
        return _to_response(q)
