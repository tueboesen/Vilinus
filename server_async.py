import asyncio
import numpy as np

async def handle_echo(reader, writer):
    global line
    while True:
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        print(f"Received {message!r} from {addr!r}")
        if message == 'quit':
            writer.write(message.encode())
            await writer.drain()
            writer.close()
            print("Closing connection to client.")
            await writer.wait_closed()
            break
        else:
            answer = f"answer={np.random.randint(0,10)}"
            print(f"Sent: {answer!r}")
            writer.write(answer.encode())
            await writer.drain()


async def main():
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 8888)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())