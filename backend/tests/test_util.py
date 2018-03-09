from unittest import mock

from syncr_backend.util import walk_with_ignore


@mock.patch('syncr_backend.util.os.walk', autospec=True)
def test_walk_with_ignore(mock_os_walk):
    mock_os_walk.side_effect = [[]]
    assert list(walk_with_ignore('foo', ignore=[])) == []

    mock_os_walk.side_effect = [
        [('foo', ['bar', 'baz'], ['qux', 'abc'])],
    ]
    assert list(
        walk_with_ignore('123', ignore=[]),
    ) == [('foo', 'qux'), ('foo', 'abc')]

    mock_os_walk.side_effect = [[
        ('foo', ['bar', 'baz'], ['qux', 'abc']),
        ('.5yncr', [], ['drop', 'file']),
    ]]
    assert list(
        walk_with_ignore('123', ignore=[]),
    ) == [('foo', 'qux'), ('foo', 'abc')]

    mock_os_walk.side_effect = [[
        ('foo', ['bar', 'baz'], ['qux', 'abc']),
        ('wfoo', ['bar', 'baz'], ['qux', 'abc']),
        ('.5yncr', [], ['drop', 'file']),
    ]]
    assert list(
        walk_with_ignore('123', ignore=['wfoo']),
    ) == [('foo', 'qux'), ('foo', 'abc')]

    mock_os_walk.side_effect = [[
        ('foo', ['bar', 'baz'], ['qux', 'abc']),
        ('wfoo', ['bar', 'baz'], ['qux', 'abc']),
        ('.5yncr', [], ['drop', 'file']),
    ]]
    assert list(
        walk_with_ignore('123', ignore=['wfoo', 'abc']),
    ) == [('foo', 'qux')]
