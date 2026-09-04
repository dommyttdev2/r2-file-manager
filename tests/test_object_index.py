from r2_file_manager.object_index import ObjectIndex


def object_item(key, size=1):
    return {
        "key": key,
        "size": size,
        "etag": f"etag-{size}",
        "last_modified": None,
        "storage_class": "STANDARD",
    }


def test_index_persists_and_searches_paths_case_insensitively(tmp_path):
    path = tmp_path / "objects.sqlite3"
    index = ObjectIndex(path)
    index.replace_bucket(
        "account",
        "assets",
        [object_item("Models/ANIMA_v1.bin", 10), object_item("other/file.txt")],
    )

    reopened = ObjectIndex(path)
    result = reopened.search("account", "assets", "anima")

    assert [item["key"] for item in result["objects"]] == ["Models/ANIMA_v1.bin"]
    assert result["scanned"] == 0


def test_replace_bucket_removes_objects_missing_from_r2_snapshot(tmp_path):
    index = ObjectIndex(tmp_path / "objects.sqlite3")
    index.replace_bucket("account", "assets", [object_item("old.bin")])
    index.replace_bucket("account", "assets", [object_item("new.bin")])

    assert index.search("account", "assets", ".bin")["objects"] == [
        {
            "key": "new.bin",
            "name": "new.bin",
            "size": 1,
            "etag": "etag-1",
            "last_modified": None,
            "storage_class": "STANDARD",
        }
    ]


def test_upload_move_and_delete_updates_are_searchable(tmp_path):
    index = ObjectIndex(tmp_path / "objects.sqlite3")
    index.upsert("account", "assets", object_item("incoming/model.bin", 42))
    index.move("account", "assets", "incoming/model.bin", "archive/model.bin")

    assert index.search("account", "assets", "incoming")["objects"] == []
    assert [item["key"] for item in index.search("account", "assets", "archive")["objects"]] == [
        "archive/model.bin"
    ]

    index.delete("account", "assets", ["archive/model.bin"])
    assert index.search("account", "assets", "archive")["objects"] == []


def test_search_uses_local_offset_pagination(tmp_path):
    index = ObjectIndex(tmp_path / "objects.sqlite3")
    index.replace_bucket(
        "account",
        "assets",
        [object_item(f"match/{number:03}.bin") for number in range(101)],
    )

    first = index.search("account", "assets", "match")
    second = index.search("account", "assets", "match", int(first["next_token"]))

    assert len(first["objects"]) == 100
    assert first["next_token"] == "100"
    assert [item["key"] for item in second["objects"]] == ["match/100.bin"]
    assert second["next_token"] is None
