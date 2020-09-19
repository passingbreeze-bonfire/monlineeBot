import asyncio, io, os, botTool, youtube_dl, sys
#
# songlist = []
#
# async def getflist():
#     for file in os.listdir("./music"):
#         if file.endswith(".mp3"):
#             # print(await botTool.musicfname("./music/" + file))
#             songlist.append(await botTool.musicfname("./music/" + file))
#
# async def main():
#     await getflist()
#     for song in songlist:
#         print(song)

class listStream:
    def __init__(self):
        self.data=[]
    async def write(self,s):
        self.data.append(s)

async def getyoutube(url):
    ydl_opt = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': u'music/%(playlist_index)s-%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
    }
    # sys.stdout = chkstr = listStream()
    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            result = info['entries']
            for i, item in enumerate(result):
                print(info['entries'][i]['title'])
        else :
            print(info['title'], info['webpage_url'])
async def main():
    url = input()
    a = await getyoutube(url)
    print(a, isinstance(a, int))

asyncio.run(main())