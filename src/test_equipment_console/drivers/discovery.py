from __future__ import annotations

from dataclasses import dataclass

import pyvisa

from test_equipment_console.drivers.base import (
    InstrumentConnectionError,
)


@dataclass(frozen=True)
class VisaResourceInfo:
    """One VISA resource discovered on the local system."""

    resource_name: str
    interface_type: str

    @property
    def display_name(self) -> str:
        return f"{self.resource_name} ({self.interface_type})"


def discover_visa_resources(
    *,
    backend: str | None = None,
) -> tuple[VisaResourceInfo, ...]:
    """Return the VISA resources currently visible to PyVISA."""

    manager: pyvisa.ResourceManager | None = None

    try:
        if backend:
            manager = pyvisa.ResourceManager(backend)
        else:
            manager = pyvisa.ResourceManager()

        resource_names = manager.list_resources()

    except (
        pyvisa.errors.VisaIOError,
        OSError,
        ValueError,
    ) as exc:
        raise InstrumentConnectionError(
            f"VISA resource discovery failed: {exc}"
        ) from exc

    finally:
        if manager is not None:
            try:
                manager.close()
            except Exception:
                pass

    resources = [
        VisaResourceInfo(
            resource_name=resource_name,
            interface_type=_get_interface_type(
                resource_name
            ),
        )
        for resource_name in resource_names
    ]

    return tuple(
        sorted(
            resources,
            key=lambda resource: resource.resource_name,
        )
    )


def _get_interface_type(
    resource_name: str,
) -> str:
    normalized = resource_name.upper()

    if normalized.startswith("GPIB"):
        return "GPIB"

    if normalized.startswith("USB"):
        return "USB"

    if normalized.startswith("TCPIP"):
        return "TCP/IP"

    if normalized.startswith("ASRL"):
        return "Serial"

    if normalized.startswith("PXI"):
        return "PXI"

    if normalized.startswith("VXI"):
        return "VXI"

    return "Other"