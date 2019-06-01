from typing import Iterator, TypeVar

T = TypeVar('T')


def repeat_forever(it: Iterator[T]) -> Iterator[T]:
    items = list(it)
    while True:
        yield from items
