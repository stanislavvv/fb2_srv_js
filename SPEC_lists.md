# Spec for some data structures in files

## JsonL fields in .zip.list:

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
      "id": "string"  # md5(normalized(name))
    }, ...
  ],
  "sequences": null || [
    {
      "name": "string",
      "id": "string",  # md5(normalized(name))
      "num": int  # optional, depends on name+id, 0 == unknown
    }, ...
  ],
  "book_title": "string",
  "cover": {
    "content-type": "image/jpeg",
    "data": "base64(image)"
  },
  "book_id": "string",  # md5(normalized(book_title))
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

## Json book object

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
      "id": "string"  # md5(normalized(name))
    }, ...
  ],
  "sequences": null || [
    {
      "name": "string",
      "id": "string",  # md5(normalized(name))
      "num": int  # optional, depends on name+id, 0 == unknown
    }, ...
  ],
  "book_title": "string",
  "book_id": "string",  # md5(normalized(book_title))
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

## Sequence data object

Referenced as sequence_info

```json
{
    "name": "string",
    "id": "string",  # md5(normalized(name))
}
```

## Author data object

Referenced as author_info

```json
{
    "name": "string",  # '--- unknown ---' if not defined in book
    "id": "string"  # md5(normalized(name))
}
```

## Silly dict

Referenced as silly_dict

Used for quick check for key existence.

```json
{"key": 1, ...}
```
