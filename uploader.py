from asyncio import Queue, set_event_loop_policy, WindowsSelectorEventLoopPolicy
from aiohttp import ClientSession
from base64 import b64encode
from os import listdir
from stdiomask import getpass
import anyio


class Uploader(object):
    def __init__(self, path: str, guild: str, token: str) -> None: 
        self.queue = Queue()
        self.guild = guild
        self.token = token
        
        for i in listdir(path):
            if "png" in i or "jpg" in i or "gif" in i:
                self.queue.put_nowait(path + "/" + i)
            else:
                print(f"invalid file type: [{i}]")
        
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        anyio.run(self.main)
    
    async def worker(self) -> None:
        async with ClientSession() as session:
            while not self.queue.empty():
                item = self.queue.get_nowait()
                await self.upload(item, session)
                self.queue.task_done()
            await session.close()
    
    async def main(self) -> None:
        self.exist = set()
        async with ClientSession() as session:
            async with session.get(f"https://discord.com/api/v9/guilds/{self.guild}/emojis", headers={"Authorization": self.token, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9003 Chrome/91.0.4472.164 Electron/13.4.0 Safari/537.36"}) as resp:
                body = await resp.json()
                for o in body:
                    self.exist.add(o["name"])
                await session.close()

        async with anyio.create_task_group() as n:
            for _ in range(10):
                n.start_soon(self.worker)
    
    async def upload(self, item: str, session: ClientSession) -> None:
        name = item.split("/")[-1].removesuffix(".png").removesuffix(".jpg").removesuffix(".gif")
        if name in self.exist:
            print(f"skipped: [{name}]")
            return
        raw = open(item, 'rb').read()
        encoded = b64encode(raw).decode()

        data = {"image": f"data:image/gif;base64,{encoded}", "name": name}
        
        headers = {
            "Authorization": self.token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9003 Chrome/91.0.4472.164 Electron/13.4.0 Safari/537.36",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Content-Length": str(len(str(data)))
        }
        
        async with session.post(f"https://discord.com/api/v9/guilds/{self.guild}/emojis", headers=headers, json=data) as resp:
            _ = await resp.text()
            print(f"uploaded: [{name}]")


if __name__ == "__main__":
    path = input("file path to folder with emojis: ").strip('"')
    guild = input("guild id: ")
    token = getpass("discord token: ")
    Uploader(path, guild, token)
