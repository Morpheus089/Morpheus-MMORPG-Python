#-----Initialisation--------------------------------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)

token = os.getenv('DISCORD_TOKEN')


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def sync_commands():

    await bot.tree.sync()
    print("Commandes en slash synchronisées avec succès.")

#--------------------------------------------------------------------------------------------------------

#-----Démarrage--------------------------------------------------------------------------------------------------------

async def load_extensions():
    try:
        await bot.load_extension("module.economie")
        print("Extension 'economie' chargée avec succès.")
        await bot.load_extension("module.craft")
        print("Extension 'craft' chargée avec succès.")
        await bot.load_extension("module.stats")
        print("Extension 'stats' chargée avec succès.")
        await bot.load_extension("module.attaque")
        print("Extension 'attaque' chargée avec succès.")
        await bot.load_extension("module_moderation.perssonalisation")
        print("Extension 'Perssonalisation' chargée avec succès.")
        await bot.load_extension("module_moderation.ticket")
        print("Extension 'Ticket' chargée avec succès.")
        await bot.load_extension("module.xp")
        print("Extension 'Niveau' chargée avec succès.")
        await bot.load_extension("module.creature")
        print("Extension 'Creature' chargée avec succès.")
    except Exception as e:
        print(f"Erreur lors du chargement des extensions : {e}")

#--------------------------------------------------------------------------------------------------------

MODULE_FOLDER = os.path.join(os.path.dirname(__file__), "module")
DATA_FOLDER = os.path.join(MODULE_FOLDER, "data")
XP_FILE = os.path.join(DATA_FOLDER, "xp.json")
STATS_FILE = os.path.join(DATA_FOLDER, "stats.json")

DEFAULT_STATS = {}
DEFAULT_XP = {}

def load_data(file_name, default_data):
    if not os.path.exists(file_name):
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(default_data, file, indent=4)
    with open(file_name, "r", encoding="utf-8") as file:
        return json.load(file)

def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

xp_data = load_data(XP_FILE, DEFAULT_XP)
stats_data = load_data(STATS_FILE, DEFAULT_STATS)

def ajouter_xp(user_id, montant):
    global xp_data, stats_data

    if user_id not in xp_data:
        xp_data[user_id] = {"xp": 0, "niveau": 1}

    if user_id not in stats_data:
        stats_data[user_id] = {
            "force": 0,
            "agilite": 0,
            "vitesse": 0,
            "intelligence": 0,
            "dexterite": 0,
            "vitalite": 0,
            "charisme": 0,
            "chance": 0,
            "points_a_distribuer": 0,
        }

    xp_data[user_id]["xp"] += montant
    logging.info(f"Ajouté {montant} XP à l'utilisateur {user_id}. Total XP: {xp_data[user_id]['xp']}")

    niveau_actuel = xp_data[user_id]["niveau"]
    while xp_data[user_id]["xp"] >= xp_pour_niveau(niveau_actuel):
        xp_data[user_id]["xp"] -= xp_pour_niveau(niveau_actuel)
        xp_data[user_id]["niveau"] += 1
        niveau_actuel = xp_data[user_id]["niveau"]
        stats_data[user_id]["points_a_distribuer"] += 5
        logging.info(f"L'utilisateur {user_id} est monté au niveau {niveau_actuel}. Points à distribuer: {stats_data[user_id]['points_a_distribuer']}")

    save_data(XP_FILE, xp_data)
    save_data(STATS_FILE, stats_data)
    logging.info(f"Données sauvegardées pour l'utilisateur {user_id}.")

def xp_pour_niveau(niveau):
    return niveau * 2000 

@bot.event
async def on_message(message):
    global xp_data

    if message.author.bot:
        return

    if not hasattr(bot, "last_messages"):
        bot.last_messages = {}

    user_id = str(message.author.id)

    if user_id in bot.last_messages and bot.last_messages[user_id] == message.content:
        return

    bot.last_messages[user_id] = message.content

    caracteres = len(message.content)
    ajouter_xp(user_id, caracteres)

    await bot.process_commands(message)

role_membre_id = 1330242611386257440  
role_non_verifie_id = 1330242628389961841  
welcome_channel_id = 1330242639521648805  

@bot.event
async def on_member_join(member: discord.Member):
    try:
        welcome_channel = member.guild.get_channel(welcome_channel_id)
        if not welcome_channel:
            print("Salon de bienvenue introuvable.")
            return

        role_non_verifie = member.guild.get_role(role_non_verifie_id)
        role_membre = member.guild.get_role(role_membre_id)

        if not role_non_verifie or not role_membre:
            print("Les rôles Non Vérifié ou Membre sont manquants.")
            return

        await member.add_roles(role_non_verifie)

        embed = discord.Embed(
            title="🔒 Vérification de sécurité",
            description=f"Bienvenue sur **{member.guild.name}** !\n\nCliquez sur le bouton ci-dessous pour prouver que vous êtes humain.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Vous devez compléter cette étape pour accéder au serveur.")

        class CaptchaView(discord.ui.View):
            def __init__(self, member):
                super().__init__(timeout=300) 
                self.member = member

            @discord.ui.button(label="Je ne suis pas un robot", style=discord.ButtonStyle.green)
            async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != self.member:
                    await interaction.response.send_message("Ce bouton ne vous appartient pas !", ephemeral=True)
                    return

                await self.member.remove_roles(role_non_verifie)
                await self.member.add_roles(role_membre)

                await interaction.response.send_message("✅ Vérification réussie ! Vous avez maintenant accès au serveur.", ephemeral=True)

                self.stop()

        view = CaptchaView(member)
        await member.send(embed=embed, view=view)

        welcome_image_url = "https://zupimages.net/up/25/03/bl3d.jpg"
        embed_welcome = discord.Embed(
            title="🎉 Bienvenue parmi nous !",
            description=(
                f"Salut {member.mention} ! Bienvenue sur **{member.guild.name}** 🌟.\n\n"
                "Voici quelques étapes pour bien commencer :\n"
                "1️⃣ Consulte les 📜 **règlement** pour savoir ce qui est attendu.\n"
                "2️⃣ Visite le canal 🔧 **Rôle react** pour personnaliser ton expérience.\n"
                "3️⃣ Passe dire bonjour dans le salon général, on ne mord pas ! 😄\n\n"
                "**Amuse-toi bien sur le serveur et n'hésite pas à demander de l'aide si nécessaire.**"
            ),
            color=discord.Color.purple()
        )
        embed_welcome.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed_welcome.set_image(url=welcome_image_url)
        embed_welcome.set_footer(text=f"Nous sommes maintenant {len(member.guild.members)} membres 🎉 !", icon_url=member.guild.icon.url if member.guild.icon else None)
        embed_welcome.add_field(name="🛠️ Ressources", value="Besoin d'aide? Consulte notre salon question ou contacte un modérateur.", inline=False)
        embed_welcome.add_field(name="📣 Rappels", value="Reste respectueux et amuse-toi bien!", inline=False)

        await welcome_channel.send(embed=embed_welcome)

    except discord.Forbidden:
        print(f"Impossible d'envoyer un message de vérification à {member}.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

#--------------------------------------------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté et prêt !")
    await load_extensions()
    await sync_commands()

bot.run(token)

#--------------------------------------------------------------------------------------------------------