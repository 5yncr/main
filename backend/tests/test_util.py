from unittest import mock

from syncr_backend.util.fileio_util import walk_with_ignore


@mock.patch('syncr_backend.util.fileio_util.os.path.relpath', autospec=True)
@mock.patch('syncr_backend.util.fileio_util.os.walk', autospec=True)
def test_walk_with_ignore(
    mock_os_walk: mock.Mock, mock_relpath: mock.Mock,
) -> None:
    mock_relpath.return_value = "123/"
    mock_os_walk.side_effect = [[]]
    assert list(walk_with_ignore('foo', ignore=[])) == []

    mock_relpath.side_effect = ['foo']
    mock_os_walk.side_effect = [
        [('foo', ['bar', 'baz'], ['qux', 'abc'])],
    ]
    assert list(
        walk_with_ignore('/foo/bar/123', ignore=[]),
    ) == [('foo', 'qux'), ('foo', 'abc')]

    mock_relpath.side_effect = ['foo', '.5yncr']
    mock_os_walk.side_effect = [[
        ('foo', ['bar', 'baz'], ['qux', 'abc']),
        ('.5yncr', [], ['drop', 'file']),
    ]]
    assert list(
        walk_with_ignore('/foo/bar/123', ignore=[]),
    ) == [('foo', 'qux'), ('foo', 'abc')]

    mock_relpath.side_effect = ['foo', 'wfoo', '.5yncr']
    mock_os_walk.side_effect = [[
        ('foo', ['bar', 'baz'], ['qux', 'abc']),
        ('wfoo', ['bar', 'baz'], ['qux', 'abc']),
        ('.5yncr', [], ['drop', 'file']),
    ]]
    assert list(
        walk_with_ignore('/foo/bar/123', ignore=['wfoo']),
    ) == [('foo', 'qux'), ('foo', 'abc')]

    mock_relpath.side_effect = ['foo', 'wfoo', '.5yncr']
    mock_os_walk.side_effect = [[
        ('foo', ['bar', 'baz'], ['qux', 'abc']),
        ('wfoo', ['bar', 'baz'], ['qux', 'abc']),
        ('.5yncr', [], ['drop', 'file']),
    ]]
    assert list(
        walk_with_ignore('/foo/bar/123', ignore=['wfoo', 'abc']),
    ) == [('foo', 'qux')]
