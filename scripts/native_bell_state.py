from spinqit import get_basic_simulator, get_compiler, Circuit, BasicSimulatorConfig, get_nmr, NMRConfig
from spinqit import H, CX, Rx
from math import pi

# === Quantum Circuit ===

circ = Circuit()
q = circ.allocateQubits(2)

circ << (H, q[0])
circ << (CX, (q[0], q[1]))

# === Compilation and Execution ===

compiler = get_compiler("native")

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

exe = compiler.compile(circ, 0)
result = device.execute(exe, config)

# === Results ===

print('States:', '\n', result.states)
print('Counts:', '\n', result.counts)
