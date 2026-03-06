import logging
import sys
from datetime import date, timedelta

from config import load_config
from garmin_client import GarminClient
from diary_generator import DiaryGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def resolve_target_date(target: str) -> str:
    if target == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    if target == "today":
        return date.today().isoformat()
    return target


def main():
    config = load_config()
    target_date = resolve_target_date(config.target_date)
    logger.info(f"対象日付: {target_date}")

    logger.info("Garminデータ取得中...")
    client = GarminClient(config.garmin_email, config.garmin_password)
    health_data = client.get_daily_health_data(target_date)

    all_keys = ("sleep", "steps", "stress", "body_battery", "hrv")
    obtained = [k for k in all_keys if health_data[k] is not None]
    missing = [k for k in all_keys if health_data[k] is None]
    logger.info(f"取得成功: {obtained}")
    if missing:
        logger.warning(f"取得失敗（スキップ）: {missing}")

    if not obtained:
        logger.error("全データ取得失敗。日記を生成できません。")
        sys.exit(1)

    logger.info("日記生成中...")
    generator = DiaryGenerator(config.anthropic_api_key)
    diary_text = generator.generate(health_data)

    logger.info(f"生成完了（{len(diary_text)}文字）")
    print("\n--- 健康日記 ---")
    print(diary_text)
    print("----------------")


if __name__ == "__main__":
    main()
