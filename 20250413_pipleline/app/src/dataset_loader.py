import json
import pandas as pd
from sklearn.datasets import load_iris, load_wine
from sklearn.model_selection import train_test_split

BUILTIN_LOADERS = {
    "load_iris": load_iris,
    "load_wine": load_wine,
}

def load_dataset(config_path, dataset_key, test_size=0.25, random_state=42):
    with open(config_path, "r") as f:
        config = json.load(f)

    if dataset_key not in config:
        raise ValueError(f"Dataset '{dataset_key}' not found.")

    dataset_cfg = config[dataset_key]

    if dataset_cfg["type"] == "builtin":
        loader_func = BUILTIN_LOADERS[dataset_cfg["loader"]]
        data = loader_func(**dataset_cfg["params"])
        X, y = data.data, data.target

    elif dataset_cfg["type"] == "csv":
        df = pd.read_csv(dataset_cfg["path"])
        target_col = dataset_cfg["params"]["target_column"]
        X = df.drop(target_col, axis=1).values
        y = df[target_col].values

    else:
        raise ValueError(f"Unknown dataset type: {dataset_cfg['type']}")

    return train_test_split(X, y, test_size=test_size, random_state=random_state)
