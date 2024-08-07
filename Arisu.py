import discord
from discord.ext import commands
import os
import yt_dlp
import asyncio
import re
import threading

token = os.environ.get("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True

sailamqualon_lock = asyncio.Lock()
lock = asyncio.Lock()
is_playing = False
is_looping = False
queue = []
lyrics = [
    (0, "### Sai lầm `quá` lớ... ~~sai sai~~ **sai** *sai* ... ***sai*** `lầm` **quá** lớn"),
    (3.0, "## `Anh` __thua__ `nên` anh ~~chịu~~"),
    (1.9, "### ~~Ngục~~ __tù__ `tối` tăm"),
    (1, "Giam `anh` *tuổi* ~~thanh xuân~~"),
    (1.4, "# Mà ~~người~~ *nhẫn* tâm `sao` em đi ~~vội vàng~~"),
    (3.0, "~~Người~~ `đành` sang ~~ngang~~"),
    (0.9, "-# Bỏ *anh* __trong__ ngục `tối`...")
]

# lyrics_van_de_ky_nang = [
#     (0, "### Sai lầm `quá` lớ... ~~sai sai~~ **sai** *sai* ... ***sai*** `lầm` **quá** lớn"),
#     (3.0, "## `Anh` __thua__ `nên` anh ~~chịu~~"),
#     (1.9, "### ~~Ngục~~ __tù__ `tối` tăm"),
#     (1, "Giam `anh` *tuổi* ~~thanh xuân~~"),
#     (1.4, "# Mà ~~người~~ *nhẫn* tâm `sao` em đi ~~vội vàng~~"),
#     (3.0, "~~Người~~ `đành` sang ~~ngang~~"),
#     (0.9, "-# Bỏ *anh* __trong__ ngục `tối`...")
# ]

bot = commands.Bot(command_prefix='Arisu!', intents=intents, help_command=None)

def clean_youtube_url(url):
    # Remove the playlist parameters from the URL
    clean_url = re.sub(r'&list=[^&]+', '', url)
    clean_url = re.sub(r'&start_radio=[^&]+', '', clean_url)
    return clean_url

def extension_validation(filename):
    name, _ = filename.rsplit('.', 1)
    return name + '.mp3'

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

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
        threading.Thread(target=lambda: bot.loop.create_task(send_lyrics(ctx))).start()

async def send_lyrics(ctx):
    for timestamp, line in lyrics:
        await asyncio.sleep(timestamp)
        await ctx.send(line)

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
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return extension_validation(ydl.prepare_filename(info)), extension_validation(ydl.prepare_filename(info))[10:].replace('.mp3', '')

    def get_audio_file_path(url):
        ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s'}
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

@bot.command(name='help')
async def help_command(ctx):
    help_text = '''
`Arisu!join` - Join the voice channel.
`Arisu!leave` - Leave the voice channel.
`Arisu!play <url>` - Play a song from a YouTube URL.
`Arisu!sailamqualon!` - Anh thua nên anh chịu
`Arisu!vandekinang` - Gì cơ?
`Arisu!pause` - Pause the current song.
`Arisu!resume` - Resume the paused song.
`Arisu!stop` - Stop the current song.
`Arisu!skip` - Skip the current song.
`Arisu!loop` - Toggle looping of the current song.
`Arisu!view` - View the current queue.
`Arisu!help` - Show this help message.
'''
    await ctx.send(help_text)

if __name__ == '__main__':
    bot.run(token)
