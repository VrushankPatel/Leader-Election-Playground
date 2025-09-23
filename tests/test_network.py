import pytest

from lep.network.controller import NetworkController


def test_network_controller_partition():
    controller = NetworkController()
    assert not controller.is_partitioned(1, 2)
    controller.set_partition(1, 2, True)
    assert controller.is_partitioned(1, 2)
    controller.set_partition(1, 2, False)
    assert not controller.is_partitioned(1, 2)


def test_network_controller_delay():
    controller = NetworkController()
    assert controller.get_delay(1, 2) == 0.0
    controller.set_delay(1, 2, 100.0)
    assert controller.get_delay(1, 2) == 100.0


def test_network_controller_drop():
    controller = NetworkController(seed=0)
    controller.set_drop_rate(1, 2, 1.0)  # Always drop
    assert controller.should_drop(1, 2)
    controller.set_drop_rate(1, 2, 0.0)  # Never drop
    assert not controller.should_drop(1, 2)