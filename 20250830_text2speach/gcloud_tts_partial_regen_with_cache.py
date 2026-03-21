from google.cloud import texttospeech
import os, re, html, json, pathlib, datetime, sys, hashlib, shutil

MAX_BYTES = 4800  # 5000バイト未満で余裕をもたせる
VOICE_NAME = "ja-JP-Standard-C"
LANG = "ja-JP"
OUTPUT_BASE = "/Users/kodamakeita/Pictures/音源素材"
CACHE_DIR = os.path.join(OUTPUT_BASE, ".cache")  # 共有キャッシュ（発話ごとに使い回し）


# ---- SSMLユーティリティ -------------------------------------------------

def is_ssml(s: str) -> bool:
    return "<speak" in s and "</speak>" in s


def rebuild_speak(content: str) -> str:
    return f"<speak>{content}</speak>"


def strip_speak_wrappers(ssml: str) -> str:
    m = re.search(r"<speak[^>]*>(.*)</speak>", ssml, flags=re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ssml


def wrap_plain_as_ssml(text: str) -> str:
    """プレーンテキストを最低限のSSMLに変換（段落=空行区切り）。"""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    ssml_paras = [f"<p>{html.escape(p)}</p>" for p in paras]
    return rebuild_speak("\n".join(ssml_paras)) if ssml_paras else rebuild_speak(html.escape(text.strip()))


def split_by_bytes(s: str, limit=MAX_BYTES):
    """最終非常手段（句読点等で既に細分化している前提）。"""
    chunks, buf, size = [], [], 0
    for ch in s:
        b = ch.encode("utf-8")
        if size + len(b) > limit and buf:
            chunks.append("".join(buf))
            buf, size = [ch], len(b)
        else:
            buf.append(ch); size += len(b)
    if buf: chunks.append("".join(buf))
    return chunks


def normalize_for_hash(ssml: str) -> str:
    """ハッシュ用に、タグ間空白など無意味な差分を吸収。テキスト内部は極力いじらない。"""
    body = ssml.strip()
    # タグ間の余分な空白を縮約
    body = re.sub(r">\s+<", "><", body)
    # 先頭/末尾の空白
    body = re.sub(r"^\s+|\s+$", "", body)
    return body


# ---- 安定チャンク化（<s>を原子単位とする） ------------------------------

def _split_sentence_tag_if_too_long(s_tag: str, limit=MAX_BYTES):
    """
    <s>…</s> が大き過ぎる場合のみ、句読点で細分化して複数の <s> に置換。
    できるだけ境界が変わらないよう、普段は1文=1チャンクを維持。
    """
    if len(rebuild_speak(f"<p>{s_tag}</p>").encode("utf-8")) <= limit:
        return [s_tag]
    m = re.search(r"<s([^>]*)>(.*)</s>", s_tag, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        return [s_tag]
    attrs, inner = m.group(1), m.group(2)
    # 句点・疑問符・感嘆符で分割（終端保持）
    units = re.split(r"(?<=[。！？\?])", inner)
    out = []
    buf = ""
    for u in [u for u in units if u and u.strip()]:
        cand = f"<s{attrs}>{buf + u}</s>"
        if len(rebuild_speak(f"<p>{cand}</p>").encode("utf-8")) <= limit:
            buf += u
            continue
        if buf.strip():
            out.append(f"<s{attrs}>{buf}</s>"); buf = ""
        # それでも大きい場合はバイト分割
        for bc in split_by_bytes(u, limit - 64):  # マージン
            out.append(f"<s{attrs}>{bc}</s>")
    if buf.strip():
        out.append(f"<s{attrs}>{buf}</s>")
    return out


def split_ssml_atomic_by_sentence(ssml_text: str, limit=MAX_BYTES):
    """
    1文(<s>…</s>)を“原子”として分割。文に続く <break/> は同一チャンクに吸着。
    各チャンクは <speak><p>…</p></speak> に包んで返す。
    こうすることで、前後の文に変更がなければキャッシュが無効化されにくい。
    """
    body = strip_speak_wrappers(ssml_text)

    # 段落単位
    paragraphs = re.findall(r"(?is)<p[^>]*>.*?</p>", body)
    chunks = []

    for phtml in paragraphs:
        # <p>タグの中身をトークン化：<s>…</s> と <break …/> を拾う
        inner_m = re.search(r"(?is)<p[^>]*>(.*)</p>", phtml)
        inner = inner_m.group(1) if inner_m else phtml
        tokens = re.findall(r"(?is)<s[^>]*>.*?</s>|<break\b[^>]*/>", inner)

        i = 0
        while i < len(tokens):
            tok = tokens[i]
            # 長過ぎる <s> を必要に応じて細分化
            if tok.lower().startswith("<s"):
                s_parts = _split_sentence_tag_if_too_long(tok, limit)
                # 直後の break をまとめる
                j = i + 1
                bbuf = ""
                while j < len(tokens) and tokens[j].lower().startswith("<break"):
                    if len(rebuild_speak(f"<p>{''.join([s_parts[-1], bbuf, tokens[j]])}</p>").encode("utf-8")) <= limit:
                        bbuf += tokens[j]
                        j += 1
                    else:
                        break
                for k, s_unit in enumerate(s_parts):
                    content = f"<p>{s_unit + (bbuf if k == len(s_parts)-1 else '')}</p>"
                    chunks.append(rebuild_speak(content))
                i = j
            else:
                # break のみ単独で来るケース（稀）。小さくても一応チャンク化。
                content = f"<p>{tok}</p>"
                chunks.append(rebuild_speak(content))
                i += 1

    # フォールバック：段落外に残った文字列があれば丸ごとチャンク化
    residual = re.sub(r"(?is)<p[^>]*>.*?</p>", "", body).strip()
    if residual:
        chunks.append(rebuild_speak(f"<p>{residual}</p>"))

    # 最終サイズ確認（バイト制限超過は安全側に再分割）
    fixed = []
    for c in chunks:
        if len(c.encode("utf-8")) <= limit:
            fixed.append(c)
        else:
            # ここに来るのは極めて稀。タグを最小化して強制分割
            inner = strip_speak_wrappers(c)
            for bc in split_by_bytes(inner, limit - 32):
                fixed.append(rebuild_speak(bc))
    return fixed


# ---- キャッシュ付き合成 --------------------------------------------------

def _tts_params():
    return {
        "lang": LANG,
        "voice": VOICE_NAME,
        "sr_hz": 48000,
        "rate": 1.2,
        "pitch": -1.0,
        "enc": "LINEAR16",
    }


def _chunk_key(ssml_chunk: str) -> str:
    payload = {
        "ssml": normalize_for_hash(ssml_chunk),
        "tts": _tts_params(),
    }
    j = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(j.encode("utf-8")).hexdigest()


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def synth_chunk_cached(client, ssml: str, idx: int, out_dir: str):
    key = _chunk_key(ssml)
    cache_path = os.path.join(CACHE_DIR, f"{key}.wav")
    out_path = os.path.join(out_dir, f"part_{idx:03d}.wav")

    if os.path.exists(cache_path):
        shutil.copy2(cache_path, out_path)
        return out_path, key, True

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
    voice = texttospeech.VoiceSelectionParams(language_code=LANG, name=VOICE_NAME)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # WAV
        sample_rate_hertz=_tts_params()["sr_hz"],
        speaking_rate=_tts_params()["rate"],
        pitch=_tts_params()["pitch"],
    )
    resp = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    # キャッシュへ保存
    _ensure_cache_dir()
    with open(cache_path, "wb") as f:
        f.write(resp.audio_content)
    shutil.copy2(cache_path, out_path)
    return out_path, key, False


# ---- 合成処理 ------------------------------------------------------------

def preview_chunks(ssml_or_text: str):
    ssml = ssml_or_text if is_ssml(ssml_or_text) else wrap_plain_as_ssml(ssml_or_text)
    parts = split_ssml_atomic_by_sentence(ssml)
    for i, s in enumerate(parts, 1):
        inner = strip_speak_wrappers(s)
        txt = re.sub(r"<[^>]+>", "", inner)
        print(f"[{i:03d}] {txt[:60].strip()}…")


def synth_all(ssml_or_text: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    client = texttospeech.TextToSpeechClient()

    # 入力がSSMLかプレーンかを自動判定
    ssml = ssml_or_text if is_ssml(ssml_or_text) else wrap_plain_as_ssml(ssml_or_text)

    # 安定チャンク化（1文=1チャンク）
    parts = split_ssml_atomic_by_sentence(ssml)

    # キャッシュ活用しながら合成
    files, manifest = [], {"created_at": datetime.datetime.now().isoformat(), "params": _tts_params(), "parts": []}
    for i, s in enumerate(parts, 1):
        out, key, hit = synth_chunk_cached(client, s, i, out_dir)
        files.append(out)
        manifest["parts"].append({
            "index": i,
            "key": key,
            "cache_hit": hit,
            "bytes": os.path.getsize(out) if os.path.exists(out) else None,
            "ssml": s,
        })

    # 連結（PCM 16bit / 48kHzに統一）
    list_txt = os.path.join(out_dir, "list.txt")
    with open(list_txt, "w", encoding="utf-8") as f:
        for p in files:
            ap = os.path.abspath(p).replace("'", r"'\''")
            f.write(f"file '{ap}'\n")
    out_wav = os.path.join(out_dir, "out_raw.wav").replace("'", r"'\''")
    os.system(f"ffmpeg -hide_banner -y -f concat -safe 0 -i '{list_txt}' -c:a pcm_s16le -ar 48000 '{out_wav}'")

    # マニフェスト保存
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, ensure_ascii=False, indent=2)

    print(f"done: {out_wav}")


# ---- エントリポイント ----------------------------------------------------
if __name__ == "__main__":
    # テキスト or SSML ファイル
    txt_path = "data/20250904.txt"
    if len(sys.argv) > 1:
        txt_path = sys.argv[1]

    base_name = pathlib.Path(txt_path).stem
    timestamp = datetime.datetime.now().strftime("%m%d%H%M")
    out_dir = os.path.join(OUTPUT_BASE, f"{base_name}_{timestamp}")
    os.makedirs(out_dir, exist_ok=True)

    with open(txt_path, encoding="utf-8") as f:
        src = f.read()

    # プレビューしたい場合は環境変数 PREVIEW=1 を付けて実行
    if os.environ.get("PREVIEW") == "1":
        preview_chunks(src)
    else:
        synth_all(src, out_dir)
