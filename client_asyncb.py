import asyncio
from time import sleep

import aioconsole


async def tcp_client(reader,writer):
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

async def connect_to_server():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    return reader, writer

async def main():
    reader, writer = connect_to_server()
    await tcp_client(reader, writer)

    await asyncio.gather(count(), count(), count())


if __name__ == '__main__':
    asyncio.run(main())

    # asyncio.run(connect_to_server())
    # asyncio.run(tcp_client(reader,writer))