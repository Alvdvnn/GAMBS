from gambs import config


def test_starting_balance_is_1000():
    assert config.STARTING_BALANCE == 1000.0


def test_house_edge_is_positive_fraction():
    assert 0.0 < config.HOUSE_EDGE < 0.2


def test_palette_has_required_keys():
    for key in ("gold", "gamble", "earn", "success", "danger", "info"):
        assert key in config.COLORS
        assert config.COLORS[key].startswith("#")


def test_save_path_under_data_dir():
    assert config.SAVE_PATH.parent == config.DATA_DIR
    assert config.SAVE_PATH.name == "save.json"
