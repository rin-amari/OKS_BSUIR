import asyncio
import tkinter as tk
import random
from time import sleep

import serial
import serial.tools.list_ports
import globals
from bitarray import bitarray

from cyclic import cyclic


def hex_print(data):
    hex_string = " ".join(format(byte, '02X') for byte in data)
    print(hex_string)


def create_packet(source_address, message):
    packet = bytearray(b'')
    flag = bytes([ord('z') + 25])
    destination_address = bytes([0x00])
    source_address = bytes([int(source_address[3:])])
    data = bytearray(b'')
    for i in message:
        data += bytes([ord(i)])

    data_bits = bitarray()
    data_bits.frombytes(data)
    data_bits_arr = list([])
    for i in range(len(data_bits)):
        if data_bits[i] & 1:
            data_bits_arr.append(1)
        else:
            data_bits_arr.append(0)
    divisor = [1, 0, 1, 0, 0, 1]

    fcs = bytes(cyclic(data_bits_arr, divisor))
    packet += flag + destination_address + source_address + data + fcs
    hex_print(packet)
    return packet


def bragging_stuffed_structure(stuffed_packet, text_stuff):
    str = ""
    i = 0
    while i < len(stuffed_packet):
        current_element = bytes([stuffed_packet[i]])
        if current_element == bytes([0x92]) or current_element == bytes([0x93]):
            str += format(current_element[0], '02X')
            i += 1
        else:
            str += "."
            i += 1

    text_stuff.delete("1.0", tk.END)
    text_stuff.insert(tk.END, str, "custom_tag")


def byte_destuffing(stuffed_packet):
    if stuffed_packet[0] != 0x93 or stuffed_packet[-1] != 0x93:
        return 0

    destuffed_packet = bytearray()

    i = 0
    while i < len(stuffed_packet) - 1:
        current_element = bytes([stuffed_packet[i]])
        next_element = bytes([stuffed_packet[i + 1]])

        if current_element == bytes([0x93]) and next_element == bytes([0x93]):
            destuffed_packet += current_element
            i += 2
        elif current_element == bytes([0x92]) and next_element == bytes([0x93]):
            i += 2
        else:
            destuffed_packet += current_element
            i += 1

    hex_print(destuffed_packet)
    return destuffed_packet


def receive(output_window, ser, stuffed_packet, text_stuff, debug_window):
    received_data = b''

    while True:
        byte = ser.read(1)
        received_data += byte
        if byte == b'':
            break
        if byte == b'\x93' and len(received_data) > 3:
            break

    if received_data.startswith(bytes([0x93])) and received_data.endswith(bytes([0x93])):
        bragging_stuffed_structure(stuffed_packet, text_stuff)
        destuffed_packet = byte_destuffing(stuffed_packet)
        received_data = destuffed_packet[3:]
        received_data = received_data[:-1]
        received_data = received_data.decode()
        output_window.insert(tk.END, received_data + "\n")

        fcs = destuffed_packet[-1]
        data = bytearray(b'')

        for i in received_data:
            data += bytes([ord(i)])

        data_bits = bitarray()
        data_bits.frombytes(data)
        data_bits_arr = list([])
        for i in data_bits:
            if i & 1:
                data_bits_arr.append(1)
            else:
                data_bits_arr.append(0)
        if data == b'!!JAM!!!!!!!!!!!!!!!!!!!!':
            debug_window.insert(tk.END, f"JAM received\n")
        # divisor = [1, 0, 1, 0, 0, 1]
        # d = cyclic(data_bits_arr, divisor)
        # if d != fcs.to_bytes():
        #     print("Received data with fcs error")
        #     for i in range(len(data_bits_arr)):
        #         data_bits_arr1 = data_bits_arr
        #         if i & 1:
        #             data_bits_arr1[i] = 0
        #         else:
        #             data_bits_arr1[i] = 1
        #         d = cyclic(data_bits_arr, divisor)
        #         if d == fcs.to_bytes():
        #             break


def byte_stuffing(packet):
    flag = bytes([0x93])
    stuffed_packet = bytearray()
    stuffed_packet += flag
    for i in packet[0:]:
        if bytes([i]) == flag:
            stuffed_packet += bytes([0x92])
            stuffed_packet.append(i)
        else:
            stuffed_packet.append(i)

    stuffed_packet += flag
    hex_print(stuffed_packet)
    return stuffed_packet


def is_channel_busy():
    return random.random() < 0.5


def is_collision():
    return random.random() < 0.25


def calculate_random_delay():
    return random.randint(0, 5)


def jam_signal(ser):
    jam_signal_packet = bytearray(b'')
    jam_signal_packet += b'!!JAM!!!!!!!!!!!!!!!!!!!!'

    return jam_signal_packet


def send_message(input_window, output_window, ser, ser2, port, text_stuff, debug_window):
    global packet
    message = input_window.get("1.0", "end-1c")
    output_window.delete("1.0", tk.END)

    if len(message) < 25:
        message = message.ljust(25)
    elif len(message) > 25:
        message = message[:25]

    packet = create_packet(port, message)
    collision_counter = 0
    while is_channel_busy():
        debug_window.insert(tk.END, "Channel is busy, waiting...\n")
        delay = calculate_random_delay()
        debug_window.insert(tk.END, f"Waiting for {delay} second(s) before sending..\n")
        sleep(delay)
        while is_collision():
            collision_counter += 1
            if collision_counter == 10:
                debug_window.insert(tk.END, f"Too many collisions...\n")
                return
            debug_window.insert(tk.END, "Collision detected...\n")
            packet = jam_signal(ser)
            delay = calculate_random_delay()
            debug_window.insert(tk.END, f"Waiting for {delay} second(s) before sending..\n")
            sleep(delay)


    stuffed_packet = byte_stuffing(packet)

    globals.bytes_count += len(stuffed_packet)
    ser.write(stuffed_packet)
    receive(output_window, ser2, stuffed_packet, text_stuff, debug_window)
    debug_window.insert(tk.END, "Received successfully\n")


async def main():
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

    text_stuff = tk.Text(root, height=1, width=40, borderwidth=0, relief="solid", bg="SystemButtonFace")
    text_stuff.tag_configure("custom_tag", font=("Helvetica", 7))
    text_stuff.pack()

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
        if turn:
            ser = serial.Serial(globals.port_1, baudrate=globals.baudrate, parity=globals.parity)
            ser2 = serial.Serial(globals.port_2, baudrate=globals.baudrate, parity=globals.parity)
            debug_window.insert(tk.END, f"Sending from {globals.port_1} to {globals.port_2}\n")
            send_message(input_window_1, output_window_1, ser, ser2, globals.port_1, text_stuff, debug_window)
        else:
            ser = serial.Serial(globals.port_4, baudrate=globals.baudrate, parity=globals.parity)
            ser2 = serial.Serial(globals.port_3, baudrate=globals.baudrate, parity=globals.parity)
            debug_window.insert(tk.END, f"Sending from {globals.port_2} to {globals.port_1}\n")
            send_message(input_window_2, output_window_2, ser2, ser, globals.port_4, text_stuff, debug_window)
        byte_count_label.config(text=f"Byte Count: {globals.bytes_count}")

    tk.Button(root, text="Send Message", command=lambda: send_button_clicked(True)).pack()

    tk.Label(root, text=f"Enter message (from {globals.port_4} to {globals.port_3}):").pack()
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
