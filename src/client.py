import asyncio
from time import sleep

import aioconsole

async def logon(username,password,reader,writer):
    """
    Client logon decoder
    """

    writer.write(username.encode())
    await writer.drain()

    data_b = await reader.read(100)
    message = data_b.decode()
    if message != 'username accepted':
        writer.close()
        await writer.wait_closed()
        raise ValueError(f"username not accepted. {message}")

    writer.write(password.encode())
    await writer.drain()

    data_b = await reader.read(100)
    message = data_b.decode()
    if message != 'password accepted':
        writer.close()
        await writer.wait_closed()
        raise ValueError(f"password not accepted. {message}")
    return

async def vibinus_game_client(hostname, port, username,password):
    """
    Async client logon

    Allows a user to issue commands to a game server and get responses back based on the command.
    """
    reader, writer = await asyncio.open_connection(hostname, port)
    try:
        await logon(username, password, reader, writer)
    except Exception as e:
        print(f"{e}")
        return
    print(f"Successfully logged on to Vibinus server {hostname}:{port} as {username}")
    print("")
    print(f"To see a list of available commands type: 'list'.")
    print(f"To see what command x does type: 'help x'")

    while True:
        line = await aioconsole.ainput(f'')
        if line == '':
            continue

        # print(f'Sent: {line!r} \n')
        writer.write(line.encode())
        await writer.drain()

        data_b = await reader.read(1000)
        data = data_b.decode()
        print(f'{data}')
        if data == 'closing connection':
            print('Disconnecting from server...')
            writer.close()
            await writer.wait_closed()
            break


if __name__ == '__main__':
    username = 'admin'
    password = 'hemmeligt'
    # hostname = '127.0.0.1'
    hostname = '192.168.165.154'
    port = '8888'
    asyncio.run(vibinus_game_client(hostname,port,username,password))