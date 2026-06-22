from gambs.save import default_save
from gambs.games.outcome import apply_net


def test_apply_net_win_updates_balance_and_stats():
    save = default_save()
    apply_net(save, bet=100.0, net=200.0)
    assert save.balance == 1200.0
    assert save.stats.games_played == 1
    assert save.stats.total_wagered == 100.0
    assert save.stats.total_won == 300.0  # gross return = bet + net


def test_apply_net_loss_does_not_count_total_won():
    save = default_save()
    apply_net(save, bet=100.0, net=-100.0)
    assert save.balance == 900.0
    assert save.stats.total_won == 0.0
    assert save.stats.games_played == 1


def test_apply_net_push_is_neutral():
    save = default_save()
    apply_net(save, bet=100.0, net=0.0)
    assert save.balance == 1000.0
    assert save.stats.games_played == 1
    assert save.stats.total_won == 0.0
    assert save.stats.total_wagered == 100.0
