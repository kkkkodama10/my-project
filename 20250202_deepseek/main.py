# main.py
from fastapi import FastAPI, Request
import uvicorn
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = FastAPI()

# 例: モデルの名前やパスはDeep Seekの情報に合わせて変更してください
model_name_or_path = "./Janus-Pro-1B"  # Hugging Face Hub上のリポジトリの場合
tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_name_or_path, trust_remote_code=True)
model.eval()  # 推論モードに設定

@app.post("/generate")
async def generate(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")

    if not prompt:
        return {"error": "promptが必要です"}

    # 特殊トークンを追加しない
    inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)

    # ボキャブラリーサイズを超えないようチェック
    max_token_id = inputs["input_ids"].max().item()
    if max_token_id >= tokenizer.vocab_size:
        return {"error": f"Invalid token ID {max_token_id} (vocab size: {tokenizer.vocab_size})"}

    # pad_token_id を設定
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # 推論
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=100)

    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"generated_text": generated_text}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)