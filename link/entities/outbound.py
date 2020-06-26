from typing import List

from .repository import Repository
from .domain import Address
from .local import LocalRepository


class OutboundRepository(Repository):
    def __init__(self, address: Address, local_repo: LocalRepository) -> None:
        super().__init__(address)
        self.local_repo = local_repo

    def delete(self, identifiers: List[str]) -> None:
        for identifier in identifiers:
            if identifier in self.local_repo:
                raise RuntimeError(f"Can't delete entity that is present in local repository. ID: {identifier}")
            if self[identifier].deletion_requested:
                raise RuntimeError(f"Can't delete entity that had its deletion requested. ID: {identifier}")
        super().delete(identifiers)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.address}, {self.local_repo})"
