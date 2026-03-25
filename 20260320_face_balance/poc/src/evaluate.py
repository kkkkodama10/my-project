"""
PoC メイン評価スクリプト

使い方:
    cd poc
    python src/evaluate.py --algo baseline
    python src/evaluate.py --algo all       # 全アルゴリズム比較
    python src/evaluate.py --algo baseline --visualize
"""
import argparse
import csv
import itertools
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"


# ============================================================
# データロード
# ============================================================

def load_dataset() -> dict[str, list[Path]]:
    """data/ 以下の person_name → [画像パスリスト] を返す。"""
    dataset: dict[str, list[Path]] = {}
    for person_dir in sorted(DATA_DIR.iterdir()):
        if not person_dir.is_dir():
            continue
        images = [
            p for p in sorted(person_dir.iterdir())
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]
        if images:
            dataset[person_dir.name] = images
    return dataset


def make_pairs(dataset: dict[str, list[Path]]):
    """全ペア (path_a, path_b, is_genuine) を生成する。"""
    persons = list(dataset.keys())
    pairs = []

    # Genuine pairs: 同一人物の全組み合わせ
    for person, images in dataset.items():
        for img_a, img_b in itertools.combinations(images, 2):
            pairs.append((img_a, img_b, True, person, person))

    # Impostor pairs: 別人の全組み合わせ（各人1枚目同士など、全組み合わせ）
    for p_a, p_b in itertools.combinations(persons, 2):
        for img_a in dataset[p_a]:
            for img_b in dataset[p_b]:
                pairs.append((img_a, img_b, False, p_a, p_b))

    return pairs


# ============================================================
# 評価指標
# ============================================================

def compute_eer(fpr: np.ndarray, tpr: np.ndarray) -> float:
    """EER（Equal Error Rate）を計算する。"""
    fnr = 1 - tpr
    idx = np.argmin(np.abs(fpr - fnr))
    return float((fpr[idx] + fnr[idx]) / 2)


def compute_dprime(genuine_scores: list[float], impostor_scores: list[float]) -> float:
    """d' (感度指数) を計算する。値が大きいほど識別力が高い。"""
    mu_g = np.mean(genuine_scores)
    mu_i = np.mean(impostor_scores)
    sigma_g = np.std(genuine_scores)
    sigma_i = np.std(impostor_scores)
    return float((mu_g - mu_i) / (np.sqrt((sigma_g**2 + sigma_i**2) / 2) + 1e-9))


def evaluate(embedder, pairs) -> dict:
    """全ペアのスコアを計算し、評価指標を返す。"""
    from algorithms.base import cosine_similarity

    genuine_scores, impostor_scores = [], []
    rows = []

    print(f"\n[{embedder.name}] スコア計算中... ({len(pairs)} ペア)")
    failed = 0
    for i, (path_a, path_b, is_genuine, person_a, person_b) in enumerate(pairs):
        if i % 50 == 0:
            print(f"  {i}/{len(pairs)}")

        emb_a = embedder.embed(str(path_a))
        emb_b = embedder.embed(str(path_b))

        if emb_a is None or emb_b is None:
            failed += 1
            continue

        if hasattr(embedder, 'similarity'):
            score = embedder.similarity(emb_a, emb_b)
        else:
            score = cosine_similarity(emb_a, emb_b)
        rows.append({
            "person_a": person_a,
            "person_b": person_b,
            "image_a": path_a.name,
            "image_b": path_b.name,
            "is_genuine": is_genuine,
            "score": score,
        })
        if is_genuine:
            genuine_scores.append(score)
        else:
            impostor_scores.append(score)

    if not genuine_scores or not impostor_scores:
        print(f"  エラー: スコアが計算できませんでした（顔検出失敗 {failed} ペア）")
        return {}

    labels = [1] * len(genuine_scores) + [0] * len(impostor_scores)
    scores = genuine_scores + impostor_scores
    fpr, tpr, _ = roc_curve(labels, scores)
    auc = roc_auc_score(labels, scores)
    eer = compute_eer(fpr, tpr)
    dprime = compute_dprime(genuine_scores, impostor_scores)

    metrics = {
        "algo": embedder.name,
        "n_genuine": len(genuine_scores),
        "n_impostor": len(impostor_scores),
        "n_failed": failed,
        "genuine_mean": float(np.mean(genuine_scores)),
        "genuine_std": float(np.std(genuine_scores)),
        "impostor_mean": float(np.mean(impostor_scores)),
        "impostor_std": float(np.std(impostor_scores)),
        "auc": auc,
        "eer": eer,
        "dprime": dprime,
    }

    return {"metrics": metrics, "rows": rows, "fpr": fpr, "tpr": tpr,
            "genuine_scores": genuine_scores, "impostor_scores": impostor_scores}


# ============================================================
# 結果保存
# ============================================================

