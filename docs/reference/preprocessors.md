# Preprocessors

FastPG applies small preprocessing helpers around create and save operations.

## `PreCreateProcessors`

### `model_obj_populate_auto_now_add_fields(model_obj)`

- Reads `model_obj.Meta.auto_now_add_fields`.
- For each listed field, sets `datetime.now(fastpg.TZ)` only when the current value is `None`.

### `model_dict_populate_auto_generated_fields(model_dict, model_cls)`

- Reads `model_cls.Meta.auto_generated_fields`.
- Deletes those keys from the insert payload before SQL execution.

## `PreSaveProcessors`

### `model_obj_populate_auto_now_fields(model_obj)`

- Reads `model_obj.Meta.auto_now_fields`.
- For each listed field, sets `datetime.now(fastpg.TZ)` only when the current value is `None`.

## Where They Are Used

- `AsyncQuerySet.create(...)`
- `AsyncQuerySet.bulk_create(...)`
- `DatabaseModel.save(...)`

If the optional `Meta` lists are missing, these helpers simply do nothing.
