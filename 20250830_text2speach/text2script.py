from google.cloud import texttospeech
import math, os, re, html
import pathlib, datetime, sys

MAX_BYTES = 4800  # 5000バイト未満で余裕をもたせる
VOICE_NAME = "ja-JP-Standard-C"
LANG = "ja-JP"
OUTPUT_BASE = "/Users/Pictures/音源素材"

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

def split_ssml_preserving_tags(ssml_text: str, limit=MAX_BYTES):
    """
    SSMLを<p>→</s>→句読点の順で細かくして、<speak>…</speak>に包んだチャンク列を返す。
    """
    body = strip_speak_wrappers(ssml_text)
    # 第1段：段落単位（</p>）で粗く分割
    segs = re.split(r"(?i)(?<=</p>)", body)
    segs = [s for s in segs if s and s.strip()]

    chunks, buf = [], ""
    def push_buf():
        nonlocal buf
        if buf.strip():
            chunks.append(rebuild_speak(buf))
            buf = ""

    for seg in segs:
        cand = rebuild_speak(buf + seg)
        if len(cand.encode("utf-8")) <= limit:
            buf += seg
            continue

        # ここからはseg単体が大きいので、</s>（文）でさらに分割
        push_buf()
        mini = re.split(r"(?i)(?<=</s>)", seg)
        tmp = ""
        for ms in [m for m in mini if m.strip()]:
            cand2 = rebuild_speak(tmp + ms)
            if len(cand2.encode("utf-8")) <= limit:
                tmp += ms
                continue

            # さらに句読点で分割（。！？?）
            if tmp.strip():
                chunks.append(rebuild_speak(tmp)); tmp = ""
            units = re.split(r"(?<=[。！？\?])", ms)
            uacc = ""
            for u in [u for u in units if u.strip()]:
                cand3 = rebuild_speak(uacc + u)
                if len(cand3.encode("utf-8")) <= limit:
                    uacc += u
                    continue
                if uacc.strip():
                    chunks.append(rebuild_speak(uacc)); uacc = ""
                # それでも大きい場合はバイト分割（稀）
                for bc in split_by_bytes(u, limit - 32):  # <speak>分の余白
                    chunks.append(rebuild_speak(bc))
            if uacc.strip():
                chunks.append(rebuild_speak(uacc))
        if tmp.strip():
            chunks.append(rebuild_speak(tmp))
    push_buf()
    return chunks

# ---- 合成処理 ------------------------------------------------------------

def synth_chunk(client, ssml: str, idx: int, out_dir: str):
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
    voice = texttospeech.VoiceSelectionParams(language_code=LANG, name=VOICE_NAME)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # WAV
        sample_rate_hertz=48000,
        speaking_rate=1.2,
        pitch=-1.0,
    )
    resp = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    out = os.path.join(out_dir, f"part_{idx:03d}.wav")
    with open(out, "wb") as f:
        f.write(resp.audio_content)
    return out

def synth_all(ssml_or_text: str, out_dir: str):
    client = texttospeech.TextToSpeechClient()

    # 入力がSSMLかプレーンかを自動判定
    ssml = ssml_or_text if is_ssml(ssml_or_text) else wrap_plain_as_ssml(ssml_or_text)

    # SSMLを壊さない分割
    parts = split_ssml_preserving_tags(ssml)
    files = [synth_chunk(client, s, i, out_dir) for i, s in enumerate(parts, 1)]

    # 連結（PCM 16bit / 48kHzに統一）
    list_txt = os.path.join(out_dir, "list.txt")
    with open(list_txt, "w", encoding="utf-8") as f:
        for p in files:
            # パスにシングルクォートがある場合はエスケープ
            ap = os.path.abspath(p).replace("'", r"'\''")
            f.write(f"file '{ap}'\n")
    out_wav = os.path.join(out_dir, "out_raw.wav").replace("'", r"'\''")
    os.system(f"ffmpeg -hide_banner -y -f concat -safe 0 -i '{list_txt}' -c:a pcm_s16le -ar 48000 '{out_wav}'")
    print(f"done: {out_wav}")

# ---- エントリポイント ----------------------------------------------------

if __name__ == "__main__":
    # テキスト or SSML ファイル
    txt_path = "data/20250825.txt"
    if len(sys.argv) > 1:
        txt_path = sys.argv[1]

    base_name = pathlib.Path(txt_path).stem
    timestamp = datetime.datetime.now().strftime("%m%d%H%M")
    out_dir = os.path.join(OUTPUT_BASE, f"{base_name}_{timestamp}")
    os.makedirs(out_dir, exist_ok=True)

    with open(txt_path, encoding="utf-8") as f:
        src = f.read()

    synth_all(src, out_dir)
    