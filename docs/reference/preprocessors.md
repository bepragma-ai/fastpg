# Preprocessors

FastPG applies a handful of pre-save hooks to keep timestamp fields up to date
without littering your application code with `datetime.utcnow()` calls.

## Timezone detection

The library reads the `FASTPG_TZ` environment variable to determine which
timezone should be used when populating automatic timestamp fields. If the value
is missing or invalid, UTC is used as a safe default.

## Creation hooks

`PreCreateProcessors.model_obj_populate_auto_now_add_fields(model_obj)`

- Populates each field listed in `Meta.auto_now_add_fields` with the current
  timezone-aware datetime.
- Invoked automatically during `create` and `bulk_create` operations before the
  model is serialised and inserted.

`PreCreateProcessors.model_dict_populate_auto_generated_fields(model_dict, model_cls)`

- Removes any fields marked in `Meta.auto_generated_fields` from the payload
  before inserting, allowing PostgreSQL defaults or sequences to take over.

## Update hooks

`PreSaveProcessors.model_obj_populate_auto_now_fields(model_obj)`

- Populates each field listed in `Meta.auto_now_fields` prior to calling `save`.
- Ensures updated timestamps always reflect the time of the update, regardless
  of what the caller set on the model instance.

These hooks are automatically wired into the ORM, but they can also be called
manually if you need similar behaviour in custom scripts.
