#!/usr/bin/env python3

import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()


def start_connections(host, port,messages):
    messages_b = [message.encode('ascii') for message in messages]
    server_addr = (host, port)
    print(f"Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(server_addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        msg_total=sum(len(m) for m in messages_b),
        recv_total=0,
        messages=messages_b.copy(),
        outb=b"",
    )
    sel.register(sock, events, data=data)



def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            print(f"Server replied: {recv_data!r} ")
            data.recv_total += len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            print(f"Closing connection")
            # print(f"Closing connection {data.connid}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            print(f"Sending {data.outb!r}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


host = '127.0.0.1'
port = 54657
username = "MortenLarsen"
password = 'horse'

while True:
    command = input("input command:")
    messages = [f"{username}", f"{password}", f"{command}"]
    start_connections(host, int(port), messages)
    try:
        while True:
            events = sel.select(timeout=300)
            if events:
                for key, mask in events:
                    service_connection(key, mask)
            # Check for a socket being monitored to continue.
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()
