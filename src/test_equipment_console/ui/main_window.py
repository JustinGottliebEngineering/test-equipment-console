from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from test_equipment_console.drivers.base import (
    BaseInstrument,
    ConnectionState,
    InstrumentError,
)
from test_equipment_console.simulators.frequency_counter import (
    SimulatedFrequencyCounter,
)
from test_equipment_console.simulators.power_supply import (
    SimulatedPowerSupply,
)


class MainWindow(QMainWindow):
    """Main window for the Test Equipment Communication Console."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(
            "Test Equipment Communication Console"
        )
        self.resize(1100, 720)
        self.setMinimumSize(900, 600)

        self._instruments: dict[str, BaseInstrument] = {
            "Simulated Frequency Counter": (
                SimulatedFrequencyCounter()
            ),
            "Simulated Power Supply": (
                SimulatedPowerSupply()
            ),
        }

        self._active_instrument: BaseInstrument | None = None

        self._build_interface()
        self._apply_styles()
        self._load_selected_instrument()

    def _build_interface(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(24, 20, 24, 24)
        root_layout.setSpacing(18)

        root_layout.addWidget(
            self._build_header()
        )

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        content_layout.addWidget(
            self._build_instrument_panel(),
            0,
        )
        content_layout.addWidget(
            self._build_console_panel(),
            1,
        )

        root_layout.addLayout(content_layout, 1)

        self.statusBar().showMessage(
            "Ready"
        )

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("headerFrame")

        layout = QVBoxLayout(header)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(4)

        title = QLabel(
            "Test Equipment Communication Console"
        )
        title.setObjectName("titleLabel")

        subtitle = QLabel(
            "Desktop instrument control, command execution, "
            "and measurement monitoring"
        )
        subtitle.setObjectName("subtitleLabel")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        return header

    def _build_instrument_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panelFrame")
        panel.setMinimumWidth(330)
        panel.setMaximumWidth(390)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        section_title = QLabel(
            "Instrument"
        )
        section_title.setObjectName("sectionTitle")

        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems(
            self._instruments.keys()
        )
        self.instrument_combo.currentTextChanged.connect(
            self._on_instrument_selection_changed
        )

        connection_layout = QHBoxLayout()
        connection_layout.setSpacing(10)

        self.connect_button = QPushButton(
            "Connect"
        )
        self.connect_button.setObjectName(
            "primaryButton"
        )
        self.connect_button.clicked.connect(
            self._connect_instrument
        )

        self.disconnect_button = QPushButton(
            "Disconnect"
        )
        self.disconnect_button.clicked.connect(
            self._disconnect_instrument
        )
        self.disconnect_button.setEnabled(False)

        connection_layout.addWidget(
            self.connect_button
        )
        connection_layout.addWidget(
            self.disconnect_button
        )

        status_title = QLabel(
            "Connection Status"
        )
        status_title.setObjectName("fieldLabel")

        self.connection_status_label = QLabel(
            "Disconnected"
        )
        self.connection_status_label.setObjectName(
            "statusDisconnected"
        )
        self.connection_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        identity_title = QLabel(
            "Instrument Identity"
        )
        identity_title.setObjectName("fieldLabel")

        identity_frame = QFrame()
        identity_frame.setObjectName(
            "identityFrame"
        )

        identity_layout = QGridLayout(
            identity_frame
        )
        identity_layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )
        identity_layout.setHorizontalSpacing(12)
        identity_layout.setVerticalSpacing(10)

        self.manufacturer_value = QLabel("—")
        self.model_value = QLabel("—")
        self.serial_value = QLabel("—")
        self.firmware_value = QLabel("—")
        self.resource_value = QLabel("—")
        self.resource_value.setWordWrap(True)

        identity_rows = (
            (
                "Manufacturer",
                self.manufacturer_value,
            ),
            (
                "Model",
                self.model_value,
            ),
            (
                "Serial Number",
                self.serial_value,
            ),
            (
                "Firmware",
                self.firmware_value,
            ),
            (
                "Resource",
                self.resource_value,
            ),
        )

        for row, (
            label_text,
            value_label,
        ) in enumerate(identity_rows):
            label = QLabel(label_text)
            label.setObjectName(
                "identityNameLabel"
            )

            value_label.setObjectName(
                "identityValueLabel"
            )
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            identity_layout.addWidget(
                label,
                row,
                0,
            )
            identity_layout.addWidget(
                value_label,
                row,
                1,
            )

        identity_layout.setColumnStretch(
            1,
            1,
        )

        layout.addWidget(section_title)
        layout.addWidget(
            self.instrument_combo
        )
        layout.addLayout(connection_layout)
        layout.addWidget(status_title)
        layout.addWidget(
            self.connection_status_label
        )
        layout.addWidget(identity_title)
        layout.addWidget(identity_frame)
        layout.addItem(
            QSpacerItem(
                0,
                0,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        )

        return panel

    def _build_console_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panelFrame")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        top_layout = QHBoxLayout()

        section_title = QLabel(
            "Command Console"
        )
        section_title.setObjectName(
            "sectionTitle"
        )

        self.clear_button = QPushButton(
            "Clear Log"
        )
        self.clear_button.clicked.connect(
            self._clear_log
        )

        top_layout.addWidget(section_title)
        top_layout.addStretch()
        top_layout.addWidget(
            self.clear_button
        )

        command_help = QLabel(
            "Enter a SCPI-style command. Commands ending in "
            "\"?\" are sent as queries."
        )
        command_help.setObjectName(
            "helpLabel"
        )
        command_help.setWordWrap(True)

        command_layout = QHBoxLayout()
        command_layout.setSpacing(10)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText(
            "Example: *IDN?, INPUT ON, "
            "VOLTAGE 12, MEASURE:VOLTAGE?"
        )
        self.command_input.setEnabled(False)
        self.command_input.returnPressed.connect(
            self._send_command
        )

        self.send_button = QPushButton(
            "Send"
        )
        self.send_button.setObjectName(
            "primaryButton"
        )
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(
            self._send_command
        )

        command_layout.addWidget(
            self.command_input,
            1,
        )
        command_layout.addWidget(
            self.send_button,
        )

        self.console_output = QTextEdit()
        self.console_output.setObjectName(
            "consoleOutput"
        )
        self.console_output.setReadOnly(True)
        self.console_output.setLineWrapMode(
            QTextEdit.LineWrapMode.NoWrap
        )

        console_font = QFont(
            "Consolas"
        )
        console_font.setStyleHint(
            QFont.StyleHint.Monospace
        )
        console_font.setPointSize(10)

        self.console_output.setFont(
            console_font
        )

        layout.addLayout(top_layout)
        layout.addWidget(command_help)
        layout.addLayout(command_layout)
        layout.addWidget(
            self.console_output,
            1,
        )

        return panel

    def _load_selected_instrument(self) -> None:
        selected_name = (
            self.instrument_combo.currentText()
        )

        self._active_instrument = (
            self._instruments[selected_name]
        )

        self._clear_identity()
        self.resource_value.setText(
            self._active_instrument.resource_name
        )
        self._update_connection_controls()

    def _on_instrument_selection_changed(
        self,
        selected_name: str,
    ) -> None:
        if (
            self._active_instrument is not None
            and self._active_instrument.is_connected
        ):
            try:
                self._active_instrument.disconnect()
            except InstrumentError as exc:
                self._append_error(
                    str(exc)
                )

        self._active_instrument = (
            self._instruments[selected_name]
        )

        self._clear_identity()
        self.resource_value.setText(
            self._active_instrument.resource_name
        )
        self._update_connection_controls()

        self._append_system_message(
            f"Selected {selected_name}."
        )

    def _connect_instrument(self) -> None:
        instrument = self._require_active_instrument()

        try:
            instrument.connect()
            identity = instrument.identify()
        except InstrumentError as exc:
            self._append_error(
                str(exc)
            )
            self._update_connection_controls()
            return

        self.manufacturer_value.setText(
            identity.manufacturer
        )
        self.model_value.setText(
            identity.model
        )
        self.serial_value.setText(
            identity.serial_number
        )
        self.firmware_value.setText(
            identity.firmware_version
        )
        self.resource_value.setText(
            instrument.resource_name
        )

        self._append_system_message(
            f"Connected to {identity.display_name} "
            f"at {instrument.resource_name}."
        )

        self.statusBar().showMessage(
            f"Connected to {identity.display_name}"
        )

        self._update_connection_controls()
        self.command_input.setFocus()

    def _disconnect_instrument(self) -> None:
        instrument = self._require_active_instrument()

        try:
            instrument.disconnect()
        except InstrumentError as exc:
            self._append_error(
                str(exc)
            )
            self._update_connection_controls()
            return

        self._append_system_message(
            f"Disconnected from {instrument.name}."
        )

        self.statusBar().showMessage(
            "Disconnected"
        )

        self._clear_identity()
        self.resource_value.setText(
            instrument.resource_name
        )
        self._update_connection_controls()

    def _send_command(self) -> None:
        instrument = self._require_active_instrument()

        command = self.command_input.text().strip()

        if not command:
            return

        if not instrument.is_connected:
            QMessageBox.warning(
                self,
                "Instrument Not Connected",
                "Connect to an instrument before sending commands.",
            )
            return

        self._append_command(
            command
        )

        try:
            if command.endswith("?"):
                response = instrument.query(
                    command
                )
                self._append_response(
                    response
                )
            else:
                instrument.write(
                    command
                )
                self._append_response(
                    "OK"
                )
        except InstrumentError as exc:
            self._append_error(
                str(exc)
            )

        self.command_input.clear()
        self.command_input.setFocus()

    def _clear_log(self) -> None:
        self.console_output.clear()

    def _update_connection_controls(self) -> None:
        instrument = self._active_instrument

        is_connected = bool(
            instrument
            and instrument.is_connected
        )

        self.connect_button.setEnabled(
            not is_connected
        )
        self.disconnect_button.setEnabled(
            is_connected
        )
        self.command_input.setEnabled(
            is_connected
        )
        self.send_button.setEnabled(
            is_connected
        )
        self.instrument_combo.setEnabled(
            not is_connected
        )

        if instrument is None:
            self.connection_status_label.setText(
                "No Instrument"
            )
            self.connection_status_label.setObjectName(
                "statusDisconnected"
            )
        elif (
            instrument.state
            == ConnectionState.CONNECTED
        ):
            self.connection_status_label.setText(
                "Connected"
            )
            self.connection_status_label.setObjectName(
                "statusConnected"
            )
        elif (
            instrument.state
            == ConnectionState.ERROR
        ):
            self.connection_status_label.setText(
                "Error"
            )
            self.connection_status_label.setObjectName(
                "statusError"
            )
        else:
            self.connection_status_label.setText(
                "Disconnected"
            )
            self.connection_status_label.setObjectName(
                "statusDisconnected"
            )

        self.connection_status_label.style().unpolish(
            self.connection_status_label
        )
        self.connection_status_label.style().polish(
            self.connection_status_label
        )

    def _clear_identity(self) -> None:
        self.manufacturer_value.setText("—")
        self.model_value.setText("—")
        self.serial_value.setText("—")
        self.firmware_value.setText("—")

    def _append_command(
        self,
        command: str,
    ) -> None:
        self._append_console_line(
            prefix="TX",
            message=command,
        )

    def _append_response(
        self,
        response: str,
    ) -> None:
        self._append_console_line(
            prefix="RX",
            message=response,
        )

    def _append_system_message(
        self,
        message: str,
    ) -> None:
        self._append_console_line(
            prefix="SYS",
            message=message,
        )

    def _append_error(
        self,
        message: str,
    ) -> None:
        self._append_console_line(
            prefix="ERR",
            message=message,
        )

        self.statusBar().showMessage(
            message,
            5000,
        )

    def _append_console_line(
        self,
        *,
        prefix: str,
        message: str,
    ) -> None:
        timestamp = datetime.now().strftime(
            "%H:%M:%S.%f"
        )[:-3]

        self.console_output.append(
            f"[{timestamp}] {prefix:<3} | {message}"
        )

        scrollbar = (
            self.console_output.verticalScrollBar()
        )
        scrollbar.setValue(
            scrollbar.maximum()
        )

    def _require_active_instrument(
        self,
    ) -> BaseInstrument:
        if self._active_instrument is None:
            raise RuntimeError(
                "No active instrument is selected."
            )

        return self._active_instrument

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        for instrument in self._instruments.values():
            if not instrument.is_connected:
                continue

            try:
                instrument.disconnect()
            except InstrumentError:
                pass

        event.accept()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #eef1f4;
            }

            QWidget {
                color: #1f2933;
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QFrame#headerFrame {
                background-color: #263746;
                border-radius: 8px;
            }

            QLabel#titleLabel {
                color: #ffffff;
                font-size: 20pt;
                font-weight: 700;
            }

            QLabel#subtitleLabel {
                color: #cbd5dc;
                font-size: 10pt;
            }

            QFrame#panelFrame {
                background-color: #ffffff;
                border: 1px solid #d5dce2;
                border-radius: 8px;
            }

            QLabel#sectionTitle {
                color: #263746;
                font-size: 14pt;
                font-weight: 700;
            }

            QLabel#fieldLabel {
                color: #52616d;
                font-size: 9pt;
                font-weight: 600;
            }

            QLabel#helpLabel {
                color: #667784;
                font-size: 9pt;
            }

            QComboBox,
            QLineEdit {
                min-height: 38px;
                padding: 0 10px;
                background-color: #ffffff;
                border: 1px solid #b9c4cc;
                border-radius: 5px;
            }

            QComboBox:focus,
            QLineEdit:focus {
                border: 2px solid #b36b36;
            }

            QComboBox:disabled,
            QLineEdit:disabled {
                background-color: #e8ecef;
                color: #7a8790;
            }

            QPushButton {
                min-height: 38px;
                padding: 0 16px;
                background-color: #e8ecef;
                border: 1px solid #bcc6cd;
                border-radius: 5px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #dce3e8;
            }

            QPushButton:pressed {
                background-color: #cbd5dc;
            }

            QPushButton:disabled {
                background-color: #edf0f2;
                color: #9aa5ad;
                border-color: #d8dee3;
            }

            QPushButton#primaryButton {
                color: #ffffff;
                background-color: #b36b36;
                border-color: #9a582a;
            }

            QPushButton#primaryButton:hover {
                background-color: #9f5d30;
            }

            QPushButton#primaryButton:pressed {
                background-color: #864b25;
            }

            QFrame#identityFrame {
                background-color: #f7f9fa;
                border: 1px solid #dde3e7;
                border-radius: 5px;
            }

            QLabel#identityNameLabel {
                color: #677681;
                font-size: 9pt;
            }

            QLabel#identityValueLabel {
                color: #263746;
                font-weight: 600;
            }

            QLabel#statusConnected {
                min-height: 36px;
                color: #176c43;
                background-color: #dff3e8;
                border: 1px solid #a9ddbf;
                border-radius: 5px;
                font-weight: 700;
            }

            QLabel#statusDisconnected {
                min-height: 36px;
                color: #5c6972;
                background-color: #edf0f2;
                border: 1px solid #d2d9de;
                border-radius: 5px;
                font-weight: 700;
            }

            QLabel#statusError {
                min-height: 36px;
                color: #9d2929;
                background-color: #f8dfdf;
                border: 1px solid #e5adad;
                border-radius: 5px;
                font-weight: 700;
            }

            QTextEdit#consoleOutput {
                color: #e6edf3;
                background-color: #17212b;
                border: 1px solid #0e161e;
                border-radius: 5px;
                padding: 10px;
                selection-background-color: #b36b36;
            }

            QStatusBar {
                background-color: #263746;
                color: #ffffff;
            }
            """
        )