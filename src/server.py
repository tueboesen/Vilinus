import asyncio
import logging
import socket

from src.game import Vibinus
from src.utils import RequirementsNotMetError, InsufficientAccessError
logger = logging.getLogger('vibinus')


class VibinusServer:

    def __init__(self,game: Vibinus, ip_address=None, port=8888):
        self.game = game
        if ip_address is None:
            self.ip = socket.gethostbyname(socket.gethostname())
        else:
            self.ip = ip_address
        self.port = port

    async def close_connection(self,writer,message,user_id=None):
        writer.write(message.encode())
        await writer.drain()
        writer.close()
        addr = writer.get_extra_info('peername')
        if user_id is None:
            username = ''
        else:
            username = self.game.usernames[user_id]
        logger.debug(f"{message} to {username} connected from {addr!r}")
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
        username = self.game.usernames[user_id]
        logger.debug(f" {username} logged on from {addr!r}")
        n_blanks = 0

        while True:
            data = await reader.read(100)
            command = data.decode()
            if command == 'quit':
                logger.debug(f"Received: {command} from {username}")
                await self.close_connection(writer, 'closing connection', user_id)
                break
            elif command == "":
                if n_blanks >= 10:
                    await self.close_connection(writer, 'closing connection', user_id)
                    break
                n_blanks += 1
                writer.write("".encode())
                await writer.drain()
                continue
            else:
                logger.debug(f"Received: {command} from {username}")
                n_blanks = 0
                try:
                    args = command.split(" ")
                    message = self.game.command_selector(user_id, args)
                except NotImplementedError as e:
                    message = f"Command not recognized: {e}"
                except (InsufficientAccessError, RequirementsNotMetError, AssertionError) as e:
                    message = f"Command failed: {e}"
                except Exception as e:
                    message = f"Something went wrong. {e}"
                logger.debug(f"Returning: {message!r} to {username}")
                writer.write(message.encode())
                await writer.drain()
        # return await asyncio.gather(return_exceptions=True)
            # print("Bastard closed the connection in a not nice way!")
            # await self.close_connection(writer, 'closing connection', user_id)

    async def main(self):
        server = await asyncio.start_server(self.game_server, self.ip, self.port)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logger.info(f'Serving on {addrs}')

        async with server:
            try:
                await server.serve_forever()
            except:
                print("you are here")


def run_server_async(server):
    asyncio.run(server.main())

if __name__ == '__main__':
    info = 'test'
    vib = VibinusServer(info)
