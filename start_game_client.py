import asyncio

from src.client import vibinus_game_client

if __name__ == '__main__':
    username = 'private'
    password = '123'
    # hostname = '127.0.0.1'
    hostname = '192.168.165.154'
    port = '8888'
    asyncio.run(vibinus_game_client(hostname,port,username,password))