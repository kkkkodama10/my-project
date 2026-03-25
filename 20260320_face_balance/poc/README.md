# 顔類似度 精度改善 PoC

## 目的

現状の実装（MediaPipe 15次元手設計特徴量 + コサイン類似度）は、**同一人物・別人問わずスコアが高く出やすく識別力が低い**。

このPoC では複数人・複数枚の写真を使い、以下を目指す。

> **同一人物ペア → 高スコア、別人ペア → 低スコア**
> この傾向が明確に出るアルゴリズム・パラメータを特定する

---

## データ準備

### 必要なもの

- **N 人分 × 5枚** の顔写真（N = 3人以上推奨、多いほど評価精度が上がる）
- 配置先: `poc/data/{person_name}/01.jpg` 〜 `05.jpg`

```
poc/data/
├── alice/
│   ├── 01.jpg
│   ├── 02.jpg
│   ├── 03.jpg
│   ├── 04.jpg
│   └── 05.jpg
├── bob/
│   └── ...
└── carol/
    └── ...
```

### 写真の選び方（精度評価の質に直結）

| 条件 | 推奨 | 避けるべき |
|------|------|-----------|
| 向き | 正面〜やや斜め（±30°以内） | 真横・極端な俯仰角 |
| 枚数の内訳 | 表情違い・照明違い・日別を混ぜる | 同日・同条件のみ |
| 解像度 | 顔が 200px 以上で写っている | 遠景で顔が小さい |
| 1枚に写る顔 | 1人のみ | 集合写真 |
| メガネ | あり・なし混在でOK | — |

---

## 評価指標

### ペア分類

5枚 × N人 のデータから全ペアを生成して評価する。

```
同一人物ペア（Genuine pairs）: C(5,2) × N = 10N 組
別人ペア（Impostor pairs）   : C(5,2) が各人 × 全組み合わせ → 多数
```

例: 4人なら Genuine 40組、Impostor ~600組

### 主要指標

| 指標 | 意味 | 目標 |
|------|------|------|
| **分布の重なり** | Genuine スコア分布 vs Impostor スコア分布の重なり | 重なりが少ない |
| **AUC** | ROC 曲線の面積（1.0が完璧、0.5がランダム） | > 0.85 |
| **EER** | 誤受入率=誤拒否率になる閾値（低いほど良い） | < 15% |
| **d' (d-prime)** | 平均の差 / 標準偏差の平均（感度指数）| > 1.5 |

### 可視化

- ヒストグラム: Genuine / Impostor スコア分布を重ねて表示
- ROC 曲線: 閾値ごとの FAR/FRR プロット
- ヒートマップ: 全ペアのスコアを人物 × 人物で可視化

---

## 試すアルゴリズム（候補）

### Baseline（現状）

```
MediaPipe 468点 → 手設計15次元 → コサイン類似度
```

### Exp-A: 顔アライメント追加

```
目の位置を水平補正してから特徴量抽出
→ 傾きによる誤差を除去
```

### Exp-B: ランドマーク次元拡張

```
15次元 → 40〜60次元
追加候補: 目の縦幅・鼻翼幅・唇の厚み・目頭形状
```

### Exp-C: 類似度指標の変更

```
コサイン類似度 → ユークリッド距離 / マンハッタン距離 / L2 正規化後のドット積
```

### Exp-D: スコア正規化（スケーリング）

```
全ペアのスコア分布から z-score 変換
→ 「この人物集合の中での相対的な近さ」に変換
```

### Exp-E: face_recognition (dlib 128次元)

```
pip install face_recognition
→ 学習済み 128次元埋め込み + コサイン類似度
→ 現状実装との精度差を確認
```

### Exp-F: Landmark + Texture ハイブリッド

```
距離比率特徴量 + 顔領域の LBP（局所二値パターン）テクスチャ特徴量
→ 骨格 + 肌のきめ・テクスチャを組み合わせ
```

---

## 進め方

### Phase 0: 環境・データ準備 ✅

- [x] `poc/data/` に写真を配置（3人: Ann 5枚, John 5枚, Shion 7枚 = 計17枚）
- [x] `poc/requirements.txt` を用意
- [x] `poc/src/evaluate.py` メイン評価スクリプトを作成
- [x] `poc/src/detector.py` MediaPipe Tasks API ベースの検出器を作成

### Phase 1: Baseline 計測 ✅

- [x] 現状アルゴリズム（15次元）で全ペアスコアを計算
- [x] 分布ヒストグラムと AUC / EER を出力
- [x] 結果: AUC=0.824, EER=22.0%, d'=1.30 → 識別力不足を確認

### Phase 2: アルゴリズム実験 ✅

全6実験を実施し、結果を `poc/results/` に保存（CSV + histogram.png + roc.png）。

```
Exp-A (aligned) → Exp-B (extended) → Exp-C (euclidean/manhattan/correlation)
→ Exp-D (normalized) → Exp-E (face_rec) → Exp-F (hybrid)
```

