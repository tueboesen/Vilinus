import asyncio

from src.game import Vibinus


class VibinusServer:

    def __init__(self,game: Vibinus):
        self.game = game

    async def close_connection(self,writer,message,user_id=None):
        writer.write(message.encode())
        await writer.drain()
        writer.close()
        addr = writer.get_extra_info('peername')
        if user_id is None:
            username = ''
        else:
            username = self.game.usernames[user_id]
        print(f"{message} to {username} connected from {addr!r}")
        await writer.wait_closed()

    async def client_authentication(self,reader,writer):
        data = await reader.read(100)
        username = data.decode()
        if username in self.game.usernames:
            idx = self.game.usernames.index(username)
            writer.write("username accepted".encode())
            await writer.drain()
        else:
            message = f"username: {username} not accepted"
            await self.close_connection(writer, message)
            return -1

        data = await reader.read(100)
        password = data.decode()
        if password == self.game.passwords[idx]:
            writer.write("password accepted".encode())
            await writer.drain()
        else:
            message = "password not accepted"
            await self.close_connection(writer, message)
            return -1
        return idx


    async def game_server(self,reader, writer):
        user_id = await self.client_authentication(reader, writer)
        addr = writer.get_extra_info('peername')
        print(f"{self.game.usernames[user_id]} logged on from {addr!r}")

        while True:
            data = await reader.read(100)
            command = data.decode()
            if command == 'quit':
                await self.close_connection(writer, 'closing connection', user_id)
                break
            else:
                try:
                    message = self.game.parse_command(user_id, command)
                except Exception as e:
                    message = f"command failed. {e}"

                addr = writer.get_extra_info('peername')
                print(f"Received {message!r} from {addr!r}")

                writer.write(message.encode())
                await writer.drain()

    async def main(self):
        server = await asyncio.start_server(self.game_server, '127.0.0.1', 8888)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Serving on {addrs}')

        async with server:
            await server.serve_forever()


def run_server_async(server):
    asyncio.run(server.main())

if __name__ == '__main__':
    info = 'test'
    vib = VibinusServer(info)