def save_results(result: dict, algo_name: str) -> None:
    """CSV と評価指標を results/{algo_name}/ に保存する。"""
    out_dir = RESULTS_DIR / algo_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # スコア一覧 CSV
    if result.get("rows"):
        with open(out_dir / "scores.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=result["rows"][0].keys())
            writer.writeheader()
            writer.writerows(result["rows"])

    # 評価指標
    m = result["metrics"]
    print(f"\n{'='*50}")
    print(f"  アルゴリズム : {m['algo']}")
    print(f"  Genuine 平均 : {m['genuine_mean']:.3f} (±{m['genuine_std']:.3f})")
    print(f"  Impostor 平均: {m['impostor_mean']:.3f} (±{m['impostor_std']:.3f})")
    print(f"  AUC          : {m['auc']:.4f}")
    print(f"  EER          : {m['eer']:.4f} ({m['eer']*100:.1f}%)")
    print(f"  d'           : {m['dprime']:.3f}")
    print(f"  検出失敗     : {m['n_failed']} ペア")
    print(f"{'='*50}")


def visualize(result: dict, algo_name: str) -> None:
    """ヒストグラム・ROC曲線を保存する。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = RESULTS_DIR / algo_name
    out_dir.mkdir(parents=True, exist_ok=True)

    genuine = result["genuine_scores"]
    impostor = result["impostor_scores"]
    fpr = result["fpr"]
    tpr = result["tpr"]
    m = result["metrics"]

    # ヒストグラム
    fig, ax = plt.subplots(figsize=(8, 5))
    bins = np.linspace(0, 1, 50)
    ax.hist(impostor, bins=bins, alpha=0.6, label="Impostor（別人）", color="red")
    ax.hist(genuine, bins=bins, alpha=0.6, label="Genuine（同一人物）", color="green")
    ax.set_xlabel("Similarity Score")
    ax.set_ylabel("Count")
    ax.set_title(f"{algo_name}  AUC={m['auc']:.3f}  EER={m['eer']*100:.1f}%  d'={m['dprime']:.2f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "histogram.png", dpi=120)
    plt.close(fig)

    # ROC曲線
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(fpr, tpr, label=f"AUC={m['auc']:.3f}")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.3)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC curve - {algo_name}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "roc.png", dpi=120)
    plt.close(fig)

    print(f"  → {out_dir}/ に保存しました")


# ============================================================
# エントリポイント
# ============================================================

def get_embedder(name: str):
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    if name == "baseline":
        from algorithms.baseline import BaselineEmbedder
        return BaselineEmbedder()
    elif name == "aligned":
        from algorithms.aligned import AlignedEmbedder
        return AlignedEmbedder()
    elif name == "face_rec":
        from algorithms.face_rec import FaceRecEmbedder
        return FaceRecEmbedder()
    elif name == "extended":
        from algorithms.extended import ExtendedEmbedder
        return ExtendedEmbedder()
    elif name == "euclidean":
        from algorithms.metric_variants import EuclideanEmbedder
        return EuclideanEmbedder()
    elif name == "manhattan":
        from algorithms.metric_variants import ManhattanEmbedder
        return ManhattanEmbedder()
    elif name == "correlation":
        from algorithms.metric_variants import CorrelationEmbedder
        return CorrelationEmbedder()
    elif name == "normalized":
        from algorithms.normalized import NormalizedEmbedder
        return NormalizedEmbedder()
    elif name == "hybrid":
        from algorithms.hybrid import HybridEmbedder
        return HybridEmbedder()
    else:
        raise ValueError(f"未知のアルゴリズム: {name}")


ALGOS = ["baseline", "aligned", "extended", "euclidean", "manhattan",
         "correlation", "normalized", "hybrid", "face_rec"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", default="baseline",
                        help=f"アルゴリズム名: {ALGOS} または 'all'")
    parser.add_argument("--visualize", action="store_true",
                        help="ヒストグラム・ROC曲線を保存する")
    args = parser.parse_args()

    dataset = load_dataset()
    if not dataset:
        print(f"エラー: {DATA_DIR} に画像が見つかりません。README に従ってデータを配置してください。")
        return

    print(f"データセット: {len(dataset)} 人, 合計 {sum(len(v) for v in dataset.values())} 枚")
    for person, images in dataset.items():
        print(f"  {person}: {len(images)} 枚")

    pairs = make_pairs(dataset)
    genuine_count = sum(1 for p in pairs if p[2])
    impostor_count = len(pairs) - genuine_count
    print(f"ペア数: Genuine {genuine_count}, Impostor {impostor_count}")

    algos = ALGOS if args.algo == "all" else [args.algo]
    all_metrics = []

    for algo_name in algos:
        try:
            embedder = get_embedder(algo_name)
        except ImportError as e:
            print(f"  [{algo_name}] スキップ（インポートエラー: {e}）")
            continue

        # Exp-D: NormalizedEmbedder は calibrate が必要
        if hasattr(embedder, 'calibrate'):
            all_paths = [str(p) for imgs in dataset.values() for p in imgs]
            embedder.calibrate(all_paths)

        result = evaluate(embedder, pairs)
        if not result:
            continue

        save_results(result, algo_name)
        all_metrics.append(result["metrics"])

        if args.visualize:
            visualize(result, algo_name)

    # 全アルゴリズム比較表
    if len(all_metrics) > 1:
        print(f"\n{'アルゴリズム':<15} {'AUC':>6} {'EER':>7} {'d-prime':>8} {'Genuine':>8} {'Impostor':>9}")
        print("-" * 60)
        for m in all_metrics:
            print(f"{m['algo']:<15} {m['auc']:>6.3f} {m['eer']*100:>6.1f}% "
                  f"{m['dprime']:>8.2f} {m['genuine_mean']:>8.3f} {m['impostor_mean']:>9.3f}")


if __name__ == "__main__":
    main()