### Phase 3: 最良手法の決定 ✅

- [x] 全実験の AUC / EER を一覧表で比較（後述）
- [x] 精度と実装コストのトレードオフを評価（後述）
- [x] 本番実装に組み込む手法を決定 → **face_rec (dlib 128次元)**

### Phase 4: 本番へのフィードバック

- [ ] 決定した手法を `backend/app/services/analysis/` に実装
- [ ] Strategy パターン（DistanceRatioExtractor の差し替え）で対応

---

## 実験結果（Phase 3: 結論）

### 評価データ

| 項目 | 値 |
|------|-----|
| 人数 | 3人（Ann, John, Shion） |
| 総画像数 | 17枚（5, 5, 7枚） |
| Genuine ペア | 41組（同一人物の組み合わせ） |
| Impostor ペア | 95組（別人の組み合わせ） |

### 全アルゴリズム比較表

| 順位 | アルゴリズム | 実験 | AUC | EER | d' | Genuine平均 | Impostor平均 |
|------|-------------|------|-----|-----|-----|-------------|--------------|
| 1 | **face_rec** | Exp-E | **0.952** | **7.3%** | 2.18 | 0.958 | 0.845 |
| 2 | normalized | Exp-D | 0.926 | 14.2% | **2.24** | 0.546 | -0.319 |
| 3 | extended | Exp-B | 0.884 | 18.5% | 1.70 | 0.996 | 0.982 |
| 4 | manhattan | Exp-C | 0.827 | 22.0% | -0.13 | 0.000 | 0.000 |
| 5 | aligned | Exp-A | 0.825 | 19.8% | 1.32 | 0.992 | 0.969 |
| 6 | baseline | — | 0.824 | 22.0% | 1.30 | 0.992 | 0.971 |
| 7 | correlation | Exp-C | 0.823 | 22.0% | 1.29 | 0.995 | 0.982 |
| 8 | hybrid | Exp-F | 0.822 | 26.0% | 1.26 | 0.890 | 0.815 |
| 9 | euclidean | Exp-C | 0.819 | 18.7% | -0.15 | 0.000 | 0.000 |

### 各実験の考察

#### Exp-A: 顔アライメント（aligned）— 微改善

目の水平補正は EER を 22.0% → 19.8% に改善したが、AUC はほぼ変わらず。
15次元特徴量自体が IPD 正規化済みのため、アライメントの効果が薄い。

#### Exp-B: ランドマーク次元拡張（extended）— 中程度の改善

15次元 → 45次元に拡張（目の縦幅・鼻翼幅・唇厚み・対称性・顎角度など）。
AUC が 0.824 → 0.884 に改善。手設計特徴量の延長として有効だが限界がある。

#### Exp-C: 類似度指標の変更（euclidean/manhattan/correlation）— 効果なし

- **euclidean/manhattan**: `exp(-d)` のスケーリングが合わず、スコアが 0 近辺に潰れた。AUC は距離の順序情報で算出されるため一応動作するが実用性なし。
- **correlation**: ピアソン相関は baseline のコサイン類似度とほぼ同等。15次元では情報が足りず、指標を変えても改善しない。

#### Exp-D: スコア正規化（normalized）— 大幅改善

baseline の15次元特徴量を全画像の統計量で z-score 正規化してからコサイン類似度を取る方式。
AUC=0.926, EER=14.2%, d'=2.24（全手法中最高の d'）と大幅に改善。

元の特徴量は次元ごとにスケールが大きく異なり（角度: 数十, 比率: 0.x）、
コサイン類似度が角度次元に支配されていた問題を正規化が解消した。

**外部ライブラリ不要**という利点があるが、正規化パラメータが全画像に依存するため、
新規画像追加時に再計算が必要という運用上の課題がある。

#### Exp-E: face_recognition / dlib 128次元（face_rec）— 最良

AUC=0.952, EER=7.3% と圧倒的に高い精度。dlib の学習済み deep learning モデル
（ResNet ベース、数百万枚の顔画像で事前学習）が生成する128次元埋め込みは、
手設計特徴量とは本質的に異なる識別力を持つ。

Genuine 平均 0.958 vs Impostor 平均 0.845 と、スコア分布が明確に分離している。

#### Exp-F: LBP テクスチャハイブリッド（hybrid）— 悪化

ランドマーク15次元 + LBP 512次元を結合。AUC=0.822, EER=26.0% と baseline より悪化。
LBP は照明条件・画像品質の変動に敏感で、写真間のテクスチャ差異が
ノイズとして作用し、かえって識別力を下げた。

### 精度 vs 実装コストのトレードオフ

