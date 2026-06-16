"""
Superdense Coding

Protocol where Alice sends 2 classical bits using only 1 qubit,
assuming she and Bob already share a Bell pair.

Qubit 0 = Alice | Qubit 1 = Bob
"""

from qiskit import QuantumCircuit as QiskitQuantumCircuit
from qiskit.visualization import circuit_drawer
import matplotlib.pyplot as plt
from spinqit.qiskit.circuit import QuantumCircuit
from spinqit import (
    get_compiler,
    get_basic_simulator,
    get_nmr,
    BasicSimulatorConfig,
    NMRConfig,
)

# === Message choice ===

print("Superdense Coding — choose the 2-bit message Alice sends:")
print("1) 00")
print("2) 01")
print("3) 10")
print("4) 11")

choice = input("Type 1, 2, 3 or 4: ").strip()
messages = {"1": "00", "2": "01", "3": "10", "4": "11"}

if choice not in messages:
    raise SystemExit("Invalid option. Please run the script again.")

message = messages[choice]
print(f"\nChosen message: {message}")

# === Quantum circuit ===

def apply_superdense_gates(qc, message):
    """Build the superdense-coding protocol on any compatible QuantumCircuit."""

    # Step 1: create the Bell pair shared by Alice (q0) and Bob (q1)
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()

    # Step 2: Alice encodes the two classical bits on her qubit (q0)
    #   00 -> identity (do nothing)
    #   01 -> X gate
    #   10 -> Z gate
    #   11 -> X and Z gates
    if message == "01":
        qc.x(0)
    elif message == "10":
        qc.z(0)
    elif message == "11":
        qc.x(0)
        qc.z(0)

    # Step 3: Bob receives Alice's qubit and decodes the message
    qc.barrier()
    qc.cx(0, 1)
    qc.h(0)

    # Step 4: measure both qubits — the outcome should match the sent message
    qc.barrier()
    qc.measure([0, 1], [0, 1])


# Circuit used to compile and run on the Triangulum II (SpinQit API)
qc = QuantumCircuit(2, 2)
apply_superdense_gates(qc, message)

# Identical circuit just for drawing the diagram (standard Qiskit API)
qc_plot = QiskitQuantumCircuit(2, 2)
apply_superdense_gates(qc_plot, message)

# === Circuit visualization ===
print("\nCIRCUIT:")
print(circuit_drawer(qc_plot, output="text"))

# === Compilation and execution ===

compiler = get_compiler("qiskit")

if input("\nUse simulator? (y/n): ").lower() == "y":
    device = get_basic_simulator()
    config = BasicSimulatorConfig()
    config.configure_shots(1024)
else:
    print("Using NMR device...")
    ip = input("IP address: ")
    port = int(input("Port: "))
    username = input("Username: ")
    password = input("Password: ")
    task = input("Task name: ")
    device = get_nmr()
    config = NMRConfig()
    config.configure_shots(1024)
    config.configure_ip(ip)
    config.configure_port(port)
    config.configure_account(username, password)
    config.configure_task(task, "GHZ")

exe = compiler.compile(qc, 0)
result = device.execute(exe, config)

# === Results ===

print("\n--- Results ---")
print(f"Message sent by Alice: {message}")
print("Counts:\n", result.counts)