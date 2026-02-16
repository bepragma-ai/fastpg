# Preprocessors

FastPG applies lightweight preprocessors around create/save operations.

## `PreCreateProcessors`

### `model_obj_populate_auto_now_add_fields(model_obj)`

- Reads `model_obj.Meta.auto_now_add_fields`.
- For each listed field: if current value is `None`, sets `datetime.now(fastpg.TZ)`.

### `model_dict_populate_auto_generated_fields(model_dict, model_cls)`

- Reads `model_cls.Meta.auto_generated_fields`.
- Deletes those keys from insert payload before SQL execution.

## `PreSaveProcessors`

### `model_obj_populate_auto_now_fields(model_obj)`

- Reads `model_obj.Meta.auto_now_fields`.
- For each listed field: if current value is `None`, sets `datetime.now(fastpg.TZ)`.

## Where preprocessors are used

- `AsyncQuerySet.create(...)`
- `AsyncQuerySet.bulk_create(...)`
- `DatabaseModel.save(...)`

These helpers fail open when optional `Meta` lists are not defined.
