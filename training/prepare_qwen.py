"""Convert training rows to LLaMA-Factory ShareGPT format without test-set leakage."""

import json
from pathlib import Path

root = Path(__file__).parent
source = json.loads((root / "dataset.json").read_text())
output = root / "llamafactory"
output.mkdir(exist_ok=True)
rows = [
    {
        "conversations": [
            {
                "from": "human",
                "value": "Classify into stops, signals, summary, knowledge. Return only the label. "
                + r["text"],
            },
            {"from": "gpt", "value": r["label"]},
        ]
    }
    for r in source["train"]
]
(output / "replay_router.json").write_text(json.dumps(rows, indent=2))
(output / "dataset_info.json").write_text(
    json.dumps(
        {
            "replay_router": {
                "file_name": "replay_router.json",
                "formatting": "sharegpt",
                "columns": {"messages": "conversations"},
            }
        },
        indent=2,
    )
)
