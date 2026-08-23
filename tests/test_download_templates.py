from __future__ import annotations

import pytest

from r2_file_manager.download_templates import BatchDownloadTemplateStore


def objects(*keys):
    return [
        {
            "key": key,
            "name": "ignored-name",
            "size": index + 1,
            "last_modified": "2026-08-23T00:00:00+00:00",
            "storage_class": "STANDARD",
        }
        for index, key in enumerate(keys)
    ]


def test_template_store_creates_lists_updates_and_deletes_per_bucket(tmp_path):
    store = BatchDownloadTemplateStore(tmp_path / "templates.json")

    created = store.create(
        bucket="models",
        name="Daily models",
        objects=objects("checkpoints/a.bin", "loras/b.bin"),
    )
    store.create(bucket="archive", name="Daily models", objects=objects("old/a.bin"))

    assert store.list("models") == [created]
    assert created["objects"][0]["name"] == "a.bin"

    updated = store.update(
        created["id"],
        bucket="models",
        name="Daily models updated",
        objects=objects("checkpoints/c.bin"),
    )
    assert updated["created_at"] == created["created_at"]
    assert [item["key"] for item in updated["objects"]] == ["checkpoints/c.bin"]

    store.delete(created["id"], bucket="models")
    assert store.list("models") == []
    assert len(store.list("archive")) == 1


def test_template_store_rejects_duplicate_names_and_invalid_objects(tmp_path):
    store = BatchDownloadTemplateStore(tmp_path / "templates.json")
    store.create(bucket="models", name="Favorites", objects=objects("a.bin"))

    with pytest.raises(ValueError, match="同名"):
        store.create(bucket="models", name="favorites", objects=objects("b.bin"))
    with pytest.raises(ValueError, match="選択"):
        store.create(bucket="models", name="Empty", objects=[])
    with pytest.raises(ValueError, match="500件"):
        store.create(
            bucket="models",
            name="Too many",
            objects=objects(*(f"file-{index}.bin" for index in range(501))),
        )


def test_template_store_cannot_update_or_delete_from_another_bucket(tmp_path):
    store = BatchDownloadTemplateStore(tmp_path / "templates.json")
    created = store.create(bucket="models", name="Favorites", objects=objects("a.bin"))

    with pytest.raises(KeyError, match="見つかりません"):
        store.update(
            created["id"],
            bucket="archive",
            name="Favorites",
            objects=objects("a.bin"),
        )
    with pytest.raises(KeyError, match="見つかりません"):
        store.delete(created["id"], bucket="archive")
