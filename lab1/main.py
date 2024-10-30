import asyncio
import tkinter as tk
import serial
import serial.tools.list_ports
import globals


def find_available_ports():
    available_ports = list(serial.tools.list_ports.comports())
    free_ports = []

    for port in available_ports:
        if "COM" in port.description:
            if "COM1" not in port.description:
                free_ports.append(port.device)

    if len(free_ports) >= 2:
        globals.port_1, globals.port_2 = free_ports[:2]
    else:
        print("No available ports")


def receive(output_window, ser, port, parity):
    received_data = b''
    while True:
        data = ser.read(1)
        if not data:
            continue

        received_data += data

        if data == b'p':
            received_data = received_data[:-1]

            if parity == 'E':
                parity_bit = (received_data.count(b'1') % 2 == 0).to_bytes(1, byteorder='big')
            elif parity == 'O':
                parity_bit = (received_data.count(b'1') % 2 == 1).to_bytes(1, byteorder='big')

            if received_data.endswith(parity_bit):
                received_message = received_data[:-1].decode('utf-8').strip()
                print(f"Received: {received_message} on port {port}")
                output_window.insert(tk.END, received_message + "\n")

            else:
                print("Received data with parity error on port " + port)
            break


def send(ser, message):

    if globals.parity == 'E':
        parity_bit = (message.count(b'1') % 2 == 0).to_bytes(1, byteorder='big')
    elif globals.parity == 'O':
        parity_bit = (message.count(b'1') % 2 == 1).to_bytes(1, byteorder='big')

    message_with_parity = message + parity_bit + b'p'
    ser.write(message_with_parity)


def send_message(input_window, output_window, ser, ser2, parity, debug_window):
    message = input_window.get("1.0", "end-1c")
    output_window.delete("1.0", tk.END)
    globals.bytes_count += len(message)
    send(ser, message.encode())
    debug_window.insert(tk.END, "Sent successfully\n")
    receive(output_window, ser2, globals.port_2, parity)
    debug_window.insert(tk.END, "Received successfully\n")


async def main():

    find_available_ports()

    root = tk.Tk()
    root.geometry("400x700")
    root.title("Serial Communication")

    debug_window = tk.Text(root, height=10, width=40)
    scrollbar = tk.Scrollbar(root, command=debug_window.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    debug_window.config(yscrollcommand=scrollbar.set)

    tk.Label(root, text=f"Enter message (from {globals.port_1} to {globals.port_2}):").pack()
    input_window_1 = tk.Text(root, height=3, width=40)
    input_window_1.pack()

    tk.Label(root, text="Output:").pack()
    output_window_1 = tk.Text(root, height=3, width=40)
    output_window_1.pack()

    tk.Label(root, text=f"Port 1: {globals.port_1}").pack()
    tk.Label(root, text=f"Port 2: {globals.port_2}").pack()
    byte_count_label = tk.Label(root, text="Byte Count: 0")
    byte_count_label.pack()

    def on_parity_selected(value):
        if value == "Even Parity":
            globals.parity = "E"
        elif value == "Odd Parity":
            globals.parity = "O"
        else:
            debug_window.insert(tk.END, "Choose parity!\n")
            raise ValueError("Invalid parity value. Use 'E' for even parity or 'O' for odd parity.")

    option_message = tk.StringVar(root)
    option_message.set("Set parity")
    options_parity_list = ["Even Parity", "Odd Parity"]
    question_menu = tk.OptionMenu(root, option_message, *options_parity_list)
    question_menu.pack()

    def send_button_clicked(turn):
        on_parity_selected(option_message.get())
        debug_window.insert(tk.END, "Setting up serial ports\n")
        debug_window.insert(tk.END, f"Parity: {globals.parity}\n")
        ser = serial.Serial(globals.port_1, baudrate=globals.baudrate, parity=globals.parity)
        ser2 = serial.Serial(globals.port_2, baudrate=globals.baudrate, parity=globals.parity)
        if turn:
            debug_window.insert(tk.END, f"Sending from {globals.port_1} to {globals.port_2}\n")
            send_message(input_window_1, output_window_1, ser, ser2, globals.parity, debug_window)
        else:
            debug_window.insert(tk.END, f"Sending from {globals.port_2} to {globals.port_1}\n")
            send_message(input_window_2, output_window_2, ser2, ser, globals.parity, debug_window)
        byte_count_label.config(text=f"Byte Count: {globals.bytes_count}")

    tk.Button(root, text="Send Message", command=lambda: send_button_clicked(True)).pack()

    tk.Label(root, text=f"Enter message (from {globals.port_2} to {globals.port_1}):").pack()
    input_window_2 = tk.Text(root, height=3, width=40)
    input_window_2.pack()

    tk.Label(root, text="Output:").pack()
    output_window_2 = tk.Text(root, height=3, width=40)
    output_window_2.pack()

    tk.Button(root, text="Send Message", command=lambda: send_button_clicked(False)).pack()

    tk.Label(root, text=f"Debug window:").pack()
    debug_window.pack()


    root.mainloop()


if __name__ == "__main__":
    asyncio.run(main())
