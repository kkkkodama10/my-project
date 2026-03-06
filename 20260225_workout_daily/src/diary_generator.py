import logging
import time
from pathlib import Path

import anthropic

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "diary_prompt.txt"
MODEL = "claude-haiku-4-5-20251001"
TEMPERATURE = 0.3
MAX_TOKENS = 500


class DiaryGenerator:
    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(self, health_data: dict) -> str:
        prompt = self._build_prompt(health_data)
        for attempt in range(2):
            try:
                message = self._client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}],
                )
                return message.content[0].text
            except Exception as e:
                if attempt == 0:
                    logger.warning(f"Claude API呼び出し失敗、リトライします: {e}")
                    time.sleep(1)
                else:
                    raise RuntimeError(f"Claude API呼び出し失敗（リトライ後）: {e}") from e

    def _build_prompt(self, health_data: dict) -> str:
        template = PROMPT_PATH.read_text(encoding="utf-8")
        lines = []
        date = health_data.get("date", "")
        if date:
            lines.append(f"日付: {date}")

        sleep = health_data.get("sleep")
        if sleep:
            lines.append(f"睡眠: 合計{sleep['total_hours']}時間"
                         + (f"（深い睡眠{sleep['deep_hours']}時間）" if sleep.get("deep_hours") else ""))

        steps = health_data.get("steps")
        if steps:
            lines.append(f"歩数: {steps['total']}歩")

        stress = health_data.get("stress")
        if stress:
            lines.append(f"ストレス平均: {stress['average']}")

        body_battery = health_data.get("body_battery")
        if body_battery:
            bb_line = f"ボディバッテリー: 睡眠回復+{body_battery['charged']}・消耗-{body_battery['drained']}"
            if body_battery.get("level"):
                bb_line += f"（現在レベル: {body_battery['level']}）"
            lines.append(bb_line)

        hrv = health_data.get("hrv")
        if hrv:
            hrv_line = f"HRV（自律神経）: 昨夜平均{hrv['last_night_avg']}"
            if hrv.get("status"):
                hrv_line += f"・状態{hrv['status']}"
            lines.append(hrv_line)

        return template.format(health_data="\n".join(lines))
