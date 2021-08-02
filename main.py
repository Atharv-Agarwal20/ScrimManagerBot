import discord
from discord.ext import commands
import random
import datetime as dt
from datetime import datetime
import pytz
import pendulum
import asyncio
import re
from webserver import keep_alive
import os
from replit import db
from asyncio import TimeoutError
from discord_components import *

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix = '.', intents=intents)
ist = pytz.timezone('Asia/Calcutta')

@client.event
async def on_ready():
    DiscordComponents(client)
    print("Bot is online")
    await client.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = ".help"))

# db["scrim"] = {"clan": [],"unix": [],"mode": []}

class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        channel = self.get_destination()
        embed = discord.Embed(
            title = "Zenith Commands",
            colour = 0x54f542
        )
        embed.add_field(name = ".scrim", value = "Start a scrim request Q&A\nRequirements: **DM Only**", inline = False)
        embed.add_field(name = ".queue", value = "List of scheduled scrims (maximum 8 at a time)", inline = False)
        embed.add_field(name = ".remove <Scrim ID>", value = "Removes a scrim from the queue\nRequirements: **Scrim manager** role", inline = False)
        embed.add_field(name = ".clear", value = "Clears entire queue\nRequirements: **Scrim manager** role", inline = False)
        embed.add_field(name = ".scrimlog <text channel mention>", value = "Change or set scrim log channel\nRequirements: **Manage Server** permission")
        await channel.send(embed=embed)

client.help_command = MyHelp()

@client.command()
@commands.guild_only()
@commands.has_permissions(manage_guild = True)
async def scrimlog(ctx, channel:discord.TextChannel):
  db["log_channel"] = channel.id
  await ctx.send(f'Scrim logs will be sent to <#{channel.id}>')

@client.command()
@commands.dm_only()
async def scrim(ctx):
  entries = db["scrim"]
  if len(list(entries["clan"])) < 9:
    try:
      author_name = ctx.author.name
      author_id = ctx.author.id
      author_discriminator = ctx.author.discriminator
      author_avatar = ctx.author.avatar
      await ctx.send("Answer the following questions **truthfully and carefully**\nAll questions timeout after 1 minute")
      await ctx.send("What is your clan name?")
      clan = await client.wait_for('message',check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout = 60)
      await ctx.send("What is your clan leader's discord username (with discriminator)")
      leader = await client.wait_for('message',check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout = 60)
      pattern = "(?!(discordtag|here|everyone)).[^\@\#\:]{1,31}#[\d]{4}"
      if (re.fullmatch(pattern, leader.content)):
        await ctx.send("What is your preferred date (in **DD/MM/YYYY** format) for the scrim in **(According to IST timezone)**")
        _date = await client.wait_for('message',check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout = 60)
        dateContent = _date.content

        slashCheck = re.findall("\/", dateContent)

        if len(slashCheck) == 2:
            day,month,year = dateContent.split('/')

            isValidDate = True
            try:
                dt.datetime(int(year),int(month),int(day))
            except ValueError :
                isValidDate = False

            if(isValidDate):
                # print ("Input date is valid ..")
                await ctx.send("What is your preferred time (in **HH:MM __24 hour__** format) for the scrim **(According to IST timezone)**")
                _time = await client.wait_for('message',check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout = 60)
                timeContent = _time.content
                colonCheck = re.findall("\:", timeContent)

                if len(colonCheck) == 1:
                    hour,minutes = timeContent.split(':')

                    isValidTime = True

                    try:
                        dt.time(int(hour),int(minutes))
                    except ValueError:
                        isValidTime = False

                    if(isValidTime):
                        date_time = f'{dateContent} - {timeContent}:00'
                        date_time = dt.datetime.strptime(date_time, "%d/%m/%Y - %H:%M:%S")
                        date_time = dt.datetime.timestamp(date_time)
                        unix = int(date_time) - 19800
                        if unix > 0:
                          m = await ctx.send("Choose mode", components=[Select(max_values=4,min_values=1,placeholder="Choose game modes", options=[
                            SelectOption(
                              label = "Search and Destroy",
                              value = "snd"
                            ),
                            SelectOption(
                              label = "Team Deathmatch",
                              value = "tdm"
                            ),
                            SelectOption(
                              label = "Hardpoint",
                              value = "hpt"
                            ),
                            SelectOption(
                              label = "Domination",
                              value = "dom"
                            )
                          ])])
                          def check(interaction):
                            return ctx.author == interaction.user and ctx.channel == interaction.channel
                          interaction = await client.wait_for("select_option",check=check,timeout=15)
                          await m.edit(components=[])
                          chosen_modes = []
                          for i in interaction.component:
                            chosen_modes.append(i.label)
                          modes="| "
                          for x in chosen_modes:
                            modes=modes+x+" | "
                          asyncio.sleep(1)
                          await m.edit(modes, components=[])
                          embed = discord.Embed(
                              title = "Scrim challenge",
                              colour = 0xF2EF18
                          )
                          embed.add_field(name = "Challenger Name", value = f'{author_name}#{author_discriminator}', inline = True)
                          embed.add_field(name = "Challenger ID", value = author_id, inline = True)
                          embed.add_field(name = "Clan Name", value = clan.content, inline = True)
                          embed.add_field(name = "Clan Leader Name (Discord)", value = leader.content, inline = True)
                          embed.add_field(name = "Scrim Date", value = _date.content, inline = True)
                          embed.add_field(name = "Scrim Time", value = _time.content, inline = True)
                          embed.add_field(name = "Mode", value = modes, inline = True)
                          embed.add_field(name = "Unix Time", value = unix, inline = True)
                          asyncio.sleep(2)
                          await ctx.send(embed = embed)
                          try:
                            log_channel = db["log_channel"]
                            await ctx.bot.get_channel(log_channel).send(embed = embed)
                          except Exception:
                            demon = client.get_user(712909465011224687)
                            await demon.send("Scrim Log Channel was deleted")
                          information = db["scrim"]
                          information["clan"].append(clan.content)
                          information["unix"].append(unix)
                          information["mode"].append(modes)
                          db["scrim"] = information
                        else:
                          await ctx.send("We cannot travel back in time. Please re-run the command and enter a valid date and time")
                    else:
                        await ctx.send("Time is in invalid format. Please re-run the command and give the time as **HH:MM** in **24 Hour System**\nExample: **15:30**")
                else:
                    await ctx.send("Time is in invalid format. Please re-run the command and give the time as **HH:MM** in **24 Hour System**\nExample: **15:30**")
            else :
                await ctx.send("Date is in invalid format. Please re-run the command and give the date as **DD/MM/YYYY**\nExample: **20/11/2005**")
        else:
            await ctx.send("Date is in invalid format. Please re-run the command and give the date as **DD/MM/YYYY**\nExample: **20/11/2005**")
      else:
        await ctx.send("Discord Username is invalid\nExample of valid username: **DEMØN#6969**")
    except TimeoutError:
      await ctx.send("Timed out")
      try:
        await m.delete()
      except Exception:
        pass
  else:
    await ctx.send("Queue is full. Ask clan admins to free up space")

