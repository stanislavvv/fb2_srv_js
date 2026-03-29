# Spec for some data structures in files

Only files structs spec. Not for database.

## JsonL fields in .zip.list (pre-index data):

Used as intermediate data for indexing.

Referenced as jsonl_book.

one structure in one file line per book:

```json
{
  "zipfile": "filename.zip",
  "filename": "filename.fb2",
  "genres": [
    "string",
    ...
  ],
  "authors": [
    {
      "name": "string",  # '--- unknown ---' if not defined in book
      "id": "string"  # md5(normalized(author name))
    }, ...
  ],
  "sequences": null || [
    {
      "name": "string",
      "id": "string",  # md5(normalized(sequence name))
      "num": int  # optional, depends on name+id, 0 == unknown
    }, ...
  ],
  "book_title": "string",
  "cover": {
    "content-type": "image/jpeg",
    "data": "base64(image)"
  },
  "book_id": "string",  # md5(zipfilename/bookfilename)
  "lang": "string[2]",
  "date_time": "datetime('+%F_%H:%M')",
  "size": "string(int(filename size in bytes))",
  "annotation": "text/stripped html string",
  "pub_info": {
    "isbn": null || "string",
    "year": null || "string[4]",  # str(year)
    "publisher": null || "string",
    "publisher_id": "string"  # md5(normalized(publisher))
  },
  "deleted": 0 || 1
}
```

## Json book object (in index data)

Will be referenced as book_info

```json
{
  "zipfile": "filename.zip",
  "filename": "filename.fb2",
  "genres": [
    "string",
    ...
  ],
  "authors": [
    {
      "name": "string",  # '--- unknown ---' if not defined in book
      "id": "string"  # md5(normalized(author name))
    }, ...
  ],
  "sequences": null || [
    {
      "name": "string",
      "id": "string",  # md5(normalized(sequence name))
      "num": int  # optional, depends on name+id, 0 == unknown
    }, ...
  ],
  "book_title": "string",
  "book_id": "string",  # md5(zipfilename/bookfilename)
  "lang": "string[2]",
  "date_time": "datetime('+%F_%H:%M')",
  "size": "string(int(filename size in bytes))",
  "annotation": "text/stripped html string",
  "pub_info": {
    "isbn": null || "string",
    "year": null || "string[4]",  # str(year)
    "publisher": null || "string",
    "publisher_id": "string"  # md5(normalized(publisher))
  },
  "deleted": 0 || 1
}
```

## Sequence data object (in index data)

Referenced as sequence_info

```json
{
    "name": "string",
    "id": "string",  # md5(normalized(name))
}
```

or (optionally, currently in author's sequences)

Referenced as sequence_info_cnt

```json
{
    "name": "string",
    "id": "string",  # md5(normalized(name))
    "cnt": int  # books count
}
```

## Author data object

Referenced as author_info (for current author info, not in lists)

```json
{
    "name": "string",  # '--- unknown ---' if not defined in book
    "id": "string"  # md5(normalized(name))
}
```

## Silly dict (in index data)

Referenced as silly_dict

Used for quick check for key existence. Value is int (1 for simple existence check, or may be come object count). Key must be string.

```json
{"key": 1, ...}
```
