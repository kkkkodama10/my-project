import logging
from datetime import date

from garminconnect import Garmin

logger = logging.getLogger(__name__)


class GarminClient:
    def __init__(self, email: str, password: str):
        self._api = Garmin(email=email, password=password)
        self._api.login()

    def get_daily_health_data(self, target_date: str) -> dict:
        return {
            "date": target_date,
            "sleep": self._get_sleep(target_date),
            "steps": self._get_steps(target_date),
            "stress": self._get_stress(target_date),
            "body_battery": self._get_body_battery(target_date),
            "hrv": self._get_hrv(target_date),
        }

    def _get_sleep(self, target_date: str) -> dict | None:
        try:
            raw = self._api.get_sleep_data(target_date)
            daily = raw.get("dailySleepDTO", {})
            total_seconds = daily.get("sleepTimeSeconds")
            deep_seconds = daily.get("deepSleepSeconds")
            light_seconds = daily.get("lightSleepSeconds")
            rem_seconds = daily.get("remSleepSeconds")
            if total_seconds is None:
                return None
            return {
                "total_hours": round(total_seconds / 3600, 1),
                "deep_hours": round(deep_seconds / 3600, 1) if deep_seconds else None,
                "light_hours": round(light_seconds / 3600, 1) if light_seconds else None,
                "rem_hours": round(rem_seconds / 3600, 1) if rem_seconds else None,
            }
        except Exception as e:
            logger.warning(f"睡眠データ取得失敗: {e}")
            return None

    def _get_steps(self, target_date: str) -> dict | None:
        try:
            raw = self._api.get_steps_data(target_date)
            total = sum(entry.get("steps", 0) for entry in raw if isinstance(entry, dict))
            if total == 0:
                return None
            return {"total": total}
        except Exception as e:
            logger.warning(f"歩数データ取得失敗: {e}")
            return None

    def _get_stress(self, target_date: str) -> dict | None:
        try:
            raw = self._api.get_stress_data(target_date)
            avg = raw.get("avgStressLevel")
            if avg is None or avg < 0:
                return None
            return {"average": avg}
        except Exception as e:
            logger.warning(f"ストレスデータ取得失敗: {e}")
            return None

    def _get_body_battery(self, target_date: str) -> dict | None:
        try:
            entries = self._api.get_body_battery(target_date, target_date)
            entry = next((e for e in entries if e.get("date") == target_date), None)
            if not entry:
                return None
            charged = entry.get("charged")
            drained = entry.get("drained")
            level = (entry.get("bodyBatteryDynamicFeedbackEvent") or {}).get("bodyBatteryLevel")
            if charged is None and drained is None:
                return None
            return {
                "charged": charged,
                "drained": drained,
                "level": level,
            }
        except Exception as e:
            logger.warning(f"ボディバッテリーデータ取得失敗: {e}")
            return None

    def _get_hrv(self, target_date: str) -> dict | None:
        try:
            raw = self._api.get_hrv_data(target_date)
            summary = raw.get("hrvSummary", {})
            last_night_avg = summary.get("lastNightAvg")
            status = summary.get("status")
            if last_night_avg is None:
                return None
            return {
                "last_night_avg": last_night_avg,
                "status": status,
            }
        except Exception as e:
            logger.warning(f"HRVデータ取得失敗: {e}")
            return None
