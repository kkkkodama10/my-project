"""ランキング計算・CSV エクスポートのビジネスロジック。"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import HTTPException

from app.schemas.event import (
    EventSummary,
    LeaderboardEntry,
    ResultsResponse,
)
from app.store.base import BaseAnswerStore, BaseEventStore, BaseUserStore


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RankingService:
    def __init__(
        self,
        event_store: BaseEventStore,
        user_store: BaseUserStore,
        answer_store: BaseAnswerStore,
    ) -> None:
        self.event_store = event_store
        self.user_store = user_store
        self.answer_store = answer_store

    async def calculate(self, event_id: str) -> ResultsResponse:
        event = await self.event_store.get(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="event not found")

        qids = await self.event_store.get_question_ids(event_id)
        total_questions = len(qids)

        users = await self.user_store.list_event_users(event_id)
        answers = await self.answer_store.list_by_event(event_id)

        # 回答を (question_id, user_id) でインデックス化
        answer_map: dict[tuple[str, str], object] = {}
        for ans in answers:
            answer_map[(ans.question_id, ans.user_id)] = ans

        entries: list[LeaderboardEntry] = []
        for user in users:
            correct_count = 0
            unanswered_count = 0
            correct_time_sum = 0.0
            for qid in qids:
                ans = answer_map.get((qid, user.id))
                if ans is None:
                    unanswered_count += 1
                elif ans.is_correct and ans.accepted:
                    correct_count += 1
                    if ans.response_time_sec_1dp is not None:
                        correct_time_sum += ans.response_time_sec_1dp

            accuracy = correct_count / total_questions if total_questions > 0 else 0

            entries.append(
                LeaderboardEntry(
                    rank=0,  # 後で計算
                    user_id=user.id,
                    display_name=user.display_name,
                    correct_count=correct_count,
                    unanswered_count=unanswered_count,
                    accuracy=round(accuracy, 4),
                    correct_time_sum_sec_1dp=round(correct_time_sum, 1),
                ),
            )

        # ソート: 正解数 desc → 回答時間合計 asc
        entries.sort(
            key=lambda e: (-e.correct_count, e.correct_time_sum_sec_1dp),
        )

        # ランク付け（同着対応）
        for i, entry in enumerate(entries):
            if i == 0:
                entry.rank = 1
            else:
                prev = entries[i - 1]
                if (
                    entry.correct_count == prev.correct_count
                    and entry.correct_time_sum_sec_1dp
                    == prev.correct_time_sum_sec_1dp
                ):
                    entry.rank = prev.rank
                else:
                    entry.rank = i + 1

        finished_at = event.finished_at if event.finished_at else _iso_now()

        return ResultsResponse(
            leaderboard=entries,
            event_summary=EventSummary(
                total_questions=total_questions,
                finished_at=finished_at,
            ),
        )

    async def export_csv(self, event_id: str) -> str:
        """ランキングを CSV 文字列として返す。"""
        result = await self.calculate(event_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["順位", "表示名", "正解数", "未回答数", "正答率", "回答時間合計(秒)"])
        for e in result.leaderboard:
            writer.writerow([
                e.rank,
                e.display_name,
                e.correct_count,
                e.unanswered_count,
                f"{e.accuracy:.1%}",
                e.correct_time_sum_sec_1dp,
            ])

        return output.getvalue()
