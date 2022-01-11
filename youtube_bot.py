import discord
import asyncio
import youtube_dl
import os
import unicodedata
import time

TOKEN = "PLACEHOLDER"
client = discord.Client()

youtube_dl.utils.bug_reports_message = lambda: ''
curr_files = list()

ytdl_format_options_download = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'prefer_ffmpeg': True
}

ytdl_format_options_stream = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes,
}

ffmpeg_options = {
    'options': '-vn',
    #'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl_download = youtube_dl.YoutubeDL(ytdl_format_options_download)
ytdl_stream = youtube_dl.YoutubeDL(ytdl_format_options_stream)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, tomp3=False):
        loop = loop or asyncio.get_event_loop()
        if tomp3:
            data = await loop.run_in_executor(None, lambda: ytdl_download.extract_info(url, download=not stream))
        else:
            data = await loop.run_in_executor(None, lambda: ytdl_stream.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if tomp3 else ytdl.prepare_filename(data)

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
#End

@client.event
async def on_ready():
    pass

@client.event
async def on_message(message):

    if message.content.startswith('~leave'):
        if message.author.voice:
            await leave(message.guild)
        else:
            await message.channel.send('Must be in a VC to kick')

    if message.content.startswith('~play'):
        split = message.content.split(' ')
        if len(split) > 2 or not split[1].startswith('https://'):
            url = ' '.join(split[1:])
        else:
            url = split[1]
        if message.author.voice:
            await play(url, message.author.voice.channel, message.guild)
        else:
            await message.channel.send('Must be in a VC to join')
    
    if message.content.startswith('~tomp3'):
        split = message.content.split(' ')
        if len(split) > 2 or not split[1].startswith('https://'):
            url = ' '.join(split[1:])
        else:
            url = split[1]
        name = await download(url)
        if name:
            try:
                await message.channel.send(file=discord.File(name))
            except Exception as e:
                print(e)
                await message.channel.send('Filesize too big!')
        else:
            await message.channel.send('Could not download. Aww. Sucks.')
    
    if message.content.startswith('~react '):
        await message.delete()
        try:
            time.sleep(0.05)
            msg = message.content.split()
            if len(msg) < 2:
                pass
            else:
                old_msg = await message.channel.history(limit=1).flatten()
                for c in ''.join(msg[1:]):
                    emoji = unicodedata.lookup("REGIONAL INDICATOR SYMBOL LETTER {}".format(c))
                    await old_msg[0].add_reaction(emoji)
        except:
            pass
    
@client.event
async def leave(server):
    for x in client.voice_clients:
            if x.guild == server:
                if x.is_playing():
                    x.stop()
                await x.disconnect()
    files = os.listdir('downloads/')
    for f in files:
        os.remove('downloads/'+f)

@client.event
async def play(url, channel,server):
    global curr_files
    curr_files = list()
    await leave(server)
    vc = await channel.connect()
    player = await YTDLSource.from_url(url)
    vc.play(player)

async def download(url):
    global curr_files
    files = os.listdir('downloads/')
    for f in files:
        os.remove('downloads/'+f)
    curr_files = list()
    await YTDLSource.from_url(url, tomp3=True)
    try:
        files = [x for x in os.listdir('downloads/') if x.endswith(".mp3")]
        #print(files[-1])
        return 'downloads/'+files[-1]
    except:
        return None

client.run(TOKEN)
