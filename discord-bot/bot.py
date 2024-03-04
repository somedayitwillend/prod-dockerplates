from unidecode import unidecode
from html2image import Html2Image
import handle, config, requests, json, asyncio, discord, re
from datetime import datetime
from discord import app_commands

async def send_message(channel, name, rio):
    try:
        response = handle.handle_response(name)
        hti = Html2Image(custom_flags=['--no-sandbox'], output_path=config.ROOT_PATH, size=(620, 250))
        hti.browser_executable = "/usr/bin/google-chrome"
        hti.screenshot(html_str=response['html'], save_as=unidecode(name) + '.jpg')
        data = {
			'name': name,
			'rio': response['rio']
		}
        if rio == -1 or rio < response['rio']:
            with open(config.ROOT_PATH + unidecode(name) + '.jpg', 'rb') as f:
                picture = discord.File(f, description=json.dumps(data))
                await channel.send(file=picture)
            
            return True
        return False
    except Exception as e:
        print(e)

def run_discord_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)
    
    global checkCount
    checkCount = 0
    
    async def run_blocking():
        func = await check_refresh()
        await client.loop.run_in_executor(None, func)
    
    async def refresh_player(name):
        filenameRoot = config.ROOT_PATH
        if filenameRoot.startswith("/"):
            filenameRoot = filenameRoot[1:]
        filenameRoot = filenameRoot.replace("/", "_")
        filenameRoot = filenameRoot.replace(":", "")
        channels = client.get_all_channels()
        for channel in channels:
            if channel.name == "scores":
                messages = [message async for message in channel.history(limit=None)]
                rio = -1
                msgMaybeDelete = None
                for msg in messages:
                    if len(msg.attachments) == 0:
                        await msg.delete()
                    elif msg.attachments[0].filename.startswith(filenameRoot + unidecode(name)):
                        msgMaybeDelete = msg
                        data = json.loads(msg.attachments[0].description)
                        rio = data['rio']
                        
                shouldDelete = await send_message(channel, name, rio)
                if shouldDelete and msgMaybeDelete != None:
                    await msgMaybeDelete.delete()
                        
    async def get_messages(channelName):
        channels = client.get_all_channels()
        for channel in channels:
            if channel.name == channelName:
                return [message async for message in channel.history(limit=None)]
    
    async def auto_refresh():
        print("Refreshing characters...")
        messages = await get_messages('scores')
        for msg in messages:
            if len(msg.attachments) > 0 and msg.attachments[0].description:
                data = json.loads(msg.attachments[0].description)
                requests.post('https://raider.io/api/crawler/characters', data='{"realmId":686,"realm":"Ragnaros","region":"eu","character":"' + data['name'] + '"}')
                
    async def youtube_refresh():
        try:
            response = requests.get(f"https://www.googleapis.com/youtube/v3/search?key={config.API_KEY}&channelId=UCkgjR2ngHM01i1SEZZWGV1A&part=snippet,id&order=date&maxResults=5")
            videos = json.loads(response.text)
            messages = await get_messages('daily-wow')
            channel = None
            videos['items'].reverse()
            for video in videos['items']:
                videoExist = False
                for msg in messages:
                    if channel == None:
                        channel = msg.channel
                    
                    if msg.content == f"https://youtube.com/watch?v={video['id']['videoId']}":
                        videoExist = True
                
                if not videoExist and channel != None:
                    await channel.send(f"https://youtube.com/watch?v={video['id']['videoId']}")
        except Exception as e:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {e}")
        
    async def check_refresh():
        try:
            global checkCount
            checkCount = checkCount + 1
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Checking...")
            messages = await get_messages('scores')
            for msg in messages:
                if len(msg.attachments) > 0 and msg.attachments[0].description:
                    data = json.loads(msg.attachments[0].description)
                    await refresh_player(data['name'])
        except Exception as e:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {e}")
        
        try:
            await asyncio.sleep(60)
            if checkCount >= 60:
                await auto_refresh()
                await youtube_refresh()
                checkCount = 0
                
            await run_blocking()
        except Exception as e:
            await run_blocking()
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {e}")
    
    @tree.command(name="refresh")
    async def refresh(interaction, name: str):
        await interaction.response.send_message("Accepted")
        await refresh_player(name)
        
    @tree.command(name="route")
    async def route(interaction, mdt_string: str):
        try:
            await interaction.response.send_message("Route created!")
            await interaction.delete_original_response()
            response = requests.get('https://keystone.guru/')
            csrfTokenRe = re.search('csrfToken = "(.*)";', response.text)
            response = requests.post('https://keystone.guru/login', data={"_token": csrfTokenRe.groups(1)[0], "email": config.KEYSTONE_GURU_EMAIL, "password": config.KEYSTONE_GURU_PASSWORD})
            cookies = response.cookies.get_dict()
            baseCokie = f"XSRF-TOKEN={cookies['XSRF-TOKEN']}; laravel_session={cookies['laravel_session']};"
            headers = {
                'Host' : 'keystone.guru',
                'Content-Type' : 'application/x-www-form-urlencoded',
                'Content-Length' : str(len(csrfTokenRe.groups(1)[0]) + len(mdt_string) + 22),
                'Cookie': baseCokie,
			}
            response = requests.post(f"https://keystone.guru/new/mdtimport", data={"_token": csrfTokenRe.groups(1)[0], "import_string": mdt_string}, headers=headers)
            
            responseUrlSplit = response.url.split('/')
            if len(responseUrlSplit) > 4:
                headers['Content-Length'] = "21"
                asd = requests.post(f"https://keystone.guru/ajax/{responseUrlSplit[5]}/publishedState", data={"published_state": "world"}, headers=headers)
                asd = "asd"
            
            await interaction.channel.send(response.url)
        except Exception as e:
            await interaction.response.send_message("Route not created!")
            await interaction.delete_original_response()
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {e}")
        
    @client.event
    async def on_ready():
        await tree.sync()
        await run_blocking()
        print(f'{client.user} is now running!')
    
    client.run(config.TOKEN)