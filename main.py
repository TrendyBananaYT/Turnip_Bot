import discord
from discord.ext import commands
import nest_asyncio
from supabase import create_client, Client
import os
import httpx

nest_asyncio.apply()

from dotenv import load_dotenv

load_dotenv("bot-env/var.env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DNS_API = os.getenv("DNS_API")

supabase: Client = create_client(
    "https://vogcadrbfyaaryxakbec.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZvZ2NhZHJiZnlhYXJ5eGFrYmVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMzNDYwOTYsImV4cCI6MjA0ODkyMjA5Nn0.kMkpHtDkPUVQCLsYj0V6fo7L2eQPdCRxIv2XWRSeXHI"
)

application_management = supabase.table("application_management")
registered_nations = supabase.table("registered_nations")

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

apply_channel_cache = {}





"""
  ____                   _         _                 
 |  _ \    ___    __ _  (_)  ___  | |_    ___   _ __ 
 | |_) |  / _ \  / _` | | | / __| | __|  / _ \ | '__|
 |  _ <  |  __/ | (_| | | | \__ \ | |_  |  __/ | |   
 |_| \_\  \___|  \__, | |_| |___/  \__|  \___| |_|   
                  |___/
"""

@bot.slash_command(name="register", description="Register your nation into the **Turnip** Database")
async def register(ctx: discord.ApplicationContext, system: str, nation_id: int):
    system = system.upper()

    if system not in ["PNW", "DNS"]:
        await ctx.respond("Invalid system specified. Please choose either `PNW` or `DNS`.", ephemeral=True)
        return

    update_data = {"discord_user_id": ctx.author.id}
    if system == "PNW":
        update_data["pnw_id"] = nation_id
    elif system == "DNS":
        update_data["dns_id"] = nation_id

    registered_nations.upsert(update_data, on_conflict=["discord_user_id"]).execute()

    await ctx.respond(f"You are now registered to the **Turnip** Database for {system} with Nation ID `{nation_id}`!", ephemeral=True)





"""
 __        __  _             
 \ \      / / | |__     ___  
  \ \ /\ / /  | '_ \   / _ \ 
   \ V  V /   | | | | | (_) |
    \_/\_/    |_| |_|  \___/
"""

@bot.slash_command(name="who", description="Get nation information for a member in the server.")
async def who(ctx: discord.ApplicationContext, system: str, member: discord.Member):
    system = system.upper()

    if system not in ["PNW", "DNS"]:
        await ctx.respond("Invalid system specified. Please choose either `PNW` or `DNS`.", ephemeral=True)
        return

    nation_field = "pnw_id" if system == "PNW" else "dns_id"
    
    result = registered_nations.select(nation_field).eq("discord_user_id", member.id).execute()
    
    if not result.data:
        await ctx.respond(f"{member.mention} is not registered in the database. They need to use `/register` first.", ephemeral=True)
        return

    nation_id = result.data[0].get(nation_field)

    if not nation_id:
        await ctx.respond(f"{member.mention} does not have a {system} nation ID registered.", ephemeral=True)
        return

    if system == "DNS":
        r = httpx.get(f'https://diplomacyandstrifeapi.com/api/nation?APICode={DNS_API}&NationId={nation_id}')
        
        if r.status_code != 200:
            await ctx.respond(f"Failed to fetch data for nation ID `{nation_id}`. Please try again later.", ephemeral=True)
            return

        nation_data = r.json()

        if isinstance(nation_data, list):
            nation_data = nation_data[0] if nation_data else {}

        nation_name = nation_data['NationName']
        leader_name = nation_data["LeaderName"]
        if leader_name == "0":
            leader_name = "None"
            
        population = nation_data["Pop"]
        alliance_name = nation_data["Alliance"]

        embed = discord.Embed(
            title=f"🌍 Nation Information: **{nation_name}**",
            description=f"Details for {member.mention}'s nation:\n\n"
                        f"👑 **Leader**: {leader_name}\n"
                        f"👥 **Population**: {population:,}\n"
                        f"🤝 **Alliance**: {alliance_name}\n",
            color=discord.Color.gold()
        )

        embed.add_field(name="🆔 Nation ID", value=nation_id, inline=True)
        embed.add_field(name="🌍 Nation Name", value=nation_name, inline=True)

        embed.add_field(
            name="━━━━━━━━━━━━━━━━━",
            value="**Additional Information**",
            inline=False
        )

        embed.add_field(name="👑 Leader Name", value=leader_name, inline=True)
        embed.add_field(name="👥 Population", value=f"{population:,}", inline=True)
        embed.add_field(name="🤝 Alliance Name", value=alliance_name, inline=True)

        embed.set_footer(text="Powered by Diplomacy and Strife API", icon_url="https://example.com/api-logo.png")
        embed.set_thumbnail(url="https://example.com/nation-flag.png")

        await ctx.respond(embed=embed, ephemeral=False)

    
    elif system == "PNW":
        await ctx.respond("Hello, World!", ephemeral=False)





"""
                        _   _   _   
    / \     _   _    __| | (_) | |_ 
   / _ \   | | | |  / _` | | | | __|
  / ___ \  | |_| | | (_| | | | | |_ 
 /_/   \_\  \__,_|  \__,_| |_|  \__|
"""

@bot.slash_command(name="audit", description="Audit the nations in the user's alliance.")
async def audit(ctx: discord.ApplicationContext):
    await ctx.defer()
    
    system = application_management.select("*").eq("server_id", ctx.guild.id).execute().data[0].get("system").lower()
    dns_id = registered_nations.select("*").eq("discord_user_id", ctx.user.id).execute().data[0].get("dns_id")
    pnw_id = registered_nations.select("*").eq("discord_user_id", ctx.user.id).execute().data[0].get("pnw_id")
        
    if system == "pnw":
        embed = discord.Embed(
            title="Audit Results",
            description="Hello World",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    elif system == "dns":
        r = httpx.get(f'https://diplomacyandstrifeapi.com/api/nation?APICode={DNS_API}&NationId={dns_id}')

        nation_data = r.json()
        if isinstance(nation_data, list):
            nation_data = nation_data[0] if nation_data else {}
            
        alliance_id = nation_data['AllianceId']
        if not DNS_API or not alliance_id:
            embed = discord.Embed(
                title="⚠️ Missing Configuration",
                description="The DnS API key is not valid.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="Audit Results",
            description=f"Violators in {nation_data['Alliance']}",
            color=discord.Color.red()
        )
        embed.set_footer(text="MMR below 79% violates the current MMR.")

        nations = httpx.get(f"https://diplomacyandstrifeapi.com/api/nation?APICode={DNS_API}").json()

        for nation in nations:
            if nation["AllianceId"] == 1438:
                nation_id = nation["NationId"]
                nation_name = nation["NationName"]
                discord_name = nation["DiscordName"]
                
                buildings = httpx.get(f"https://diplomacyandstrifeapi.com/api/NationBuildings?APICode={DNS_API}&NationId={nation_id}").json()
                
                total_slots = buildings[0]["TotalSlots"]
                
                army_bases = buildings[0]["ArmyBases"]
                air_bases = buildings[0]["AirBases"]
                naval_bases = buildings[0]["NavalBases"]
                
                army_bases_mmr = round((army_bases / (total_slots * 0.08)) * 100, 2)
                naval_bases_mmr = round((naval_bases / (total_slots * 0.04)) * 100, 2)
                air_bases_mmr = round((air_bases / (total_slots * 0.04)) * 100, 2)
                                
                if army_bases_mmr < 79 or naval_bases_mmr < 79 or air_bases_mmr < 79: 
                    print(nation_name)
                    army = f"Army Bases MMR: `{army_bases_mmr}%`" if army_bases_mmr < 79 else ""
                    air = f"Air Bases MMR:   `{air_bases_mmr}%`" if air_bases_mmr < 79 else ""
                    naval = f"Naval Bases MMR: `{naval_bases_mmr}%`" if naval_bases_mmr < 79 else ""
                    
                    output = f"`@{discord_name}`\n{army}\n{air}\n{naval}\n-------------------------"
                                    
                    embed.add_field(name=f"\n\n🌍 Nation: {nation_name}\n", value=output, inline=False)

                
        await ctx.respond(embed=embed, ephemeral=True)
        
    else:
        embed = discord.Embed(
            title="⚠️ Invalid System",
            description="The system is not set to a valid value (PnW or DNS).",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)
   



     
"""
  ____                                       _                      _   _                  _     _                      ____   _                                      _       
 |  _ \   _   _   _ __    __ _    ___       / \     _ __    _ __   | | (_)   ___    __ _  | |_  (_)   ___    _ __      / ___| | |__     __ _   _ __    _ __     ___  | |  ___ 
 | |_) | | | | | | '__|  / _` |  / _ \     / _ \   | '_ \  | '_ \  | | | |  / __|  / _` | | __| | |  / _ \  | '_ \    | |     | '_ \   / _` | | '_ \  | '_ \   / _ \ | | / __|
 |  __/  | |_| | | |    | (_| | |  __/    / ___ \  | |_) | | |_) | | | | | | (__  | (_| | | |_  | | | (_) | | | | |   | |___  | | | | | (_| | | | | | | | | | |  __/ | | \__ \
 |_|      \__,_| |_|     \__, |  \___|   /_/   \_\ | .__/  | .__/  |_| |_|  \___|  \__,_|  \__| |_|  \___/  |_| |_|    \____| |_| |_|  \__,_| |_| |_| |_| |_|  \___| |_| |___/
                         |___/                     |_|     |_|
""" 

@bot.slash_command(name="purge_application_channels", description="Deletes all of the current Application Channels in the server.")
async def purge_application_channels(ctx: discord.ApplicationContext):
    server_data = application_management.select("interview_channels").eq("server_id", ctx.guild.id).execute()

    if not server_data.data:
        embed = discord.Embed(
            title="⚠️ No Channels to Purge",
            description="No application channels found for this server.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    interview_channels = server_data.data[0].get("interview_channels", [])

    for channel_id in interview_channels:
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            await channel.delete()

    application_management.update(
        {"interview_channels": []}
    ).eq("server_id", ctx.guild.id).execute()

    embed = discord.Embed(
        title="✅ Purge Complete",
        description="All application channels have been deleted.",
        color=discord.Color.green()
    )
    await ctx.respond(embed=embed, ephemeral=True)
   



 
"""
 __     __          _          
 \ \   / /   ___   | |_    ___ 
  \ \ / /   / _ \  | __|  / _ \
   \ V /   | (_) | | |_  |  __/
    \_/     \___/   \__|  \___|
""" 

@bot.slash_command(name="vote", description="Start the voting process for an interview channel.")
async def vote(interaction: discord.Interaction, channel: discord.TextChannel):
    server_id = interaction.guild.id
    server_data = application_management.select("*").eq("server_id", server_id).execute().data
    if not server_data:
        embed = discord.Embed(
            title="⚠️ Server Data Not Found!",
            description="The server is not set up for applications. Please contact an admin.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return


    interview_channels = application_management.select("*").eq("server_id", server_id).execute().data[0].get("interview_channels")
    if channel.id not in interview_channels:
        embed = discord.Embed(
            title="⚠️ Invalid Interview Channel",
            description=f"{channel.mention} is not a valid interview channel.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return


    interviewer_role_id = application_management.select("*").eq("server_id", server_id).execute().data[0].get("interviewer_role")
    if not interviewer_role_id:
        embed = discord.Embed(
            title="⚠️ Interviewer Role Not Set",
            description="Please set the interviewer role using `/set_interviewer_role`.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    interviewer_role = interaction.guild.get_role(interviewer_role_id)
    if not interviewer_role:
        embed = discord.Embed(
            title="⚠️ Role Error",
            description="The interviewer role could not be found. Please contact an admin.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await channel.set_permissions(
        interviewer_role, 
        read_messages=True, 
        send_messages=False, 
        add_reactions=False
    )
    
    interviewer_channel_id = application_management.select("*").eq("server_id", server_id).execute().data[0].get("interviewer_channel_id")

    interviewer_channel = interaction.guild.get_channel(interviewer_channel_id)
    threads = interviewer_channel.threads
    archived_threads = [t async for t in interviewer_channel.archived_threads(limit=50)]  # Fetch archived threads

    all_threads = list(threads) + archived_threads

    expected_thread_name = f"{channel.name}".lower().strip()

    thread = next(
        (t for t in all_threads if t.name.lower().strip() == expected_thread_name),
        None
    )

    if not thread:
        embed = discord.Embed(
            title="⚠️ No Matching Thread Found",
            description=f"No thread named '{expected_thread_name}' exists in this channel.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await thread.edit(locked=False)
    
    message = await thread.send(f"{interviewer_role.mention}, the thread has been unlocked for voting.")

    await message.add_reaction("✅")
    await message.add_reaction("❌")
    
    await interaction.response.send_message(f"The thread '{thread.name}' has been unlocked.", ephemeral=True)

    embed = discord.Embed(
        title="✅ Voting Opened",
        description=f"The voting process has been opened for {channel.mention}.\n"
                    f"The discussion thread {thread.mention} is now unlocked.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)





"""
               _                                 _                      
  ___    ___  | |_           ___   _   _   ___  | |_    ___   _ __ ___  
 / __|  / _ \ | __|         / __| | | | | / __| | __|  / _ \ | '_ ` _ \ 
 \__ \ |  __/ | |_          \__ \ | |_| | \__ \ | |_  |  __/ | | | | | |
 |___/  \___|  \__|         |___/  \__, | |___/  \__|  \___| |_| |_| |_|
                                   |___/
""" 

@bot.slash_command(name="set_system", description="Set the system for this server (PNW or DNS).")
async def set_system(ctx: discord.ApplicationContext, system: str):
    system = system.upper()

    if system not in ["PNW", "DNS"]:
        await ctx.respond("Invalid system specified. Please choose either `PNW` or `DNS`.", ephemeral=True)
        return

    application_management.upsert(
        {
            "server_id": ctx.guild.id,
            "system": system,
        },
        on_conflict=["server_id"]
    ).execute()

    embed = discord.Embed(
        title="✅ System Set",
        description=f"The system has been set to {system} for this server.",
        color=discord.Color.green()
    )
    await ctx.respond(embed=embed, ephemeral=True)





"""
  ____           _       ___           _                           _                       ____            _        
 / ___|    ___  | |_    |_ _|  _ __   | |_    ___   _ __  __   __ (_)   ___  __      __   |  _ \    ___   | |   ___ 
 \___ \   / _ \ | __|    | |  | '_ \  | __|  / _ \ | '__| \ \ / / | |  / _ \ \ \ /\ / /   | |_) |  / _ \  | |  / _ \
  ___) | |  __/ | |_     | |  | | | | | |_  |  __/ | |     \ V /  | | |  __/  \ V  V /    |  _ <  | (_) | | | |  __/
 |____/   \___|  \__|   |___| |_| |_|  \__|  \___| |_|      \_/   |_|  \___|   \_/\_/     |_| \_\  \___/  |_|  \___|
""" 

@bot.slash_command(name="set_interviewer_role", description="Set the interviewer role for application voting.")
async def set_interviewer_role(interaction: discord.Interaction, role: discord.Role):
    server_id = interaction.guild.id
    application_management.upsert(
        {"server_id": server_id, "interviewer_role": role.id}, 
        on_conflict=["server_id"]
    ).execute()

    embed = discord.Embed(
        title="✅ Interviewer Role Set",
        description=f"The interviewer role has been set to {role.mention}.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)





"""
  ____           _          _                      _              ____   _                                      _ 
 / ___|    ___  | |_       / \     _ __    _ __   | |  _   _     / ___| | |__     __ _   _ __    _ __     ___  | |
 \___ \   / _ \ | __|     / _ \   | '_ \  | '_ \  | | | | | |   | |     | '_ \   / _` | | '_ \  | '_ \   / _ \ | |
  ___) | |  __/ | |_     / ___ \  | |_) | | |_) | | | | |_| |   | |___  | | | | | (_| | | | | | | | | | |  __/ | |
 |____/   \___|  \__|   /_/   \_\ | .__/  | .__/  |_|  \__, |    \____| |_| |_|  \__,_| |_| |_| |_| |_|  \___| |_|
                                  |_|     |_|          |___/
""" 

@bot.slash_command(name="set_apply_channel", description="Set the channel where the application message will be sent.")
async def set_apply_channel(ctx: discord.ApplicationContext, channel: discord.TextChannel):
    button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)

    async def button_callback(interaction: discord.Interaction):
        if interaction.user != ctx.user:
            await interaction.response.send_message("You are not allowed to confirm this action.", ephemeral=True)
            return

        application_management.upsert(
            {
                "server_id": ctx.guild.id,
                "apply_channel_id": channel.id,
            },
            on_conflict=["server_id"]
        ).execute()

        apply_channel_cache[ctx.guild.id] = channel.id

        await channel.purge(limit=100)
        await send_apply_message(channel)

        embed = discord.Embed(
            title="✅ Application Channel Set",
            description=f"The application message has been sent to {channel.mention}.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    button.callback = button_callback
    view = discord.ui.View()
    view.add_item(button)

    embed = discord.Embed(
        title="⚠️ Confirm Apply Channel",
        description=f"Are you sure you want to set {channel.mention} as the application channel? Click the button to confirm.",
        color=discord.Color.orange()
    )

    await ctx.respond(embed=embed, view=view, ephemeral=True)





"""
  ____                       _        _                      _             __  __                                           
 / ___|    ___   _ __     __| |      / \     _ __    _ __   | |  _   _    |  \/  |   ___   ___   ___    __ _    __ _    ___ 
 \___ \   / _ \ | '_ \   / _` |     / _ \   | '_ \  | '_ \  | | | | | |   | |\/| |  / _ \ / __| / __|  / _` |  / _` |  / _ \
  ___) | |  __/ | | | | | (_| |    / ___ \  | |_) | | |_) | | | | |_| |   | |  | | |  __/ \__ \ \__ \ | (_| | | (_| | |  __/
 |____/   \___| |_| |_|  \__,_|   /_/   \_\ | .__/  | .__/  |_|  \__, |   |_|  |_|  \___| |___/ |___/  \__,_|  \__, |  \___|
                                            |_|     |_|          |___/                                         |___/
""" 

async def send_apply_message(channel: discord.TextChannel):
    button = discord.ui.Button(label="Apply Now 🚀", style=discord.ButtonStyle.success)

    async def button_callback(interaction: discord.Interaction):
        await start_application_process(interaction)

    button.callback = button_callback
    view = discord.ui.View()
    view.add_item(button)

    embed = discord.Embed(
        title="📩 Start Your Application!",
        description="Click the **Apply Now** button below to begin your application process.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Powered by Your Friendly Bot")
    message = await channel.send(embed=embed, view=view)

    application_management.upsert(
        {
            "server_id": channel.guild.id,
            "apply_message": message.id
        },
        on_conflict=["server_id"]
    ).execute()





"""
  ____    _                    _          _                      _   _                  _     _                     ____                                           
 / ___|  | |_    __ _   _ __  | |_       / \     _ __    _ __   | | (_)   ___    __ _  | |_  (_)   ___    _ __     |  _ \   _ __    ___     ___    ___   ___   ___ 
 \___ \  | __|  / _` | | '__| | __|     / _ \   | '_ \  | '_ \  | | | |  / __|  / _` | | __| | |  / _ \  | '_ \    | |_) | | '__|  / _ \   / __|  / _ \ / __| / __|
  ___) | | |_  | (_| | | |    | |_     / ___ \  | |_) | | |_) | | | | | | (__  | (_| | | |_  | | | (_) | | | | |   |  __/  | |    | (_) | | (__  |  __/ \__ \ \__ \
 |____/   \__|  \__,_| |_|     \__|   /_/   \_\ | .__/  | .__/  |_| |_|  \___|  \__,_|  \__| |_|  \___/  |_| |_|   |_|     |_|     \___/   \___|  \___| |___/ |___/
                                                |_|     |_|
""" 

async def start_application_process(interaction: discord.Interaction):
    modal = discord.ui.Modal(
        title="Application Form",
        custom_id="nation_id_modal",
    )

    nation_id_input = discord.ui.InputText(
        label="Nation ID",
        placeholder="Enter your unique Nation ID here",
        style=discord.InputTextStyle.short,
        required=True,
    )
    modal.add_item(nation_id_input)

    async def modal_callback(modal_interaction: discord.Interaction):
        nation_id = nation_id_input.value
        server_data = application_management.select("*").eq("server_id", interaction.guild.id).execute()
        if not server_data.data:
            embed = discord.Embed(
                title="⚠️ Server Data Not Found!",
                description="Please ask an admin to set up the application channel first.",
                color=discord.Color.red()
            )
            await modal_interaction.response.send_message(embed=embed, ephemeral=True)
            return

        system = server_data.data[0]["system"]
        category_name = server_data.data[0].get("category_name")
        if not category_name:
            embed = discord.Embed(
                title="⚠️ Application Category Not Set!",
                description="Please ask an admin to set up an application category using `/set_category`.",
                color=discord.Color.red()
            )
            await modal_interaction.response.send_message(embed=embed, ephemeral=True)
            return

        category = discord.utils.get(interaction.guild.categories, name=category_name)
        if not category:
            embed = discord.Embed(
                title="⚠️ Category Error",
                description="Could not find the application category. Please contact an admin.",
                color=discord.Color.red()
            )
            await modal_interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if system == "DNS":
            r = httpx.get(f'https://diplomacyandstrifeapi.com/api/nation?APICode={DNS_API}&NationId={nation_id}')
            if r.status_code != 200:
                await modal_interaction.response.send_message("Failed to fetch nation data.", ephemeral=True)
                return

            nation_data = r.json()
            if isinstance(nation_data, list):
                nation_data = nation_data[0] if nation_data else {}
            
            nation_name = nation_data['NationName']
            new_channel = await interaction.guild.create_text_channel(
                name=f"app-{nation_id}-{nation_name}",
                category=category
            )            
        
            interviewer_channel_id = application_management.select("*").eq("server_id", new_channel.guild.id).execute().data[0].get("interviewer_channel_id")
            if not interviewer_channel_id:
                embed = discord.Embed(
                    title="⚠️ Interviewer Channel Not Found",
                    description="Please ask an admin to set the interviewer channel using `/set_interviewer_channel`.",
                    color=discord.Color.red()
                )
                await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                return

            interviewer_channel = interaction.guild.get_channel(interviewer_channel_id)
            if not interviewer_channel:
                embed = discord.Embed(
                    title="⚠️ Interviewer Channel Error",
                    description="Could not find the interviewer channel. Please contact an admin.",
                    color=discord.Color.red()
                )
                await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                return

            message = await interviewer_channel.send(
                f"Discussion for {nation_name}'s application."
            )

            thread_name = f"app-{nation_id}-{nation_name}".lower()
            await message.create_thread(
                name=thread_name,
            )

            leader_name = nation_data["LeaderName"]
            if leader_name == "0":
                leader_name = "None"
            
            population = nation_data["Pop"]
            alliance_name = nation_data["Alliance"]

            embed = discord.Embed(
                title=f"Nation Information: {nation_name}",
                description=f"Details for {modal_interaction.user.mention}'s nation:",  # Mentions the user who applied
                color=discord.Color.gold()
            )
            
            embed.add_field(name="Nation ID", value=nation_id, inline=True)
            embed.add_field(name="Nation Name", value=nation_name, inline=True)
            embed.add_field(name="Leader Name", value=leader_name, inline=True)
            embed.add_field(name="Population", value="{:,}".format(population), inline=True)
            embed.add_field(name="Alliance Name", value=alliance_name, inline=True)
            embed.set_footer(text="Powered by Diplomacy and Strife API")

            message = await new_channel.send(embed=embed)
            await message.pin()

        elif system == "PNW":
            new_channel = await interaction.guild.create_text_channel(
                name=f"application-{nation_id}-hello-world",
                category=category
            )
            embed = discord.Embed(
                title="Hello World",
                description="This is a simple 'Hello World' message for PNW servers.",
                color=discord.Color.green()
            )
            message = await new_channel.send(embed=embed)
            await message.pin()

        interview_channels = application_management.select("*").eq("server_id", new_channel.guild.id).execute().data
        if len(interview_channels) > 0:
            interview_channels = interview_channels[0]["interview_channels"]
            interview_channels.append(new_channel.id)
        else:
            interview_channels = [new_channel.id]

        application_management.upsert(
            {
                "server_id": new_channel.guild.id,
                "interview_channels": interview_channels
            },
            on_conflict=["server_id"]
        ).execute()

        embed = discord.Embed(
            title="✅ Application Submitted",
            description=f"Your application channel has been created: {new_channel.mention}",
            color=discord.Color.green()
        )
        await modal_interaction.response.send_message(embed=embed, ephemeral=True)

    modal.callback = modal_callback
    await interaction.response.send_modal(modal)





"""
  ____           _       ___           _                           _                                      ____   _                                      _ 
 / ___|    ___  | |_    |_ _|  _ __   | |_    ___   _ __  __   __ (_)   ___  __      __   ___   _ __     / ___| | |__     __ _   _ __    _ __     ___  | |
 \___ \   / _ \ | __|    | |  | '_ \  | __|  / _ \ | '__| \ \ / / | |  / _ \ \ \ /\ / /  / _ \ | '__|   | |     | '_ \   / _` | | '_ \  | '_ \   / _ \ | |
  ___) | |  __/ | |_     | |  | | | | | |_  |  __/ | |     \ V /  | | |  __/  \ V  V /  |  __/ | |      | |___  | | | | | (_| | | | | | | | | | |  __/ | |
 |____/   \___|  \__|   |___| |_| |_|  \__|  \___| |_|      \_/   |_|  \___|   \_/\_/    \___| |_|       \____| |_| |_|  \__,_| |_| |_| |_| |_|  \___| |_|
""" 

@bot.slash_command(name="set_interviewer_channel", description="Set the channel where the Interviewers will discuss.")
async def set_apply_channel(ctx: discord.ApplicationContext, channel: discord.TextChannel):
    button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)

    async def button_callback(interaction: discord.Interaction):
        if interaction.user != ctx.user:
            await interaction.response.send_message("You are not allowed to confirm this action.", ephemeral=True)
            return

        application_management.upsert(
            {
                "server_id": ctx.guild.id,
                "interviewer_channel_id": channel.id,
            },
            on_conflict=["server_id"]
        ).execute()

        apply_channel_cache[ctx.guild.id] = channel.id

        embed = discord.Embed(
            title="✅ Interviewer Channel Set",
            description=f"The Interviewer channel has been set to {channel.mention}.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    button.callback = button_callback
    view = discord.ui.View()
    view.add_item(button)

    embed = discord.Embed(
        title="⚠️ Confirm Interviewer Channel",
        description=f"Are you sure you want to set {channel.mention} as the Interviewer channel? Click the button to confirm.",
        color=discord.Color.orange()
    )

    await ctx.respond(embed=embed, view=view, ephemeral=True)





"""
  ____           _          _                      _   _                  _     _                      ____           _                                         
 / ___|    ___  | |_       / \     _ __    _ __   | | (_)   ___    __ _  | |_  (_)   ___    _ __      / ___|   __ _  | |_    ___    __ _    ___    _ __   _   _ 
 \___ \   / _ \ | __|     / _ \   | '_ \  | '_ \  | | | |  / __|  / _` | | __| | |  / _ \  | '_ \    | |      / _` | | __|  / _ \  / _` |  / _ \  | '__| | | | |
  ___) | |  __/ | |_     / ___ \  | |_) | | |_) | | | | | | (__  | (_| | | |_  | | | (_) | | | | |   | |___  | (_| | | |_  |  __/ | (_| | | (_) | | |    | |_| |
 |____/   \___|  \__|   /_/   \_\ | .__/  | .__/  |_| |_|  \___|  \__,_|  \__| |_|  \___/  |_| |_|    \____|  \__,_|  \__|  \___|  \__, |  \___/  |_|     \__, |
                                  |_|     |_|                                                                                      |___/                  |___/
""" 

@bot.slash_command(name="set_application_category", description="Set the category for application channels.")
async def set_category(ctx: discord.ApplicationContext, category_name: str):
    button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)

    async def button_callback(interaction: discord.Interaction):
        if interaction.user != ctx.user:
            await interaction.response.send_message("You are not allowed to confirm this action.", ephemeral=True)
            return
        
        category = discord.utils.get(ctx.guild.categories, name=category_name)
        if not category:
            embed = discord.Embed(
                title="⚠️ Category Not Found",
                description=f"Category '{category_name}' does not exist. Please create it first.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        application_management.upsert(
            {
                "server_id": ctx.guild.id,
                "category_name": category_name
            },
            on_conflict=["server_id"]
        ).execute()

        embed = discord.Embed(
            title="✅ Application Category Set",
            description=f"The application category has been set to '{category_name}'.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    button.callback = button_callback
    view = discord.ui.View()
    view.add_item(button)

    embed = discord.Embed(
        title="⚠️ Confirm Application Category",
        description=f"Are you sure you want to set the application category to '{category_name}'? Click the button to confirm.",
        color=discord.Color.orange()
    )

    await ctx.respond(embed=embed, view=view, ephemeral=True)





"""
  ____                 _                                _      ____            _             __  __                                           
 |  _ \    ___   ___  | |_    ___    _ __    ___       / \    |  _ \   _ __   | |  _   _    |  \/  |   ___   ___   ___    __ _    __ _    ___ 
 | |_) |  / _ \ / __| | __|  / _ \  | '__|  / _ \     / _ \   | |_) | | '_ \  | | | | | |   | |\/| |  / _ \ / __| / __|  / _` |  / _` |  / _ \
 |  _ <  |  __/ \__ \ | |_  | (_) | | |    |  __/    / ___ \  |  __/  | |_) | | | | |_| |   | |  | | |  __/ \__ \ \__ \ | (_| | | (_| | |  __/
 |_| \_\  \___| |___/  \__|  \___/  |_|     \___|   /_/   \_\ |_|     | .__/  |_|  \__, |   |_|  |_|  \___| |___/ |___/  \__,_|  \__, |  \___|
                                                                      |_|          |___/                                         |___/
""" 

async def restore_apply_message(guild):
    server_data = application_management.select("*").eq("server_id", guild.id).execute()
    if server_data.data:
        apply_message_id = server_data.data[0].get("apply_message")
        if apply_message_id:
            channel_id = server_data.data[0].get("apply_channel_id")
            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel:
                    try:
                        message = await channel.fetch_message(apply_message_id)
                        button = discord.ui.Button(label="Apply Now 🚀", style=discord.ButtonStyle.success)

                        async def button_callback(interaction: discord.Interaction):
                            await start_application_process(interaction)

                        button.callback = button_callback
                        view = discord.ui.View()
                        view.add_item(button)

                        await message.edit(embed=message.embeds[0], view=view)
                    except discord.NotFound:
                        pass




@bot.event
async def on_ready():
    for guild in bot.guilds:
        await restore_apply_message(guild)
        

bot.run(DISCORD_TOKEN)