@client.command()
@commands.guild_only()
async def queue(ctx):
  information = db["scrim"]
  clan = information["clan"]
  unix = information["unix"]
  mode = information["mode"]
  embed = discord.Embed(
    title = "Scrim Queue",
    colour = 0x33B2FF
  )
  for i in range(len(clan)):
    identifier = i+1
    embed.add_field(name = f'#{identifier}\n{clan[i]}', value = f'<t:{unix[i]}>\n**{mode[i]}**\nScrim <t:{unix[i]}:R>', inline = False)
  await ctx.send(embed = embed)

@client.command()
@commands.guild_only()
@commands.has_role("Scrim manager")
async def remove(ctx, iden: int):
  stuff = db["scrim"]
  try:
    del stuff["clan"][iden-1]
    del stuff["unix"][iden-1]
    del stuff["mode"][iden-1]
    db["scrim"] = stuff
    await ctx.send(f'Entry {iden} removed')
  except Exception:
    await ctx.send("Provided ID is either too less or too big")

@client.command()
@commands.guild_only()
@commands.has_role("Scrim manager")
async def clear(ctx):
  information = db["scrim"]
  information["clan"].clear()
  information["unix"].clear()
  information["mode"].clear()
  db["scrim"] = information
  await ctx.send("Schedule cleared")

@client.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.PrivateMessageOnly):
    await ctx.send("This command can only be used in DMs")
  if isinstance(error, commands.NoPrivateMessage):
      await ctx.send("This command cannot be used in DMs")
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Missing required arguments")
  if isinstance(error, commands.MissingPermissions):
    await ctx.send("You are missing required permissions")
  if isinstance(error, commands.MissingRole):
    await ctx.send("You are missing required role")

keep_alive()
my_secret = os.environ['token']
client.run(my_secret)
