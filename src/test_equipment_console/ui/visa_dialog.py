from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from test_equipment_console.drivers.base import (
    InstrumentConnectionError,
)
from test_equipment_console.drivers.discovery import (
    VisaResourceInfo,
    discover_visa_resources,
)


class VisaResourceDialog(QDialog):
    """Dialog for discovering and selecting a VISA resource."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Add VISA Instrument")
        self.resize(700, 520)
        self.setMinimumSize(620, 460)

        self._resources: list[VisaResourceInfo] = []

        self._build_interface()
        self._apply_styles()
        self._refresh_resources()

    @property
    def instrument_name(self) -> str:
        return self.name_input.text().strip()

    @property
    def resource_name(self) -> str:
        return self.resource_input.text().strip()

    @property
    def timeout_ms(self) -> int:
        return self.timeout_spin.value()

    @property
    def read_termination(self) -> str | None:
        return self._termination_value(
            self.read_termination_combo.currentText()
        )

    @property
    def write_termination(self) -> str | None:
        return self._termination_value(
            self.write_termination_combo.currentText()
        )

    @property
    def backend(self) -> str | None:
        backend = self.backend_input.text().strip()
        return backend or None

    def _build_interface(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 20, 22, 20)
        root_layout.setSpacing(16)

        title = QLabel("VISA Resource Discovery")
        title.setObjectName("dialogTitle")

        description = QLabel(
            "Refresh the local VISA resource list, select an instrument, "
            "and configure its communication settings."
        )
        description.setObjectName("descriptionLabel")
        description.setWordWrap(True)

        backend_layout = QHBoxLayout()
        backend_layout.setSpacing(10)

        backend_label = QLabel("VISA Backend")
        backend_label.setObjectName("fieldLabel")

        self.backend_input = QLineEdit()
        self.backend_input.setPlaceholderText(
            "Leave blank for the system VISA backend"
        )

        self.refresh_button = QPushButton("Refresh Resources")
        self.refresh_button.setObjectName("primaryButton")
        self.refresh_button.clicked.connect(
            self._refresh_resources
        )

        backend_layout.addWidget(backend_label)
        backend_layout.addWidget(
            self.backend_input,
            1,
        )
        backend_layout.addWidget(
            self.refresh_button
        )

        self.resource_list = QListWidget()
        self.resource_list.setObjectName("resourceList")
        self.resource_list.itemSelectionChanged.connect(
            self._on_resource_selected
        )
        self.resource_list.itemDoubleClicked.connect(
            self._on_resource_double_clicked
        )

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        form_layout.setHorizontalSpacing(14)
        form_layout.setVerticalSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "Example: Bench Multimeter"
        )

        self.resource_input = QLineEdit()
        self.resource_input.setPlaceholderText(
            "Example: GPIB0::10::INSTR"
        )

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(
            100,
            120_000,
        )
        self.timeout_spin.setValue(5000)
        self.timeout_spin.setSingleStep(100)
        self.timeout_spin.setSuffix(" ms")

        self.read_termination_combo = QComboBox()
        self.read_termination_combo.addItems(
            (
                r"\n",
                r"\r\n",
                r"\r",
                "None",
            )
        )

        self.write_termination_combo = QComboBox()
        self.write_termination_combo.addItems(
            (
                r"\n",
                r"\r\n",
                r"\r",
                "None",
            )
        )

        form_layout.addRow(
            "Instrument Name",
            self.name_input,
        )
        form_layout.addRow(
            "Resource Name",
            self.resource_input,
        )
        form_layout.addRow(
            "Timeout",
            self.timeout_spin,
        )
        form_layout.addRow(
            "Read Termination",
            self.read_termination_combo,
        )
        form_layout.addRow(
            "Write Termination",
            self.write_termination_combo,
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(
            self._validate_and_accept
        )
        self.button_box.rejected.connect(
            self.reject
        )

        root_layout.addWidget(title)
        root_layout.addWidget(description)
        root_layout.addLayout(backend_layout)
        root_layout.addWidget(
            self.resource_list,
            1,
        )
        root_layout.addLayout(form_layout)
        root_layout.addWidget(
            self.button_box
        )

    def _refresh_resources(self) -> None:
        self.refresh_button.setEnabled(False)
        self.resource_list.clear()
        self._resources.clear()

        self.resource_list.addItem(
            "Searching for VISA resources..."
        )

        try:
            resources = discover_visa_resources(
                backend=self.backend
            )
        except InstrumentConnectionError as exc:
            self.resource_list.clear()
            self.resource_list.addItem(
                "VISA discovery failed."
            )

            QMessageBox.critical(
                self,
                "VISA Discovery Failed",
                str(exc),
            )

            self.refresh_button.setEnabled(True)
            return

        self.resource_list.clear()
        self._resources.extend(resources)

        if not resources:
            empty_item = QListWidgetItem(
                "No VISA resources were found."
            )
            empty_item.setFlags(
                empty_item.flags()
                & ~Qt.ItemFlag.ItemIsSelectable
            )
            self.resource_list.addItem(
                empty_item
            )
        else:
            for resource in resources:
                item = QListWidgetItem(
                    resource.display_name
                )
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    resource.resource_name,
                )
                self.resource_list.addItem(item)

            self.resource_list.setCurrentRow(0)

        self.refresh_button.setEnabled(True)

    def _on_resource_selected(self) -> None:
        item = self.resource_list.currentItem()

        if item is None:
            return

        resource_name = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not resource_name:
            return

        self.resource_input.setText(
            str(resource_name)
        )

        if not self.name_input.text().strip():
            self.name_input.setText(
                self._suggest_instrument_name(
                    str(resource_name)
                )
            )

    def _on_resource_double_clicked(
        self,
        item: QListWidgetItem,
    ) -> None:
        resource_name = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not resource_name:
            return

        self._validate_and_accept()

    def _validate_and_accept(self) -> None:
        if not self.instrument_name:
            QMessageBox.warning(
                self,
                "Instrument Name Required",
                "Enter a name for the VISA instrument.",
            )
            self.name_input.setFocus()
            return

        if not self.resource_name:
            QMessageBox.warning(
                self,
                "Resource Name Required",
                "Select or enter a VISA resource name.",
            )
            self.resource_input.setFocus()
            return

        self.accept()

    @staticmethod
    def _suggest_instrument_name(
        resource_name: str,
    ) -> str:
        normalized = resource_name.upper()

        if normalized.startswith("GPIB"):
            return "GPIB Instrument"

        if normalized.startswith("USB"):
            return "USB Instrument"

        if normalized.startswith("TCPIP"):
            return "Network Instrument"

        if normalized.startswith("ASRL"):
            return "Serial Instrument"

        if normalized.startswith("PXI"):
            return "PXI Instrument"

        if normalized.startswith("VXI"):
            return "VXI Instrument"

        return "VISA Instrument"

    @staticmethod
    def _termination_value(
        display_value: str,
    ) -> str | None:
        mapping: dict[str, str | None] = {
            r"\n": "\n",
            r"\r\n": "\r\n",
            r"\r": "\r",
            "None": None,
        }

        return mapping[display_value]

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background-color: #eef1f4;
            }

            QWidget {
                color: #1f2933;
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QLabel#dialogTitle {
                color: #263746;
                font-size: 18pt;
                font-weight: 700;
            }

            QLabel#descriptionLabel {
                color: #5f6f7a;
                font-size: 9pt;
            }

            QLabel#fieldLabel {
                color: #52616d;
                font-size: 9pt;
                font-weight: 600;
            }

            QLineEdit,
            QComboBox,
            QSpinBox {
                min-height: 36px;
                padding: 0 9px;
                background-color: #ffffff;
                border: 1px solid #b9c4cc;
                border-radius: 5px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus {
                border: 2px solid #b36b36;
            }

            QListWidget#resourceList {
                background-color: #ffffff;
                border: 1px solid #cbd4da;
                border-radius: 6px;
                padding: 6px;
                alternate-background-color: #f5f7f8;
            }

            QListWidget#resourceList::item {
                min-height: 34px;
                padding: 4px 8px;
                border-radius: 4px;
            }

            QListWidget#resourceList::item:selected {
                color: #ffffff;
                background-color: #52616d;
            }

            QListWidget#resourceList::item:hover:!selected {
                background-color: #e8ecef;
            }

            QPushButton {
                min-height: 36px;
                padding: 0 14px;
                background-color: #e8ecef;
                border: 1px solid #bcc6cd;
                border-radius: 5px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #dce3e8;
            }

            QPushButton#primaryButton {
                color: #ffffff;
                background-color: #b36b36;
                border-color: #9a582a;
            }

            QPushButton#primaryButton:hover {
                background-color: #9f5d30;
            }
            """
        )