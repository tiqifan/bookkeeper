from datetime import datetime, timedelta

import pytest

from bookkeeper.repository.memory_repository import MemoryRepository
from bookkeeper.models.budget import Budget


@pytest.fixture
def repo():
    return MemoryRepository()


def test_create_with_full_args_list():
    b = Budget(amount=100, category=1, length=7, start_date=datetime.now(),
               end_date=(datetime.now()+timedelta(days=7)), pk=1)
    assert b.amount == 100
    assert b.category == 1
    assert b.length == 7


def test_create_brief():
    b = Budget(100, 1, 7)
    assert b.amount == 100
    assert b.category == 1
    assert b.length == 7
    assert b.end_date - b.start_date == timedelta(days=b.length)


def test_can_add_to_repo(repo):
    b = Budget(100, 1, 7)
    pk = repo.add(b)
    assert b.pk == pk
