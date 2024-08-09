import discord
from discord.ext import commands
import os
import yt_dlp
import asyncio
import re
import threading
from AI_Model import AI_Arisu, AI_Arisu_Everything, AI_Arisu_Maid


token = os.environ.get("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True

sailamqualon_lock = asyncio.Lock()
lock = asyncio.Lock()
is_playing = False
is_looping = False
queue = []

lyrics_sai_lam_qua_lon = [
    (0, "### Sai lầm `quá` lớ... ~~sai sai~~ **sai** *sai* ... ***sai*** `lầm` **quá** lớn"),
    (3.0, "## `Anh` __thua__ `nên` anh ~~chịu~~"),
    (1.9, "### ~~Ngục~~ __tù__ `tối` tăm"),
    (1, "Giam `anh` *tuổi* ~~thanh xuân~~"),
    (1.4, "# Mà ~~người~~ *nhẫn* tâm `sao` em đi ~~vội vàng~~"),
    (3.0, "~~Người~~ `đành` sang ~~ngang~~"),
    (0.9, "-# Bỏ *anh* __trong__ ngục `tối`...")
]

lyrics_van_de_ky_nang = [
    (0, "### Hả"),
    (0.9, "# `Mày` nói cái `đéo` gì ~~cơ~~?"),
    (1.0, "### ~~Cái gì~~ __cơ__ `?`"),
    (0.3, "Vấn `đề` *kĩ* ~~năng gì~~ **cơ**"),
    (0.9, "# Địt mẹ mày mày *ngu* thì nói mẹ đi"),
    (0.8, "## Địt con mẹ mày ~~đừng có nói như~~ thế nhá"),
    (0.8, "Địt con `mẹ` mày `đừng` có xàm ~~lồn~~"),
    (0.8, "# Địt `con` mẹ ~~mày~~ bây *giờ* mày thua tao"),
    (0.8, "Bây `giờ` **địt** con `mẹ` mày gáy **cái** đéo gì"),
    (0.9, "# Lói"),
    (0.6, "## ~~`Lói` nhanh~~")
]

bot = commands.Bot(command_prefix='arisu!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if bot.user in message.mentions:
        if message.content == r'<@1266718573858918572>':
            await message.channel.send("Do you need help, Master?")
        else:
            await message.channel.send(AI_Arisu_Maid.reply(message.content.replace(r'<@1266718573858918572>', r'Arisu')))
    await bot.process_commands(message)
    
@bot.command(name='join')
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not connected to a voice channel.")

@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send("I am not connected to a voice channel.")

@bot.command(name='sailamqualon!')
async def play(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            return
    async with sailamqualon_lock:
        ctx.voice_client.stop()
        source = discord.FFmpegPCMAudio(r'C:\Users\LENOVO\Downloads\y2mate.com - Sai lầm của Arisu quá lớn creDyumusic.mp3')
        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
        threading.Thread(target=lambda: bot.loop.create_task(send_lyrics(ctx, lyrics_sai_lam_qua_lon))).start()

@bot.command(name='vandekinang')
async def play(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            return
    async with sailamqualon_lock:
        ctx.voice_client.stop()
        source = discord.FFmpegPCMAudio(r'C:\Users\LENOVO\Downloads\utomp3.com - Arisu said Cái j cơ Vấn đề kĩ năng Bản đồ họa 4K.mp3')
        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
        threading.Thread(target=lambda: bot.loop.create_task(send_lyrics(ctx, lyrics_van_de_ky_nang))).start()

@bot.command(name='play')
async def play(ctx, url: str):
    async with lock:
        url = clean_youtube_url(url)
        if not ctx.voice_client:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                await channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                return

    def download_audio(url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'noplaylist': True,  # Download single video, not playlist
            'concurrent_fragment_downloads': 5,  # Number of fragments to download concurrently (HTTP chunking)
            'quiet': False,  # Suppress output to improve performance slightly
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return extension_validation(ydl.prepare_filename(info)), extension_validation(ydl.prepare_filename(info))[10:].replace('.mp3', '')

    def get_audio_file_path(url):
        ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s',
                    'noplaylist': True,
                    'quiet': False,}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return extension_validation(ydl.prepare_filename(info))

    audio_file_path = get_audio_file_path(url)
    if os.path.exists(audio_file_path):
        audio_file = audio_file_path
        name = os.path.basename(audio_file).replace('.mp3', '')
    else:
        audio_file, name = download_audio(url)

    queue.append((audio_file, name))

    if not is_playing:
        threading.Thread(target=lambda: bot.loop.create_task(play_next(ctx))).start()

@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
    else:
        await ctx.send("No audio is playing.")

@bot.command(name='resume')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
    else:
        await ctx.send("Audio is not paused.")

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    else:
        await ctx.send("No audio is playing.")

@bot.command(name='siu')
async def siu(ctx):
    await ctx.send("Siuuuuuuu")

@bot.command(name='loop')
async def loop(ctx):
    global is_looping
    is_looping = not is_looping
    await ctx.send(f"Looping has been {'enabled' if is_looping else 'disabled'}.")

@bot.command(name='skip')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped the current song.")
    else:
        await ctx.send("No song is currently playing.")

@bot.command(name='view')
async def view(ctx):
    if queue:
        queue_list = "\n".join([f"{i + 1}. {name}" for i, (_, name) in enumerate(queue)])
        await ctx.send(f"Current queue:\n{queue_list}")
    else:
        await ctx.send("The queue is currently empty.")

@bot.command(name='chat')
async def chat(ctx, *, input:str):
    await ctx.send(AI_Arisu.reply(input))

@bot.command(name='ask')
async def ask(ctx, *, input:str):
    await ctx.send(AI_Arisu_Everything.reply(input))

@bot.command(name='help')
async def help_command(ctx):
    help_text = '''
`arisu!join` - Join the voice channel.
`arisu!leave` - Leave the voice channel.
`arisu!play <url>` - Play a song from a YouTube URL.
`arisu!sailamqualon!` - Anh thua nên anh chịu
`arisu!vandekinang` - Gì cơ?
`Arisu!pause` - Pause the current song.cr
`arisu!resume` - Resume the paused song.
`arisu!stop` - Stop the current song.
`arisu!skip` - Skip the current song.
`arisu!loop` - Toggle looping of the current song.
`arisu!view` - View the current queue.
`arisu!chat <text>` - Talk with arisu
`arisu!ask <text>` - Ask arisu anything
`arisu!help` - Show this help message.
'''
    await ctx.send(help_text)

def clean_youtube_url(url):
    # Remove the playlist parameters from the URL
    clean_url = re.sub(r'&list=[^&]+', '', url)
    clean_url = re.sub(r'&start_radio=[^&]+', '', clean_url)
    return clean_url

def extension_validation(filename):
    name, _ = filename.rsplit('.', 1)
    return name + '.mp3'

async def send_lyrics(ctx, lyrics):
    for timestamp, line in lyrics:
        await asyncio.sleep(timestamp)
        await ctx.send(line)

async def play_next(ctx):
    global is_playing

    if queue:
        is_playing = True
        audio_file, name = queue.pop(0)
        source = discord.FFmpegPCMAudio(audio_file)
        await ctx.send(f'Playing **{name}**')
        ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(on_audio_finished(ctx, e, audio_file)))
    else:
        is_playing = False

async def on_audio_finished(ctx, error, audio_file):
    if error:
        print(f'Error playing audio: {error}')
    if is_looping:
        source = discord.FFmpegPCMAudio(audio_file)
        ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(on_audio_finished(ctx, e, audio_file)))
    else:
        threading.Thread(target=lambda: bot.loop.create_task(play_next(ctx))).start()

if __name__ == '__main__':
    bot.run(token)
