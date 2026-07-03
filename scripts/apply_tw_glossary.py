#!/usr/bin/env python3
import json
import re
import sys
from collections import Counter


TOKEN_RE = re.compile(r"%\d*\$?[#0\- +]*(?:\d+|\*)?(?:\.\d+)?[A-Za-z]|{{[^{}]+}}|{[A-Za-z0-9_.-]+}|</?[A-Za-z][^>]*>")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tokens(value):
    return Counter(TOKEN_RE.findall(value))


def apply_terms(value, terms):
    for source, target in terms:
        value = value.replace(source, target)
    return value


def walk(original, converted, terms, path="$"):
    if type(original) is not type(converted):
        raise SystemExit(f"type mismatch at {path}")

    if isinstance(original, dict):
        if original.keys() != converted.keys():
            raise SystemExit(f"key mismatch at {path}")
        return {key: walk(original[key], converted[key], terms, f"{path}.{key}") for key in original}

    if isinstance(original, list):
        if len(original) != len(converted):
            raise SystemExit(f"list length mismatch at {path}")
        return [walk(a, b, terms, f"{path}[{i}]") for i, (a, b) in enumerate(zip(original, converted))]

    if isinstance(original, str):
        value = apply_terms(converted, terms)
        if tokens(original) != tokens(value):
            raise SystemExit(f"placeholder mismatch at {path}")
        return value

    return converted


def self_test():
    terms = [("倉庫", "儲存庫")]
    original = {"a": "打开 {repo} 仓库 %s", "b": ["<b>确定</b>"]}
    converted = {"a": "打開 {repo} 倉庫 %s", "b": ["<b>確定</b>"]}
    result = walk(original, converted, terms)
    assert result["a"] == "打開 {repo} 儲存庫 %s"
    assert result["b"][0] == "<b>確定</b>"


def main(argv):
    if argv == ["--self-test"]:
        self_test()
        return
    if len(argv) != 4:
        raise SystemExit("usage: apply_tw_glossary.py ORIGINAL_JSON CONVERTED_JSON GLOSSARY_JSON OUTPUT_JSON")

    original_path, converted_path, glossary_path, output_path = argv
    glossary = load(glossary_path)
    terms = sorted(glossary.items(), key=lambda item: len(item[0]), reverse=True)
    result = walk(load(original_path), load(converted_path), terms)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
