import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from qiskit import QuantumCircuit as QiskitQuantumCircuit
from qiskit.visualization import circuit_drawer
from spinqit import (
    BasicSimulatorConfig,
    NMRConfig,
    get_basic_simulator,
    get_compiler,
    get_nmr,
)
from spinqit.qiskit.circuit import QuantumCircuit as SpinQitQuantumCircuit

MESSAGES = ("00", "01", "10", "11")


def _apply_superdense_gates(qc, message: str) -> None:
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()

    if message == "01":
        qc.x(0)
    elif message == "10":
        qc.z(0)
    elif message == "11":
        qc.x(0)
        qc.z(0)

    qc.barrier()
    qc.cx(0, 1)
    qc.h(0)
    qc.measure([0, 1], [0, 1])


def build_superdense_coding_circuit(message: str) -> SpinQitQuantumCircuit:
    qc = SpinQitQuantumCircuit(2, 2)
    _apply_superdense_gates(qc, message)
    return qc


def build_superdense_coding_circuit_for_display(message: str) -> QiskitQuantumCircuit:
    qc = QiskitQuantumCircuit(2, 2)
    _apply_superdense_gates(qc, message)
    return qc


class SuperdenseCodingApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Superdense Coding — Triangulum II")
        self.geometry("1100x720")
        self.minsize(900, 600)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self._canvas_widget = None
        self._build_layout()
        self._update_circuit_plot()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkScrollableFrame(self, width=340, label_text="Settings")
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        plot_frame = ctk.CTkFrame(self)
        plot_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        plot_frame.grid_rowconfigure(0, weight=1)
        plot_frame.grid_columnconfigure(0, weight=1)

        self.plot_container = ctk.CTkFrame(plot_frame, fg_color="transparent")
        self.plot_container.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        ctk.CTkLabel(
            sidebar,
            text="Classical message (2 bits)",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=8, pady=(4, 0))

        self.message_var = ctk.StringVar(value="00")
        self.message_menu = ctk.CTkOptionMenu(
            sidebar,
            variable=self.message_var,
            values=list(MESSAGES),
            command=self._on_message_changed,
        )
        self.message_menu.pack(fill="x", padx=8, pady=(4, 12))

        ctk.CTkLabel(
            sidebar,
            text="Device",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=8, pady=(4, 0))

        self.device_var = ctk.StringVar(value="simulator")
        device_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        device_frame.pack(fill="x", padx=8, pady=(4, 8))

        ctk.CTkRadioButton(
            device_frame,
            text="Simulator",
            variable=self.device_var,
            value="simulator",
            command=self._toggle_device_fields,
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            device_frame,
            text="NMR device (Triangulum II)",
            variable=self.device_var,
            value="nmr",
            command=self._toggle_device_fields,
        ).pack(anchor="w", pady=2)

        ctk.CTkLabel(
            sidebar,
            text="Simulator",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=8, pady=(8, 0))

        self.sim_shots_entry = self._labeled_entry(sidebar, "Shots", "1024")

        self.nmr_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.nmr_section.pack(fill="x", padx=0, pady=(8, 0))

        ctk.CTkLabel(
            self.nmr_section,
            text="NMR device",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=8, pady=(4, 0))

        self.nmr_ip_entry = self._labeled_entry(self.nmr_section, "IP address", "127.0.0.1")
        self.nmr_port_entry = self._labeled_entry(self.nmr_section, "Port", "8989")
        self.nmr_user_entry = self._labeled_entry(self.nmr_section, "Username", "")
        self.nmr_password_entry = self._labeled_entry(
            self.nmr_section, "Password", "", show="*"
        )
        self.nmr_task_entry = self._labeled_entry(self.nmr_section, "Task name", "")
        self.nmr_task_type_entry = self._labeled_entry(self.nmr_section, "Task type", "GHZ")
        self.nmr_shots_entry = self._labeled_entry(self.nmr_section, "Shots", "1024")

        button_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        button_frame.pack(fill="x", padx=8, pady=16)

        self.run_button = ctk.CTkButton(
            button_frame,
            text="Run circuit",
            command=self._run_circuit,
        )
        self.run_button.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            button_frame,
            text="Refresh diagram",
            fg_color="transparent",
            border_width=1,
            command=self._update_circuit_plot,
        ).pack(fill="x")

        ctk.CTkLabel(
            sidebar,
            text="Results",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=8, pady=(8, 0))

        self.results_box = ctk.CTkTextbox(sidebar, height=160)
        self.results_box.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        self.results_box.configure(state="disabled")

        self._toggle_device_fields()

    def _labeled_entry(
        self,
        parent: ctk.CTkBaseClass,
        label: str,
        default: str,
        show: Optional[str] = None,
    ) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=8, pady=(6, 0))
        entry = ctk.CTkEntry(parent, show=show) if show else ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=8, pady=(2, 0))
        if default:
            entry.insert(0, default)
        return entry

    def _toggle_device_fields(self) -> None:
        use_nmr = self.device_var.get() == "nmr"
        state = "normal" if use_nmr else "disabled"

        for widget in self.nmr_section.winfo_children():
            if isinstance(widget, ctk.CTkEntry):
                widget.configure(state=state)

        self.sim_shots_entry.configure(state="disabled" if use_nmr else "normal")

    def _on_message_changed(self, _value: str) -> None:
        self._update_circuit_plot()

    def _get_selected_message(self) -> str:
        return self.message_var.get()

    def _parse_positive_int(self, value: str, field_name: str) -> int:
        try:
            parsed = int(value.strip())
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer.") from exc
        if parsed <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")
        return parsed

    def _build_device_config(self):
        if self.device_var.get() == "simulator":
            shots = self._parse_positive_int(self.sim_shots_entry.get(), "Simulator shots")
            device = get_basic_simulator()
            config = BasicSimulatorConfig()
            config.configure_shots(shots)
            return device, config

        ip = self.nmr_ip_entry.get().strip()
        port = self._parse_positive_int(self.nmr_port_entry.get(), "Port")
        username = self.nmr_user_entry.get().strip()
        password = self.nmr_password_entry.get()
        task = self.nmr_task_entry.get().strip()
        task_type = self.nmr_task_type_entry.get().strip() or "GHZ"
        shots = self._parse_positive_int(self.nmr_shots_entry.get(), "NMR shots")

        if not ip:
            raise ValueError("Please enter the NMR device IP address.")
        if not username:
            raise ValueError("Please enter the NMR device username.")
        if not task:
            raise ValueError("Please enter the NMR task name.")

        device = get_nmr()
        config = NMRConfig()
        config.configure_shots(shots)
        config.configure_ip(ip)
        config.configure_port(port)
        config.configure_account(username, password)
        config.configure_task(task, task_type)
        return device, config

    def _set_results(self, text: str) -> None:
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", tk.END)
        self.results_box.insert("1.0", text)
        self.results_box.configure(state="disabled")

    def _update_circuit_plot(self) -> None:
        message = self._get_selected_message()
        circuit = build_superdense_coding_circuit_for_display(message)

        if self._canvas_widget is not None:
            self._canvas_widget.get_tk_widget().destroy()
            plt.close(self._canvas_widget.figure)

        figure = circuit_drawer(circuit, output="mpl", fold=-1)
        canvas = FigureCanvasTkAgg(figure, master=self.plot_container)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)
        self._canvas_widget = canvas

    def _run_circuit(self) -> None:
        self.run_button.configure(state="disabled", text="Running...")
        self._set_results("Running circuit...\n")

        thread = threading.Thread(target=self._execute_circuit, daemon=True)
        thread.start()

    def _execute_circuit(self) -> None:
        try:
            message = self._get_selected_message()
            circuit = build_superdense_coding_circuit(message)
            device, config = self._build_device_config()

            compiler = get_compiler("qiskit")
            executable = compiler.compile(circuit, 0)
            result = device.execute(executable, config)
            
            counts = {'00': 0, '01': 0, '10': 0, '11': 0}
            counts.update(result.counts)
            counts_txt = "\n".join(
                [f"State=|{state}> Count={count}" for state, count in counts.items()]
            )
            output = (
                f"SENT MESSAGE: {message}\n\n"
                f"MEASUREMENTS\n{counts_txt}"

            )
            self.after(0, lambda: self._on_run_success(output))
        except Exception as exc:
            self.after(0, lambda: self._on_run_error(str(exc)))

    def _on_run_success(self, output: str) -> None:
        self._set_results(output)
        self.run_button.configure(state="normal", text="Run circuit")

    def _on_run_error(self, error_message: str) -> None:
        self._set_results(f"Execution error:\n{error_message}")
        self.run_button.configure(state="normal", text="Run circuit")
        messagebox.showerror("Error", error_message)


def main() -> None:
    app = SuperdenseCodingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
