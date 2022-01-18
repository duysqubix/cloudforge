import uuid
from pathlib import Path
from unittest import TestCase

from utils.utils import TokenReplacer


class TokenReplacerTestCase(TestCase):
    def setUp(self):
        self.source_dir = Path("/tmp/validator-terraform-source-%s" %
                               str(uuid.uuid4()))
        self.sink_dir = Path("/tmp/validator-terraform-sink-%s" %
                             str(uuid.uuid4()))

        self.source_dir.mkdir(exist_ok=True)
        self.sink_dir.mkdir(exist_ok=True)

    def tearDown(self):
        self.source_dir.rmdir()
        self.sink_dir.rmdir()

    def test_replace_token_all(self):
        prefix = "__"
        suffix = "__"

        token_definitions = {
            "test1": "converted1",
            "test2": "converted2",
            "test3": "converted3",
        }
        content = """
        __test1__
        __test2__
        __test3__
        test4
        """.strip()

        tokenizer = TokenReplacer(self.source_dir)
        tokenizer.tree = {"dummy_path": content}
        tokenizer.replace_tokens(token_definitions,
                                 prefix=prefix,
                                 suffix=suffix)

        result = "__" not in tokenizer.tree['dummy_path']
        self.assertTrue(result)

    def test_replace_token_all_mixed_fixs(self):
        prefix = "##"
        suffix = "__"

        token_definitions = {
            "test1": "converted1",
            "test2": "converted2",
            "test3": "converted3",
        }
        content = """
        ##test1__
        ##test2__
        ##test3__
        test4
        """.strip()

        tokenizer = TokenReplacer(self.source_dir)
        tokenizer.tree = {"dummy_path": content}
        tokenizer.replace_tokens(token_definitions,
                                 prefix=prefix,
                                 suffix=suffix)

        result = "__" not in tokenizer.tree['dummy_path']
        self.assertTrue(result)

    def test_replace_token_missing_tokens(self):
        prefix = "__"
        suffix = "__"

        token_definitions = {
            "test1": "converted1",
            "test2": "converted2",
            "test3": "converted3",
        }
        content = """
        __test1__
        __test2__
        __test3__
        __test4__
        """.strip()

        tokenizer = TokenReplacer(self.source_dir)
        tokenizer.tree = {"dummy_path": content}
        tokenizer.replace_tokens(token_definitions,
                                 prefix=prefix,
                                 suffix=suffix)

        missing_tokens = tokenizer.find_missing_tokens()
        self.assertTrue(bool(missing_tokens))

    def test_replace_token_no_missing_tokens(self):
        prefix = "__"
        suffix = "__"

        token_definitions = {
            "test1": "converted1",
            "test2": "converted2",
            "test3": "converted3",
            "test4": "converted4"
        }
        content = """
            __test1__
            __test2__
            __test3__
            __test4__
            """.strip()

        tokenizer = TokenReplacer(self.source_dir)
        tokenizer.tree = {"dummy_path": content}
        tokenizer.replace_tokens(token_definitions,
                                 prefix=prefix,
                                 suffix=suffix)

        missing_tokens = tokenizer.find_missing_tokens()
        self.assertFalse(bool(missing_tokens))
