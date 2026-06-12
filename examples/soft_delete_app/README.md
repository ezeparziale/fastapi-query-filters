# Soft-Delete Example Application

This example demonstrates how to use the dynamic soft-delete filtering capability of `fastapi-query-filters` using a Stargate SG-1 themed domain model.

## Features

- Hides destroyed/deleted items automatically from query results.
- Uses `soft_delete_field` in `FilterConfig`.
- Automatic detection of column type (supports `Boolean` and `DateTime`/`Date`).

## Running the Example

Start the FastAPI application with Uvicorn:

```bash
uvicorn examples.soft_delete_app.main:app --reload
```

Then query the endpoint:

```bash
# Get only non-destroyed artifacts (automatically hides the "Staff Weapon" because it is_destroyed = True)
GET /artifacts
```
