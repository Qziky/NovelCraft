from novel_cli.commands.edit import ACTION_PROMPTS


def test_action_prompts_keys():
    expected = {"polish", "shorten", "expand", "rewrite"}
    assert set(ACTION_PROMPTS.keys()) == expected


def test_action_prompts_values_are_strings():
    for key, value in ACTION_PROMPTS.items():
        assert isinstance(value, str)
        assert len(value) > 0


def test_action_prompts_contain_chinese():
    for key, value in ACTION_PROMPTS.items():
        assert any("\u4e00" <= c <= "\u9fff" for c in value), f"{key} prompt should contain Chinese characters"
