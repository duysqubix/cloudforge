import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from .tokenizer import Tokenizer, UnparsedTokensError


@pytest.fixture
def test_files(tmpdir):
    tmpdir = Path(tmpdir)
    test_files = {
        tmpdir / "test1.txt": "Hello, {{__name__}}!",
        tmpdir / "test2.txt": "{{__name__}}, how are you?",
        tmpdir / "subdir/test3.txt": "{{__name__}}",
    }
    for path, content in test_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    yield tmpdir, test_files


def test_tokenizer_replace_tokens(test_files):
    root_dir, files = test_files
    tokenizer = Tokenizer(root_dir=root_dir, ext="txt")
    tokenizer.read_root()
    tokens = {"name": "Alice"}
    parsed_tree = tokenizer.replace_tokens(tokens)
    assert parsed_tree[str(root_dir / "test1.txt")] == "Hello, Alice!"
    assert parsed_tree[str(root_dir / "test2.txt")] == "Alice, how are you?"
    assert parsed_tree[str(root_dir / "subdir/test3.txt")] == "Alice"


def test_tokenizer_validate_tokens(test_files):
    root_dir, files = test_files
    tokenizer = Tokenizer(root_dir=root_dir, ext="txt")
    tokenizer.read_root()
    tokens = {"name": "Alice"}
    parsed_tree = tokenizer.replace_tokens(tokens)
    unused_tokens = tokenizer.validate_tokens(parsed_tree)
    assert unused_tokens == set()


def test_tokenizer_replace_and_validate_tokens(test_files):
    root_dir, files = test_files
    tokenizer = Tokenizer(root_dir=root_dir, ext="txt")
    tokenizer.read_root()
    tokens = {"name": "Alice"}
    parsed_tree = tokenizer.replace_and_validate_tokens(tokens)
    assert parsed_tree[str(root_dir / "test1.txt")] == "Hello, Alice!"
    assert parsed_tree[str(root_dir / "test2.txt")] == "Alice, how are you?"
    assert parsed_tree[str(root_dir / "subdir/test3.txt")] == "Alice"
    with pytest.raises(UnparsedTokensError):
        tokenizer.replace_and_validate_tokens({})


def test_tokenizer_dump_to(test_files):
    root_dir, files = test_files
    tokenizer = Tokenizer(root_dir=root_dir, ext="txt")
    tokenizer.read_root()
    tokens = {"name": "Alice"}
    parsed_tree = tokenizer.replace_tokens(tokens)
    with TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "output"
        tokenizer.dump_to(parsed_tree, target_dir, unique=False)
        assert (target_dir / "test1.txt").read_text() == "Hello, Alice!"
        assert (target_dir / "test2.txt").read_text() == "Alice, how are you?"
        assert (target_dir / "subdir/test3.txt").read_text() == "Alice"
