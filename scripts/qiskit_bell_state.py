from spinqit.qiskit.circuit import QuantumCircuit
from spinqit import get_compiler, get_basic_simulator, get_nmr, BasicSimulatorConfig, NMRConfig
from math import pi

# === Quantum Circuit ===

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

# === Compilation and Execution ===

compiler = get_compiler('qiskit')

if input("Use simulator? (y/n): ").lower() == 'y':
    device = get_basic_simulator()
    config = BasicSimulatorConfig()
else:
    print("Using NMR device...")
    ip = input("Enter the IP address: ")
    port = int(input("Enter the port: "))
    username = input("Enter the username: ")
    password = input("Enter the password: ")
    task = input("Enter the task name: ")
    device = get_nmr()
    config = NMRConfig()
    config.configure_shots(1024)
    config.configure_ip(ip)
    config.configure_port(port)
    config.configure_account(username, password)
    config.configure_task(task, 'GHZ')

exe = compiler.compile(qc, 0)
result = device.execute(exe, config)

# === Results ===

print('States:', '\n', result.states)
print('Counts:', '\n', result.counts)

