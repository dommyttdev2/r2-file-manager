"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  addSelection,
  buildAria2Command,
  buildDownloadOutputs,
  formatBatchTotalSize,
  selectVisible,
  uniqueDownloadNames,
} = require("../r2_file_manager/static/download_utils.js");

test("URL, curl, wget, and aria2 use the same URLs", () => {
  const downloads = [
    { key: "models/a/model.bin", url: "https://example.test/a?sig=one" },
    { key: "models/b/model.bin", url: "https://example.test/b?sig=two" },
    { key: "models/c/model.bin", url: "https://example.test/c?sig=three" },
  ];

  assert.deepEqual(uniqueDownloadNames(downloads.map((item) => item.key)), [
    "model.bin",
    "model (2).bin",
    "model (3).bin",
  ]);
  assert.deepEqual(buildDownloadOutputs(downloads), {
    url: "https://example.test/a?sig=one\nhttps://example.test/b?sig=two\nhttps://example.test/c?sig=three",
    curl: [
      "curl --fail --location --output 'model.bin' 'https://example.test/a?sig=one'",
      "curl --fail --location --output 'model (2).bin' 'https://example.test/b?sig=two'",
      "curl --fail --location --output 'model (3).bin' 'https://example.test/c?sig=three'",
    ].join("\n"),
    wget: [
      "wget --output-document='model.bin' 'https://example.test/a?sig=one'",
      "wget --output-document='model (2).bin' 'https://example.test/b?sig=two'",
      "wget --output-document='model (3).bin' 'https://example.test/c?sig=three'",
    ].join("\n"),
    aria2: "aria2c --allow-overwrite=false --auto-file-renaming=false -j3 -x3 -Z 'https://example.test/a?sig=one' 'https://example.test/b?sig=two' 'https://example.test/c?sig=three'",
  });
});

test("aria2 connection count is configurable and clamped to its supported range", () => {
  const downloads = [
    { key: "one.bin", url: "https://example.test/one?x=1&y=2" },
    { key: "two.bin", url: "https://example.test/two?x=3&y=4" },
  ];

  assert.equal(
    buildAria2Command(downloads, 8),
    "aria2c --allow-overwrite=false --auto-file-renaming=false -j3 -x8 -Z 'https://example.test/one?x=1&y=2' 'https://example.test/two?x=3&y=4'",
  );
  assert.match(buildAria2Command(downloads, 99), /^aria2c --allow-overwrite=false --auto-file-renaming=false -j3 -x16 -Z /);
  assert.match(buildAria2Command(downloads, 0), /^aria2c --allow-overwrite=false --auto-file-renaming=false -j3 -x1 -Z /);
  assert.equal(
    buildAria2Command([downloads[0]], 3),
    "aria2c --allow-overwrite=false --auto-file-renaming=false -j3 -x3 'https://example.test/one?x=1&y=2'",
  );
});

test("aria2 concurrent download count is configurable and clamped", () => {
  const downloads = [
    { key: "one.bin", url: "https://example.test/one" },
    { key: "two.bin", url: "https://example.test/two" },
  ];

  assert.match(buildAria2Command(downloads, 3, 8), /^aria2c --allow-overwrite=false --auto-file-renaming=false -j8 -x3 -Z /);
  assert.match(buildAria2Command(downloads, 3, 99), /^aria2c --allow-overwrite=false --auto-file-renaming=false -j16 -x3 -Z /);
  assert.match(buildAria2Command(downloads, 3, 0), /^aria2c --allow-overwrite=false --auto-file-renaming=false -j1 -x3 -Z /);
});

test("selection survives changing visible folders and is capped at 500", () => {
  const selected = new Map();
  assert.equal(addSelection(selected, { key: "folder-a/a.bin", size: 1 }), true);
  assert.equal(addSelection(selected, { key: "folder-b/b.bin", size: 2 }), true);
  assert.deepEqual([...selected.keys()], ["folder-a/a.bin", "folder-b/b.bin"]);

  const visible = Array.from({ length: 500 }, (_value, index) => ({
    key: `search/result-${index}.bin`,
    size: index,
  }));
  const result = selectVisible(selected, visible, 500);

  assert.equal(result.added, 498);
  assert.equal(result.limitReached, true);
  assert.equal(selected.size, 500);
  assert.equal(addSelection(selected, { key: "overflow.bin" }, 500), false);
});

test("selecting the same object twice keeps a single canonical selection", () => {
  const selected = new Map();
  const original = { key: "models/a.bin", size: 1 };
  assert.equal(addSelection(selected, original), true);
  assert.equal(addSelection(selected, { key: "models/a.bin", size: 99 }), true);
  assert.equal(selected.size, 1);
  assert.equal(selected.get("models/a.bin"), original);
});

test("batch total size uses MB below one GiB and GB from one GiB", () => {
  assert.equal(formatBatchTotalSize(0), "0 MB");
  assert.equal(formatBatchTotalSize(512 * 1024 ** 2), "512.0 MB");
  assert.equal(formatBatchTotalSize(1024 ** 3), "1.00 GB");
  assert.equal(formatBatchTotalSize(1.5 * 1024 ** 3), "1.50 GB");
});
