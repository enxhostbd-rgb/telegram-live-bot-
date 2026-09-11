import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.raw import types
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioQuality, MediaStream
from sessions import SESSIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveAutoJoiner")

# আপনার আসল API_ID এবং API_HASH বসান
API_ID = 38606057  
API_HASH = "2d261a3744539d81a0ae4e6ee7693373"  
TARGET_CHANNEL = -1003668550531

app = Client("main_monitor", api_id=API_ID, api_hash=API_HASH)

worker_clients = []
tgcalls_clients = []

async def init_workers():
    for index, session_str in enumerate(SESSIONS):
        client = Client(
            name=f"worker_{index}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_str,
            in_memory=True
        )
        await client.start()
        worker_clients.append(client)
        
        call_app = PyTgCalls(client)
        await call_app.start()
        tgcalls_clients.append((client, call_app))
        logger.info(f"Worker {index + 1} Ready.")

async def join_live_stream(channel_id):
    logger.info(f"Live detected in {channel_id}! Joining accounts...")
    for client, call_app in tgcalls_clients:
        try:
            try:
                await client.join_chat(channel_id)
            except Exception:
                pass

            await call_app.play(
                channel_id,
                MediaStream(
                    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                    video_flags=MediaStream.Flags.IGNORE,
                    audio_parameters=AudioQuality.LOW
                )
            )
            logger.info(f"Account {client.me.first_name} joined the live.")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Failed to join: {e}")

@app.on_message(filters.chat(TARGET_CHANNEL) & filters.service)
async def service_message_handler(client, message):
    if message.video_chat_started or message.voice_chat_started:
        await join_live_stream(message.chat.id)

@app.on_raw_update()
async def raw_update_handler(client, update, users, chats):
    if isinstance(update, types.UpdateGroupCall):
        call = update.call
        if not call.discarded:
            asyncio.create_task(join_live_stream(TARGET_CHANNEL))

async def main():
    await app.start()
    logger.info("Main Monitor Started...")
    await init_workers()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
