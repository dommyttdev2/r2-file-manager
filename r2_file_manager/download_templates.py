from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAX_TEMPLATE_OBJECTS = 500
MAX_TEMPLATES_PER_BUCKET = 100
MAX_TEMPLATE_NAME_LENGTH = 100


class BatchDownloadTemplateStore:
    """Thread-safe local storage for reusable batch download selections."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.RLock()

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write(self, templates: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(templates, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    @staticmethod
    def _validate_bucket(bucket: str) -> str:
        normalized = str(bucket or "").strip()
        if not normalized:
            raise ValueError("バケットを指定してください。")
        return normalized

    @staticmethod
    def _validate_name(name: str) -> str:
        normalized = str(name or "").strip()
        if not normalized:
            raise ValueError("テンプレート名を入力してください。")
        if len(normalized) > MAX_TEMPLATE_NAME_LENGTH:
            raise ValueError("テンプレート名は100文字以内で入力してください。")
        if any(ord(character) < 32 for character in normalized):
            raise ValueError("テンプレート名に改行や制御文字は使用できません。")
        return normalized

    @staticmethod
    def _validate_objects(objects: Any) -> list[dict[str, Any]]:
        if not isinstance(objects, list) or not objects:
            raise ValueError("テンプレートに保存するファイルを選択してください。")
        if len(objects) > MAX_TEMPLATE_OBJECTS:
            raise ValueError("テンプレートに保存できるファイルは500件までです。")

        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in objects:
            if not isinstance(item, dict):
                raise ValueError("テンプレートのファイル情報が正しくありません。")
            key = str(item.get("key") or "")
            if not key or key in seen or len(key.encode("utf-8")) > 1024:
                raise ValueError("テンプレートのObject Keyが正しくありません。")
            seen.add(key)
            try:
                size = max(0, int(item.get("size") or 0))
            except (TypeError, ValueError) as exc:
                raise ValueError("テンプレートのファイルサイズが正しくありません。") from exc
            last_modified = item.get("last_modified")
            normalized.append(
                {
                    "key": key,
                    "name": key.rsplit("/", 1)[-1] or "download",
                    "size": size,
                    "last_modified": str(last_modified) if last_modified else None,
                    "storage_class": str(item.get("storage_class") or "STANDARD"),
                }
            )
        return normalized

    @staticmethod
    def _ensure_unique_name(
        templates: dict[str, dict[str, Any]],
        bucket: str,
        name: str,
        *,
        excluding_id: str | None = None,
    ) -> None:
        normalized_name = name.casefold()
        if any(
            template.get("bucket") == bucket
            and template_id != excluding_id
            and str(template.get("name") or "").casefold() == normalized_name
            for template_id, template in templates.items()
        ):
            raise ValueError("同名のテンプレートがすでに存在します。")

    def list(self, bucket: str) -> list[dict[str, Any]]:
        normalized_bucket = self._validate_bucket(bucket)
        with self._lock:
            templates = [
                template
                for template in self._read().values()
                if template.get("bucket") == normalized_bucket
            ]
        return sorted(templates, key=lambda item: item.get("updated_at", ""), reverse=True)

    def create(self, *, bucket: str, name: str, objects: Any) -> dict[str, Any]:
        normalized_bucket = self._validate_bucket(bucket)
        normalized_name = self._validate_name(name)
        normalized_objects = self._validate_objects(objects)
        with self._lock:
            templates = self._read()
            bucket_count = sum(
                template.get("bucket") == normalized_bucket for template in templates.values()
            )
            if bucket_count >= MAX_TEMPLATES_PER_BUCKET:
                raise ValueError("1つのバケットに保存できるテンプレートは100件までです。")
            self._ensure_unique_name(templates, normalized_bucket, normalized_name)
            now = datetime.now(UTC).isoformat()
            template_id = str(uuid.uuid4())
            template = {
                "id": template_id,
                "bucket": normalized_bucket,
                "name": normalized_name,
                "objects": normalized_objects,
                "created_at": now,
                "updated_at": now,
            }
            templates[template_id] = template
            self._write(templates)
            return template

    def update(
        self,
        template_id: str,
        *,
        bucket: str,
        name: str,
        objects: Any,
    ) -> dict[str, Any]:
        normalized_bucket = self._validate_bucket(bucket)
        normalized_name = self._validate_name(name)
        normalized_objects = self._validate_objects(objects)
        with self._lock:
            templates = self._read()
            template = templates.get(template_id)
            if template is None or template.get("bucket") != normalized_bucket:
                raise KeyError("テンプレートが見つかりません。")
            self._ensure_unique_name(
                templates,
                normalized_bucket,
                normalized_name,
                excluding_id=template_id,
            )
            template.update(
                name=normalized_name,
                objects=normalized_objects,
                updated_at=datetime.now(UTC).isoformat(),
            )
            self._write(templates)
            return template

    def delete(self, template_id: str, *, bucket: str) -> None:
        normalized_bucket = self._validate_bucket(bucket)
        with self._lock:
            templates = self._read()
            template = templates.get(template_id)
            if template is None or template.get("bucket") != normalized_bucket:
                raise KeyError("テンプレートが見つかりません。")
            del templates[template_id]
            self._write(templates)
