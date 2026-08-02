from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
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
    QStackedWidget,
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
        self.resize(1180, 780)
        self.setMinimumSize(980, 680)

        self._instruments: dict[str, BaseInstrument] = {
            "Simulated Frequency Counter": (
                SimulatedFrequencyCounter()
            ),
            "Simulated Power Supply": (
                SimulatedPowerSupply()
            ),
        }

        self._active_instrument: BaseInstrument | None = None

        self._measurement_timer = QTimer(self)
        self._measurement_timer.setInterval(1000)
        self._measurement_timer.timeout.connect(
            self._poll_measurement
        )

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
            self._build_workspace_panel(),
            1,
        )

        root_layout.addLayout(
            content_layout,
            1,
        )

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

        self.live_monitor_button = QPushButton(
            "Start Live Monitor"
        )
        self.live_monitor_button.setCheckable(True)
        self.live_monitor_button.setEnabled(False)
        self.live_monitor_button.clicked.connect(
            self._toggle_live_monitor
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
        layout.addWidget(
            self.live_monitor_button
        )
        layout.addItem(
            QSpacerItem(
                0,
                0,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        )

        return panel

    def _build_workspace_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panelFrame")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        controls_title = QLabel(
            "Instrument Controls"
        )
        controls_title.setObjectName(
            "sectionTitle"
        )

        self.instrument_control_stack = QStackedWidget()
        self.instrument_control_stack.addWidget(
            self._build_frequency_counter_controls()
        )
        self.instrument_control_stack.addWidget(
            self._build_power_supply_controls()
        )

        console = self._build_console_panel()

        layout.addWidget(controls_title)
        layout.addWidget(
            self.instrument_control_stack
        )
        layout.addWidget(
            console,
            1,
        )

        return panel

    def _build_frequency_counter_controls(
        self,
    ) -> QWidget:
        widget = QFrame()
        widget.setObjectName("controlFrame")

        layout = QGridLayout(widget)
        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        target_label = QLabel(
            "Target Frequency"
        )
        target_label.setObjectName(
            "fieldLabel"
        )

        self.counter_target_spin = QDoubleSpinBox()
        self.counter_target_spin.setRange(
            1.0,
            10_000_000_000.0,
        )
        self.counter_target_spin.setDecimals(3)
        self.counter_target_spin.setValue(
            10_000_000.0
        )
        self.counter_target_spin.setSuffix(
            " Hz"
        )
        self.counter_target_spin.setEnabled(
            False
        )

        self.counter_input_button = QPushButton(
            "Enable Input"
        )
        self.counter_input_button.setCheckable(
            True
        )
        self.counter_input_button.setEnabled(
            False
        )
        self.counter_input_button.clicked.connect(
            self._toggle_counter_input
        )

        self.counter_measure_button = QPushButton(
            "Measure Frequency"
        )
        self.counter_measure_button.setObjectName(
            "primaryButton"
        )
        self.counter_measure_button.setEnabled(
            False
        )
        self.counter_measure_button.clicked.connect(
            self._measure_frequency_counter
        )

        measurement_frame = QFrame()
        measurement_frame.setObjectName(
            "measurementFrame"
        )

        measurement_layout = QGridLayout(
            measurement_frame
        )
        measurement_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )
        measurement_layout.setHorizontalSpacing(
            18
        )
        measurement_layout.setVerticalSpacing(
            8
        )

        self.counter_frequency_value = QLabel(
            "—"
        )
        self.counter_error_hz_value = QLabel(
            "—"
        )
        self.counter_error_ppm_value = QLabel(
            "—"
        )

        counter_rows = (
            (
                "Measured Frequency",
                self.counter_frequency_value,
            ),
            (
                "Frequency Error",
                self.counter_error_hz_value,
            ),
            (
                "Error",
                self.counter_error_ppm_value,
            ),
        )

        for row, (
            text,
            value,
        ) in enumerate(counter_rows):
            name_label = QLabel(text)
            name_label.setObjectName(
                "measurementNameLabel"
            )
            value.setObjectName(
                "measurementValueLabel"
            )
            value.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            measurement_layout.addWidget(
                name_label,
                row,
                0,
            )
            measurement_layout.addWidget(
                value,
                row,
                1,
            )

        measurement_layout.setColumnStretch(
            1,
            1,
        )

        layout.addWidget(
            target_label,
            0,
            0,
        )
        layout.addWidget(
            self.counter_target_spin,
            0,
            1,
        )
        layout.addWidget(
            self.counter_input_button,
            0,
            2,
        )
        layout.addWidget(
            self.counter_measure_button,
            0,
            3,
        )
        layout.addWidget(
            measurement_frame,
            1,
            0,
            1,
            4,
        )

        layout.setColumnStretch(
            1,
            1,
        )

        return widget

    def _build_power_supply_controls(
        self,
    ) -> QWidget:
        widget = QFrame()
        widget.setObjectName("controlFrame")

        layout = QGridLayout(widget)
        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        voltage_label = QLabel(
            "Voltage Setpoint"
        )
        voltage_label.setObjectName(
            "fieldLabel"
        )

        self.supply_voltage_spin = QDoubleSpinBox()
        self.supply_voltage_spin.setRange(
            0.0,
            30.0,
        )
        self.supply_voltage_spin.setDecimals(3)
        self.supply_voltage_spin.setValue(
            12.0
        )
        self.supply_voltage_spin.setSuffix(
            " V"
        )
        self.supply_voltage_spin.setEnabled(
            False
        )

        current_label = QLabel(
            "Current Limit"
        )
        current_label.setObjectName(
            "fieldLabel"
        )

        self.supply_current_spin = QDoubleSpinBox()
        self.supply_current_spin.setRange(
            0.001,
            5.0,
        )
        self.supply_current_spin.setDecimals(3)
        self.supply_current_spin.setValue(
            1.0
        )
        self.supply_current_spin.setSuffix(
            " A"
        )
        self.supply_current_spin.setEnabled(
            False
        )

        self.supply_apply_button = QPushButton(
            "Apply Settings"
        )
        self.supply_apply_button.setEnabled(
            False
        )
        self.supply_apply_button.clicked.connect(
            self._apply_power_supply_settings
        )

        self.supply_output_button = QPushButton(
            "Enable Output"
        )
        self.supply_output_button.setCheckable(
            True
        )
        self.supply_output_button.setEnabled(
            False
        )
        self.supply_output_button.clicked.connect(
            self._toggle_power_supply_output
        )

        self.supply_measure_button = QPushButton(
            "Measure Output"
        )
        self.supply_measure_button.setObjectName(
            "primaryButton"
        )
        self.supply_measure_button.setEnabled(
            False
        )
        self.supply_measure_button.clicked.connect(
            self._measure_power_supply
        )

        measurement_frame = QFrame()
        measurement_frame.setObjectName(
            "measurementFrame"
        )

        measurement_layout = QGridLayout(
            measurement_frame
        )
        measurement_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )
        measurement_layout.setHorizontalSpacing(
            18
        )
        measurement_layout.setVerticalSpacing(
            8
        )

        self.supply_voltage_value = QLabel(
            "—"
        )
        self.supply_current_value = QLabel(
            "—"
        )
        self.supply_power_value = QLabel(
            "—"
        )

        supply_rows = (
            (
                "Measured Voltage",
                self.supply_voltage_value,
            ),
            (
                "Measured Current",
                self.supply_current_value,
            ),
            (
                "Measured Power",
                self.supply_power_value,
            ),
        )

        for row, (
            text,
            value,
        ) in enumerate(supply_rows):
            name_label = QLabel(text)
            name_label.setObjectName(
                "measurementNameLabel"
            )
            value.setObjectName(
                "measurementValueLabel"
            )
            value.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            measurement_layout.addWidget(
                name_label,
                row,
                0,
            )
            measurement_layout.addWidget(
                value,
                row,
                1,
            )

        measurement_layout.setColumnStretch(
            1,
            1,
        )

        layout.addWidget(
            voltage_label,
            0,
            0,
        )
        layout.addWidget(
            self.supply_voltage_spin,
            0,
            1,
        )
        layout.addWidget(
            current_label,
            0,
            2,
        )
        layout.addWidget(
            self.supply_current_spin,
            0,
            3,
        )
        layout.addWidget(
            self.supply_apply_button,
            1,
            0,
        )
        layout.addWidget(
            self.supply_output_button,
            1,
            1,
        )
        layout.addWidget(
            self.supply_measure_button,
            1,
            2,
            1,
            2,
        )
        layout.addWidget(
            measurement_frame,
            2,
            0,
            1,
            4,
        )

        layout.setColumnStretch(
            1,
            1,
        )
        layout.setColumnStretch(
            3,
            1,
        )

        return widget

    def _build_console_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("consoleFrame")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)

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

        self._select_control_panel()
        self._clear_identity()
        self._clear_measurements()

        self.resource_value.setText(
            self._active_instrument.resource_name
        )

        self._update_connection_controls()

    def _on_instrument_selection_changed(
        self,
        selected_name: str,
    ) -> None:
        self._stop_live_monitor()

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

        self._select_control_panel()
        self._clear_identity()
        self._clear_measurements()

        self.resource_value.setText(
            self._active_instrument.resource_name
        )

        self._reset_instrument_buttons()
        self._update_connection_controls()

        self._append_system_message(
            f"Selected {selected_name}."
        )

    def _select_control_panel(self) -> None:
        if isinstance(
            self._active_instrument,
            SimulatedFrequencyCounter,
        ):
            self.instrument_control_stack.setCurrentIndex(
                0
            )
        else:
            self.instrument_control_stack.setCurrentIndex(
                1
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

        self._reset_instrument_buttons()
        self._update_connection_controls()
        self.command_input.setFocus()

    def _disconnect_instrument(self) -> None:
        instrument = self._require_active_instrument()

        self._stop_live_monitor()

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
        self._clear_measurements()
        self._reset_instrument_buttons()

        self.resource_value.setText(
            instrument.resource_name
        )

        self._update_connection_controls()

    def _toggle_counter_input(
        self,
        checked: bool,
    ) -> None:
        instrument = self._active_instrument

        if not isinstance(
            instrument,
            SimulatedFrequencyCounter,
        ):
            return

        try:
            if checked:
                instrument.enable_input()
                self.counter_input_button.setText(
                    "Disable Input"
                )
                self._append_system_message(
                    "Frequency-counter input enabled."
                )
            else:
                instrument.disable_input()
                self.counter_input_button.setText(
                    "Enable Input"
                )
                self._clear_counter_measurement()
                self._append_system_message(
                    "Frequency-counter input disabled."
                )
        except InstrumentError as exc:
            self.counter_input_button.setChecked(
                not checked
            )
            self._append_error(
                str(exc)
            )

    def _measure_frequency_counter(self) -> None:
        instrument = self._active_instrument

        if not isinstance(
            instrument,
            SimulatedFrequencyCounter,
        ):
            return

        try:
            measurement = instrument.measure_frequency(
                target_hz=self.counter_target_spin.value()
            )
        except InstrumentError as exc:
            self._append_error(
                str(exc)
            )
            return

        self.counter_frequency_value.setText(
            f"{measurement.frequency_hz:,.3f} Hz"
        )
        self.counter_error_hz_value.setText(
            f"{measurement.error_hz:+,.3f} Hz"
        )
        self.counter_error_ppm_value.setText(
            f"{measurement.error_ppm:+.6f} ppm"
        )

    def _apply_power_supply_settings(self) -> None:
        instrument = self._active_instrument

        if not isinstance(
            instrument,
            SimulatedPowerSupply,
        ):
            return

        try:
            instrument.configure(
                voltage_v=self.supply_voltage_spin.value(),
                current_limit_a=self.supply_current_spin.value(),
            )
        except InstrumentError as exc:
            self._append_error(
                str(exc)
            )
            return

        self._append_system_message(
            "Power-supply settings applied: "
            f"{instrument.voltage_setpoint_v:.3f} V, "
            f"{instrument.current_limit_a:.3f} A."
        )

    def _toggle_power_supply_output(
        self,
        checked: bool,
    ) -> None:
        instrument = self._active_instrument

        if not isinstance(
            instrument,
            SimulatedPowerSupply,
        ):
            return

        try:
            if checked:
                instrument.configure(
                    voltage_v=self.supply_voltage_spin.value(),
                    current_limit_a=self.supply_current_spin.value(),
                )
                instrument.enable_output()
                self.supply_output_button.setText(
                    "Disable Output"
                )
                self._append_system_message(
                    "Power-supply output enabled."
                )
                self._measure_power_supply()
            else:
                instrument.disable_output()
                self.supply_output_button.setText(
                    "Enable Output"
                )
                self._clear_supply_measurement()
                self._append_system_message(
                    "Power-supply output disabled."
                )
        except InstrumentError as exc:
            self.supply_output_button.setChecked(
                not checked
            )
            self._append_error(
                str(exc)
            )

    def _measure_power_supply(self) -> None:
        instrument = self._active_instrument

        if not isinstance(
            instrument,
            SimulatedPowerSupply,
        ):
            return

        try:
            measurement = instrument.measure()
        except InstrumentError as exc:
            self._append_error(
                str(exc)
            )
            return

        self.supply_voltage_value.setText(
            f"{measurement.voltage_v:.6f} V"
        )
        self.supply_current_value.setText(
            f"{measurement.current_a:.6f} A"
        )
        self.supply_power_value.setText(
            f"{measurement.power_w:.6f} W"
        )

    def _toggle_live_monitor(
        self,
        checked: bool,
    ) -> None:
        if checked:
            self._measurement_timer.start()
            self.live_monitor_button.setText(
                "Stop Live Monitor"
            )
            self._append_system_message(
                "Live measurement monitoring started."
            )
            self._poll_measurement()
        else:
            self._stop_live_monitor()
            self._append_system_message(
                "Live measurement monitoring stopped."
            )

    def _stop_live_monitor(self) -> None:
        self._measurement_timer.stop()
        self.live_monitor_button.setChecked(
            False
        )
        self.live_monitor_button.setText(
            "Start Live Monitor"
        )

    def _poll_measurement(self) -> None:
        instrument = self._active_instrument

        if (
            instrument is None
            or not instrument.is_connected
        ):
            self._stop_live_monitor()
            return

        if isinstance(
            instrument,
            SimulatedFrequencyCounter,
        ):
            if instrument.input_enabled:
                self._measure_frequency_counter()
            return

        if isinstance(
            instrument,
            SimulatedPowerSupply,
        ):
            if instrument.output_enabled:
                self._measure_power_supply()

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

            self._synchronize_controls_from_instrument()

        except InstrumentError as exc:
            self._append_error(
                str(exc)
            )

        self.command_input.clear()
        self.command_input.setFocus()

    def _synchronize_controls_from_instrument(
        self,
    ) -> None:
        instrument = self._active_instrument

        if isinstance(
            instrument,
            SimulatedFrequencyCounter,
        ):
            self.counter_input_button.setChecked(
                instrument.input_enabled
            )
            self.counter_input_button.setText(
                "Disable Input"
                if instrument.input_enabled
                else "Enable Input"
            )
            return

        if isinstance(
            instrument,
            SimulatedPowerSupply,
        ):
            self.supply_voltage_spin.setValue(
                instrument.voltage_setpoint_v
            )
            self.supply_current_spin.setValue(
                instrument.current_limit_a
            )
            self.supply_output_button.setChecked(
                instrument.output_enabled
            )
            self.supply_output_button.setText(
                "Disable Output"
                if instrument.output_enabled
                else "Enable Output"
            )

            if not instrument.output_enabled:
                self._clear_supply_measurement()

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
        self.live_monitor_button.setEnabled(
            is_connected
        )

        is_counter = isinstance(
            instrument,
            SimulatedFrequencyCounter,
        )
        is_supply = isinstance(
            instrument,
            SimulatedPowerSupply,
        )

        self.counter_target_spin.setEnabled(
            is_connected and is_counter
        )
        self.counter_input_button.setEnabled(
            is_connected and is_counter
        )
        self.counter_measure_button.setEnabled(
            is_connected and is_counter
        )

        self.supply_voltage_spin.setEnabled(
            is_connected and is_supply
        )
        self.supply_current_spin.setEnabled(
            is_connected and is_supply
        )
        self.supply_apply_button.setEnabled(
            is_connected and is_supply
        )
        self.supply_output_button.setEnabled(
            is_connected and is_supply
        )
        self.supply_measure_button.setEnabled(
            is_connected and is_supply
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

    def _reset_instrument_buttons(self) -> None:
        self.counter_input_button.setChecked(
            False
        )
        self.counter_input_button.setText(
            "Enable Input"
        )

        self.supply_output_button.setChecked(
            False
        )
        self.supply_output_button.setText(
            "Enable Output"
        )

    def _clear_identity(self) -> None:
        self.manufacturer_value.setText("—")
        self.model_value.setText("—")
        self.serial_value.setText("—")
        self.firmware_value.setText("—")

    def _clear_measurements(self) -> None:
        self._clear_counter_measurement()
        self._clear_supply_measurement()

    def _clear_counter_measurement(self) -> None:
        self.counter_frequency_value.setText(
            "—"
        )
        self.counter_error_hz_value.setText(
            "—"
        )
        self.counter_error_ppm_value.setText(
            "—"
        )

    def _clear_supply_measurement(self) -> None:
        self.supply_voltage_value.setText(
            "—"
        )
        self.supply_current_value.setText(
            "—"
        )
        self.supply_power_value.setText(
            "—"
        )

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
        self._measurement_timer.stop()

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

            QFrame#controlFrame {
                background-color: #f7f9fa;
                border: 1px solid #d8e0e5;
                border-radius: 6px;
            }

            QFrame#consoleFrame {
                border: none;
            }

            QFrame#identityFrame,
            QFrame#measurementFrame {
                background-color: #f7f9fa;
                border: 1px solid #dde3e7;
                border-radius: 5px;
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

            QLabel#identityNameLabel,
            QLabel#measurementNameLabel {
                color: #677681;
                font-size: 9pt;
            }

            QLabel#identityValueLabel {
                color: #263746;
                font-weight: 600;
            }

            QLabel#measurementValueLabel {
                color: #263746;
                font-family: "Consolas";
                font-size: 11pt;
                font-weight: 700;
            }

            QComboBox,
            QLineEdit,
            QDoubleSpinBox {
                min-height: 38px;
                padding: 0 10px;
                background-color: #ffffff;
                border: 1px solid #b9c4cc;
                border-radius: 5px;
            }

            QComboBox:focus,
            QLineEdit:focus,
            QDoubleSpinBox:focus {
                border: 2px solid #b36b36;
            }

            QComboBox:disabled,
            QLineEdit:disabled,
            QDoubleSpinBox:disabled {
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

            QPushButton:checked {
                color: #ffffff;
                background-color: #496b59;
                border-color: #385244;
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