"""This module contains custom classes based on the schema class from DataJoint"""
from typing import Optional, Dict, Any

from datajoint.connection import Connection
from datajoint.schemas import Schema


class LazySchema:
    """A proxy around an instance of the DataJoint schema class that creates said instance in a lazy way.

    This class creates an instance of the DataJoint schema class if the "initialize" method is called or a non-existing
    attribute is accessed. After creation all non-existing attributes will be looked up on the created instance.

    Attributes:
        schema_kwargs: A dictionary containing keyword arguments and their values. It is used to create an instance
            of the DataJoint schema class when needed.
    """

    _schema_cls = Schema

    def __init__(
        self,
        schema_name: str,
        context: Optional[Dict] = None,
        *,
        connection: Optional[Connection] = None,
        create_schema: Optional[bool] = True,
        create_tables: Optional[bool] = True
    ) -> None:
        self.schema_kwargs = dict(
            schema_name=schema_name,
            context=context,
            connection=connection,
            create_schema=create_schema,
            create_tables=create_tables,
        )
        self._is_initialized = False
        self._schema: Optional[Schema] = None

    def initialize(self) -> None:
        """Fully initializes the lazy schema."""
        if not self._is_initialized:
            self._initialize()

    def _initialize(self) -> None:
        self._schema = self._schema_cls(**self.schema_kwargs)
        self._is_initialized = True

    def __getattr__(self, item: str) -> Any:
        self.initialize()
        return getattr(self._schema, item)
