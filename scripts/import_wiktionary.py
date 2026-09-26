"""把 kaikki.org 的 Wiktextract 英文字典 JSONL 匯入 MongoDB `grammar`
collection。獨立腳本，不依賴 app 既有的 sys.path 慣例（一次性工具，不跟
app runtime 耦合），自己讀環境變數，命名對齊 geclec_project-db/main_config.py
的既有慣例。

資料來源：https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl
（純英文子集，下載後用 --input 指向本機檔案路徑）。

用法：
    python3 import_wiktionary.py --input /path/to/kaikki-en.jsonl [--limit N]

冪等：用 (term, pos) 當 upsert key，重複執行只會更新既有文件，不會產生
重複資料，之後 kaikki 資料更新可以直接重跑。
"""
import argparse
import json
import os
import sys

from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

MONGODB_HOST = os.environ.get("MONGODB_HOST", "mongodb")
MONGODB_PORT = int(os.environ.get("MONGODB_PORT", "27017"))
MONGODB_DB = os.environ.get("MONGODB_DB", "local")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "grammar")
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "")

BATCH_SIZE = 1000

VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["term", "word", "pos", "definitions", "source"],
        "properties": {
            "term": {"bsonType": "string"},
            "word": {"bsonType": "string"},
            "pos": {"bsonType": "string"},
            "definitions": {
                "bsonType": "array",
                "minItems": 1,
                "items": {"bsonType": "string"},
            },
            "examples": {"bsonType": "array", "items": {"bsonType": "string"}},
            "synonyms": {"bsonType": "array", "items": {"bsonType": "string"}},
            "source": {"bsonType": "string"},
            "source_updated_at": {"bsonType": ["date", "null"]},
        },
    }
}


def connect():
    if MONGODB_USERNAME:
        client = MongoClient(
            host=MONGODB_HOST,
            port=MONGODB_PORT,
            username=MONGODB_USERNAME,
            password=MONGODB_PASSWORD,
        )
    else:
        client = MongoClient(MONGODB_HOST, MONGODB_PORT)
    return client[MONGODB_DB]


def ensure_collection(db):
    """建立 collection（含 validator）跟 index，已存在就跳過——冪等。"""
    if MONGODB_COLLECTION not in db.list_collection_names():
        db.create_collection(MONGODB_COLLECTION, validator=VALIDATOR)
        print(f"[setup] created collection {MONGODB_COLLECTION} with validator")
    else:
        db.command("collMod", MONGODB_COLLECTION, validator=VALIDATOR)
        print(f"[setup] collection {MONGODB_COLLECTION} exists, validator updated")

    db[MONGODB_COLLECTION].create_index("term")
    print("[setup] ensured index on term")


def extract_definitions_and_examples(senses):
    """回傳 (definitions, examples)。跳過純變化形指向的 sense（form_of 存在
    代表這只是「XX 的複數/過去式」之類，不是真正的字義）。examples 只取
    type=="example"（現代口語化例句），過濾掉 type=="quotation"（古英文
    文學引文）。
    kaikki 的 glosses 是「巢狀分類路徑」的完整清單（[上層分類詞義, ...,
    這個子詞義的具體釋義]），只取最後一個元素（最具體的葉節點定義）——用
    extend 整條路徑都收會導致同一個上層分類詞義在每個子詞義裡重複出現。"""
    definitions = []
    examples = []
    for sense in senses:
        if sense.get("form_of") or sense.get("alt_of"):
            continue
        glosses = sense.get("glosses") or []
        if not glosses:
            continue
        leaf_gloss = glosses[-1].strip()
        if leaf_gloss:
            definitions.append(leaf_gloss)
        for ex in sense.get("examples") or []:
            if ex.get("type") == "example" and ex.get("text"):
                examples.append(ex["text"].strip())
    return definitions, examples


def extract_synonyms(entry):
    return [
        s["word"].strip()
        for s in entry.get("synonyms") or []
        if isinstance(s, dict) and s.get("word")
    ]


def transform(entry):
    """把一筆 kaikki JSON 轉成目標 schema；不是有效字典條目就回傳 None。"""
    if entry.get("lang") != "English":
        return None

    word = entry.get("word")
    pos = entry.get("pos")
    if not word or not pos:
        return None

    definitions, examples = extract_definitions_and_examples(entry.get("senses") or [])
    if not definitions:
        return None  # 純變化形指向或沒有真正字義的空殼條目，跳過

    return {
        "term": word.lower(),
        "word": word,
        "pos": pos,
        "definitions": definitions,
        "examples": examples,
        "synonyms": extract_synonyms(entry),
        "source": "wiktionary",
    }


def run(input_path, limit=None):
    db = connect()
    ensure_collection(db)
    collection = db[MONGODB_COLLECTION]

    stats = {"processed": 0, "skipped_non_english": 0, "skipped_empty": 0, "written": 0}
    batch = []

    def flush():
        if not batch:
            return
        try:
            result = collection.bulk_write(batch, ordered=False)
            stats["written"] += result.upserted_count + result.modified_count
        except BulkWriteError as exc:
            print(f"[warn] bulk_write partial failure: {exc.details.get('writeErrors', [])[:1]}", file=sys.stderr)
        batch.clear()

    with open(input_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            stats["processed"] += 1
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get("lang") != "English":
                stats["skipped_non_english"] += 1
                continue

            doc = transform(entry)
            if doc is None:
                stats["skipped_empty"] += 1
                continue

            batch.append(
                UpdateOne(
                    {"term": doc["term"], "pos": doc["pos"]},
                    {"$set": doc},
                    upsert=True,
                )
            )
            if len(batch) >= BATCH_SIZE:
                flush()

            if stats["processed"] % 100000 == 0:
                print(f"[progress] processed={stats['processed']} written={stats['written']}")

    flush()
    print(f"[done] {stats}")
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="kaikki JSONL 檔案路徑")
    parser.add_argument("--limit", type=int, default=None, help="只處理前 N 行（測試用）")
    args = parser.parse_args()
    run(args.input, args.limit)