| アルゴリズム | AUC | 追加依存 | CPU負荷 | 運用の複雑さ |
|---|---|---|---|---|
| **face_rec** | 0.952 | dlib, face_recognition | 高（dlib のCNNモデル推論） | 低（stateless） |
| normalized | 0.926 | なし | 低 | 中（正規化パラメータの管理） |
| extended | 0.884 | なし | 低 | 低 |
| baseline | 0.824 | なし | 低 | 低 |

### 決定: 本番採用手法

**face_rec (dlib 128次元埋め込み) を採用する。**

#### 選定理由

1. **精度が圧倒的**: AUC=0.952 は目標（>0.85）を大幅にクリア。EER=7.3% は実用レベル
2. **スコア分布の明確な分離**: Genuine 0.958 vs Impostor 0.845 → 閾値設定が容易
3. **実装がシンプル**: `face_recognition.face_encodings()` 1行で128次元ベクトルが取得でき、コサイン類似度で比較するだけ
4. **Stateless**: normalized と違い、他の画像に依存しない。新規画像も即座に比較可能
5. **検出失敗ゼロ**: 全136ペアで顔検出に成功（dlib の HOG ベース検出器は堅牢）

#### 懸念点と対策

| 懸念 | 対策 |
|------|------|
| dlib のビルドが Apple Silicon で困難 | Docker 環境で統一（本番は Docker 前提） |
| CPU 負荷が高い | 分析パイプラインは非同期処理済み。キャッシュも活用 |
| モデルサイズ（~100MB） | Docker イメージに含める。ランタイムDLは不要 |
| 3人17枚の少数データでの評価 | 本番導入後にデータ増加に応じて再評価を検討 |

#### Phase 4 への申し送り

本番統合時の実装方針:

1. `backend/app/services/analysis/` に `dlib_embedder.py` を追加
2. 既存の `DistanceRatioExtractor` と差し替え可能な Strategy パターンで実装
3. `face_recognition` を `backend/requirements.txt` に追加
4. Docker イメージに `cmake` + `dlib` ビルド環境を追加
5. 既存の MediaPipe ランドマーク検出は可視化用途で残す（ランドマーク確認画面）

---

## ディレクトリ構成

```
poc/
├── README.md                  ← このファイル
├── requirements.txt           ← PoC用の追加ライブラリ
├── face_landmarker.task       ← MediaPipe Tasks API モデルファイル
├── data/                      ← 評価用写真（.gitignore 対象）
│   ├── Ann/   (5枚)
│   ├── John/  (5枚)
│   └── Shion/ (7枚)
├── src/
│   ├── evaluate.py            ← メイン評価スクリプト（全ペア計算・指標出力・可視化）
│   ├── detector.py            ← MediaPipe Tasks API ベースの顔ランドマーク検出器
│   └── algorithms/
│       ├── __init__.py
│       ├── base.py            ← FaceEmbedder ABC + 類似度関数
│       ├── baseline.py        ← Baseline: 15次元手設計特徴量
│       ├── aligned.py         ← Exp-A: 顔アライメント（目の水平補正）
│       ├── extended.py        ← Exp-B: 45次元拡張特徴量
│       ├── metric_variants.py ← Exp-C: 類似度指標変更（euclidean/manhattan/correlation）
│       ├── normalized.py      ← Exp-D: z-score 正規化
│       ├── face_rec.py        ← Exp-E: face_recognition (dlib 128次元) ★採用
│       └── hybrid.py          ← Exp-F: ランドマーク + LBP テクスチャ
└── results/                   ← 実験結果（自動生成、.gitignore 対象）
    ├── baseline/   (scores.csv, histogram.png, roc.png)
    ├── aligned/
    ├── extended/
    ├── euclidean/
    ├── manhattan/
    ├── correlation/
    ├── normalized/
    ├── hybrid/
    └── face_rec/   ★最良結果
```

---

## アルゴリズム共通インターフェース

各実験は同一インターフェースで実装し、差し替えを容易にする。

```python
from abc import ABC, abstractmethod
import numpy as np

class FaceEmbedder(ABC):
    name: str  # 実験名（ファイル名などに使用）

    @abstractmethod
    def embed(self, image_path: str) -> np.ndarray:
        """画像パスから特徴量ベクトルを返す。"""
        ...

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
```

---

## 判断基準（次のアクションを決めるための閾値）

| AUC | 判断 |
|-----|------|
| < 0.70 | アルゴリズム自体に問題あり。別手法へ |
| 0.70〜0.85 | 改善の余地あり。パラメータチューニング |
| 0.85〜0.95 | 実用レベル。本番実装を検討 |
| > 0.95 | 高精度。データが少ないと過学習の可能性を確認 |

---

## 注意事項

- PoC は Docker コンテナ外（ホストの Python 環境）で実行する想定
- `face_recognition` ライブラリは `cmake` と `dlib` のビルドが必要（Homebrew で事前インストール）
- 写真は個人情報のため `poc/data/` は `.gitignore` に追加すること
- 実験結果の PNG/CSV は `poc/results/` に自動保存し、人手で消さない（比較のため）
