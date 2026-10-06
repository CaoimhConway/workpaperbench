"""Common public structural checker. No financial reference answers."""
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


if __name__ == "__main__":
    content = Path(sys.argv[1]).read_bytes()
    if len(content) > 65536:
        raise ValueError("answer exceeds 64 KiB")
    answer = json.loads(content, object_pairs_hook=unique,
                        parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite number")))
    schema = json.loads(Path(__file__).with_name("schema.json").read_text())
    Draft202012Validator(schema).validate(answer)
    identifiers = [a["id"] for a in answer["answers"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate claim")
    print("Structure valid. This does not check numerical, evidence, conclusion or replay correctness.")
