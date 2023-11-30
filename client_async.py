import asyncio
from time import sleep

import aioconsole


async def tcp_echo_client():
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 8888)
    while True:
        line = await aioconsole.ainput('Command me... ')

        print(f'Send: {line!r}')
        writer.write(line.encode())
        await writer.drain()

        data_b = await reader.read(100)
        data = data_b.decode()
        print(f'Received: {data!r}')
        if data == 'quit':
            print('Closing the connection')
            writer.close()
            await writer.wait_closed()
            break

asyncio.run(tcp_echo_client())