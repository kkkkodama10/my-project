import os
import subprocess
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

KEYCHAIN_SERVICE = "auto-diary"
KEYCHAIN_ACCOUNT = "garmin"


@dataclass
class Config:
    garmin_email: str
    garmin_password: str
    anthropic_api_key: str
    target_date: str
    language: str


def _get_garmin_password_from_keychain() -> str | None:
    result = subprocess.run(
        ["security", "find-generic-password", "-a", KEYCHAIN_ACCOUNT, "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def load_config() -> Config:
    load_dotenv()

    missing = []
    garmin_email = os.getenv("GARMIN_EMAIL")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    # GARMIN_PASSWORD は .env → Keychain の順で取得
    garmin_password = os.getenv("GARMIN_PASSWORD") or _get_garmin_password_from_keychain()

    if not garmin_email:
        missing.append("GARMIN_EMAIL")
    if not garmin_password:
        print("ERROR: Garmin パスワードが見つかりません。")
        print("以下のいずれかで登録してください:")
        print(f'  Keychain: security add-generic-password -a "{KEYCHAIN_ACCOUNT}" -s "{KEYCHAIN_SERVICE}" -w "your_password"')
        print("  .env:     GARMIN_PASSWORD=your_password")
        sys.exit(1)
    if not anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        print(f"ERROR: 必須環境変数が未設定です: {', '.join(missing)}")
        print(".env.example をコピーして .env を作成し、認証情報を記入してください。")
        sys.exit(1)

    return Config(
        garmin_email=garmin_email,
        garmin_password=garmin_password,
        anthropic_api_key=anthropic_api_key,
        target_date=os.getenv("DIARY_TARGET_DATE", "yesterday"),
        language=os.getenv("DIARY_LANGUAGE", "ja"),
    )
