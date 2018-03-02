import fnmatch
import os
from typing import Iterator
from typing import List
from typing import Tuple


def walk_with_ignore(
    path: str, ignore: List[str],
) -> Iterator[Tuple[str, str]]:
    """Walks the files in a directory, while filtering anything that should be
    ignored.  Implemented on top of os.walk, but instead returns an iterator
    over (dirpath, filename)

    :param path: The path to walk
    :param ignore: Patterns to ignore
    :return: An iterator of (dirpath, filename) that are in path but not ignore
    """
    for (dirpath, _, filenames) in os.walk(path):
        for name in filenames:
            if any([fnmatch.fnmatch(name, i) for i in ignore]):
                continue
            full_name = os.path.join(dirpath, name)
            if any([fnmatch.fnmatch(full_name, i) for i in ignore]):
                continue
            yield (dirpath, name)
