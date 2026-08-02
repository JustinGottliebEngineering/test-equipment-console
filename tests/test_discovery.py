from __future__ import annotations

from typing import Any

import pyvisa
import pytest

from test_equipment_console.drivers.base import (
    InstrumentConnectionError,
)
from test_equipment_console.drivers.discovery import (
    VisaResourceInfo,
    discover_visa_resources,
)


class FakeDiscoveryResourceManager:
    def __init__(
        self,
        resources: tuple[str, ...] = (),
    ) -> None:
        self.resources = resources
        self.closed = False
        self.list_error: Exception | None = None
        self.close_error: Exception | None = None

    def list_resources(self) -> tuple[str, ...]:
        if self.list_error is not None:
            raise self.list_error

        return self.resources

    def close(self) -> None:
        if self.close_error is not None:
            raise self.close_error

        self.closed = True


def install_fake_resource_manager(
    monkeypatch: pytest.MonkeyPatch,
    manager: FakeDiscoveryResourceManager,
) -> list[Any]:
    calls: list[Any] = []

    def fake_resource_manager(
        backend: str | None = None,
    ) -> FakeDiscoveryResourceManager:
        calls.append(backend)
        return manager

    monkeypatch.setattr(
        pyvisa,
        "ResourceManager",
        fake_resource_manager,
    )

    return calls


def test_visa_resource_info_display_name() -> None:
    resource = VisaResourceInfo(
        resource_name="GPIB0::10::INSTR",
        interface_type="GPIB",
    )

    assert resource.display_name == (
        "GPIB0::10::INSTR (GPIB)"
    )


def test_discovery_returns_empty_tuple(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDiscoveryResourceManager()

    calls = install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    resources = discover_visa_resources()

    assert resources == ()
    assert calls == [None]
    assert manager.closed


def test_discovery_returns_sorted_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDiscoveryResourceManager(
        resources=(
            "USB0::0x1234::0x5678::SN001::INSTR",
            "GPIB0::13::INSTR",
            "ASRL3::INSTR",
            "TCPIP0::192.168.1.50::INSTR",
        )
    )

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    resources = discover_visa_resources()

    assert tuple(
        resource.resource_name
        for resource in resources
    ) == (
        "ASRL3::INSTR",
        "GPIB0::13::INSTR",
        "TCPIP0::192.168.1.50::INSTR",
        "USB0::0x1234::0x5678::SN001::INSTR",
    )

    assert tuple(
        resource.interface_type
        for resource in resources
    ) == (
        "Serial",
        "GPIB",
        "TCP/IP",
        "USB",
    )


def test_discovery_classifies_supported_interfaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDiscoveryResourceManager(
        resources=(
            "GPIB0::5::INSTR",
            "USB0::1::2::3::INSTR",
            "TCPIP0::HOST::INSTR",
            "ASRL4::INSTR",
            "PXI0::1::INSTR",
            "VXI0::2::INSTR",
            "CUSTOM::RESOURCE",
        )
    )

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    resources = discover_visa_resources()

    interface_types = {
        resource.resource_name: resource.interface_type
        for resource in resources
    }

    assert interface_types["GPIB0::5::INSTR"] == "GPIB"
    assert interface_types["USB0::1::2::3::INSTR"] == "USB"
    assert interface_types["TCPIP0::HOST::INSTR"] == "TCP/IP"
    assert interface_types["ASRL4::INSTR"] == "Serial"
    assert interface_types["PXI0::1::INSTR"] == "PXI"
    assert interface_types["VXI0::2::INSTR"] == "VXI"
    assert interface_types["CUSTOM::RESOURCE"] == "Other"


def test_discovery_is_case_insensitive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDiscoveryResourceManager(
        resources=(
            "gpib0::8::instr",
            "usb0::1::2::3::instr",
        )
    )

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    resources = discover_visa_resources()

    interface_types = {
        resource.resource_name: resource.interface_type
        for resource in resources
    }

    assert interface_types["gpib0::8::instr"] == "GPIB"
    assert interface_types["usb0::1::2::3::instr"] == "USB"


def test_discovery_uses_requested_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDiscoveryResourceManager()

    calls = install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    discover_visa_resources(
        backend="@py",
    )

    assert calls == ["@py"]


def test_discovery_wraps_visa_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDiscoveryResourceManager()
    manager.list_error = pyvisa.errors.VisaIOError(
        pyvisa.constants.StatusCode.error_system_error
    )

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    with pytest.raises(
        InstrumentConnectionError,
        match="VISA resource discovery failed",
    ):
        discover_visa_resources()

    assert manager.closed


def test_discovery_wraps_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDiscoveryResourceManager()
    manager.list_error = ValueError(
        "Invalid VISA backend."
    )

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    with pytest.raises(
        InstrumentConnectionError,
        match="Invalid VISA backend",
    ):
        discover_visa_resources()

    assert manager.closed


def test_discovery_ignores_close_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDiscoveryResourceManager(
        resources=(
            "GPIB0::13::INSTR",
        )
    )
    manager.close_error = OSError(
        "Close failed."
    )

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    resources = discover_visa_resources()

    assert len(resources) == 1
    assert resources[0].resource_name == (
        "GPIB0::13::INSTR"
    )