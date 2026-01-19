import re
import time
import random
import functools
from typing import Optional

from .constants import OPERATORS
from .errors import (
    InvalidINClauseValueError,
    UnsupportedOperatorError,
    MalformedMetaError,
)


import logging
logger = logging.getLogger(__name__)


class Relation:
    """Represents a relationship between two models."""

    def __init__(
        self,
        related_model,
        foreign_field: str,
        related_name: Optional[str] = None,
    ) -> None:
        self.RelatedModel = related_model
        try:
            self.table = self.RelatedModel.Meta.db_table
        except AttributeError as e:
            if str(e) == "Meta":
                raise MalformedMetaError(self.RelatedModel.__name__)
        self.model_fields = self.RelatedModel.__fields__.keys()
        self.foreign_field = foreign_field
        self.related_id_field = self.RelatedModel.Meta.primary_key
        if related_name:
            self.related_name = related_name
        else:
            self.related_name = re.sub(r'([a-z])([A-Z])', r'\1_\2', self.RelatedModel.__name__).lower()  # Camel case to snake case

    def set_related_data_set_name(self, related_name: str) -> None:
        """Set a custom name for the related data set."""
        self.related_name = related_name

    def render_on_clause(self) -> str:
        """Return the SQL ON clause for the relation."""
        return f"t.{self.foreign_field} = r.{self.related_id_field}"


class Prefetch:
    
    def __init__(self, dataset_name:str, queryset) -> None:
        self.dataset_name = dataset_name
        self.queryset = queryset
        self.foreign_field = None  # Foreign key from the base model
        self.id_field = None  # Foreign key from the base model
    
    def set_foreign_field(self, foreign_field:str) -> None:
        self.foreign_field = foreign_field
    
    def set_id_field(self, id_field:str) -> None:
        self.id_field = id_field


class Q:
    """Convenience object for constructing SQL WHERE clauses."""

    def __init__(self, where_clause=None, params=None, relation:Relation=None, **kwargs):
        self.relation = relation
        self.relation_key = relation.related_name + '__' if relation else None

        if where_clause:
            self.where_clause = where_clause
            self.params = params or {}
        else:
            self.secret = random.randint(0, 9999)
            conditions, self.params = [], {}
            field_idx = 0
            for key, value in kwargs.items():
                field_idx += 1
                if self.relation:
                    if self.relation_key in key:
                        key = key.replace(self.relation_key, 'r.')
                    else:
                        key = 't.' + key
                else:
                    key = 't.' + key

                if "__" in key:
                    field, op = key.split("__", 1)
                    field_name = f"{field}_{field_idx}_{self.secret}"
                    field_name = field_name.replace('.', '_')

                    try:
                        operator = OPERATORS[op]
                    except KeyError:
                        raise UnsupportedOperatorError(
                            f'Unsupported operator: "{op}". Options are: {", ".join(OPERATORS.keys())}. '
                            f'If "{field}" is a related field, use `filter_related()` to add where clauses for the related field.'
                        )

                    if operator == "IN":
                        if not isinstance(value, list):
                            raise InvalidINClauseValueError(
                                f'IN clause value for "{field}" must be supplied with a "list" type and not "{type(value).__name__}" type.'
                            )
                        if len(value) == 0:
                            raise InvalidINClauseValueError(
                                f'IN clause value for "{field}" must be supplied with a non-empty "list".'
                            )

                        sub_fields = []
                        for idx, sub_val in enumerate(value):
                            sub_fields.append(f":{field_name}_{idx}")
                            self.params[f"{field_name}_{idx}"] = sub_val

                        conditions.append(f"{field} IN ({','.join(sub_fields)})")

                    elif operator == "IS NULL":
                        if value:
                            conditions.append(f"{field} IS NULL")
                        else:
                            conditions.append(f"{field} IS NOT NULL")

                    elif operator in ("ILIKE", "LIKE"):
                        if op in ("contains", "icontains"):
                            value = f"%{value}%"
                        elif op in ("startswith", "istartswith"):
                            value = f"{value}%"
                        elif op in ("endswith", "iendswith"):
                            value = f"%{value}"
                        conditions.append(f"{field} {operator} :{field_name}")
                        self.params[f"{field_name}"] = value

                    else:
                        conditions.append(f"{field} {operator} :{field_name}")
                        self.params[f"{field_name}"] = value

                else:
                    field_name = f"{key}_{field_idx}_{self.secret}"
                    field_name = field_name.replace('.', '_')
                    conditions.append(f"{key} = :{field_name}")
                    self.params[f"{field_name}"] = value

            self.where_clause = " AND ".join(conditions)

    def __or__(self, other):
        combined_query = f"({self.where_clause} OR {other.where_clause})"
        combined_params = {**self.params, **other.params}
        return Q(where_clause=combined_query, params=combined_params, relation=self.relation)

    def __and__(self, other):
        combined_query = f"({self.where_clause} AND {other.where_clause})"
        combined_params = {**self.params, **other.params}
        return Q(where_clause=combined_query, params=combined_params, relation=self.relation)

    def __repr__(self):
        return f"{self.where_clause} {self.params}"


def async_sql_logger(func):
    """Log execution time of SQL queries when enabled."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        from .fastpg import FAST_PG  # Imported here to avoid circular import

        if FAST_PG.log_db_queries:
            async_pg_db_obj = args[0]
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time

            if elapsed_time < 1.0:
                logger.info(f"{FAST_PG.log_title}_QUERY_LT_1_SEC [{async_pg_db_obj.conn_name} {async_pg_db_obj.conn_type.value} took {elapsed_time:.4f}s]: {kwargs['query']}")
            elif elapsed_time < 5.0:
                logger.info(f"{FAST_PG.log_title}_QUERY_1_5_SEC [{async_pg_db_obj.conn_name} {async_pg_db_obj.conn_type.value} took {elapsed_time:.4f}s]: {kwargs['query']}")
            elif elapsed_time < 10.0:
                logger.info(f"{FAST_PG.log_title}_QUERY_5_10_SEC [{async_pg_db_obj.conn_name} {async_pg_db_obj.conn_type.value} took {elapsed_time:.4f}s]: {kwargs['query']}")
            else:
                logger.info(f"{FAST_PG.log_title}_QUERY_GT_10_SEC [{async_pg_db_obj.conn_name} {async_pg_db_obj.conn_type.value} took {elapsed_time:.4f}s]: {kwargs['query']}")

            return result

        return await func(*args, **kwargs)

    return wrapper
