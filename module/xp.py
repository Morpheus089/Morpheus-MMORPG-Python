#-----Initialisation--------------------------------------------------------------------------------------------------------

import discord
from discord.ext import commands
import json
import os
from discord import app_commands


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--------------------------------------------------------------------------------------------------------

#-----Lancement-JSON--------------------------------------------------------------------------------------------------------

class Xp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
        self.DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
        self.STATS_FILE = os.path.join(self.DATA_FOLDER, "stats.json")
        self.XP_FILE = os.path.join(self.DATA_FOLDER, "xp.json")

       
        self.DEFAULT_STATS = {}
        self.DEFAULT_XP = {}

        
        self.stats_data = self.load_data(self.STATS_FILE, self.DEFAULT_STATS)
        self.xp_data = self.load_data(self.XP_FILE, self.DEFAULT_XP)

        self.unlocked_attacks = self.load_data(os.path.join(self.DATA_FOLDER, "unlocked_attacks.json"), {})

        for user_id in self.xp_data:
            user_id_str = str(user_id)
            self.verifier_deblocage_attaques(user_id_str)

    def load_data(self, file_name, default_data):
       
        if not os.path.exists(file_name):
            
            os.makedirs(os.path.dirname(file_name), exist_ok=True)  
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump(default_data, file, indent=4)
        
        
        with open(file_name, "r", encoding="utf-8") as file:
            return json.load(file)

    def save_data(self, file_name, data):
        
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def save_unlocked_attacks(self):
        self.save_data(os.path.join(self.DATA_FOLDER, "unlocked_attacks.json"), self.unlocked_attacks)

    def verifier_deblocage_attaques(self, user_id):
        if user_id not in self.xp_data:
            return

        niveau_joueur = self.xp_data[user_id]["niveau"]
        if user_id not in self.unlocked_attacks:
            self.unlocked_attacks[user_id] = []

        attaque_cog = self.bot.get_cog("Attaque")
        if attaque_cog is None:
            print("Le cog Attaque n'a pas été trouvé!")
            return

        for nom_attaque, details_attaque in attaque_cog.attaque_data.items():
            niveau_requis = details_attaque["niveau_requis"]
            if niveau_joueur >= niveau_requis and nom_attaque not in self.unlocked_attacks[user_id]:
                self.unlocked_attacks[user_id].append(nom_attaque)
                print(f"Attaque {nom_attaque} débloquée pour {user_id}!")

        self.save_unlocked_attacks()

    @app_commands.command(name="voir_attaques_debloquees", description="Affiche les attaques débloquées.")
    async def voir_attaques_debloquees_cmd(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        self.verifier_deblocage_attaques(user_id)
        if user_id not in self.unlocked_attacks or not self.unlocked_attacks[user_id]:
            await interaction.response.send_message("Vous n'avez débloqué aucune attaque pour le moment.")
            return

        self.verifier_deblocage_attaques(user_id)

        embed = discord.Embed(title="Attaques débloquées", color=discord.Color.green())
        for attaque in self.unlocked_attacks[user_id]:
            embed.add_field(name=attaque, value="Attaque débloquée!", inline=False)
        await interaction.response.send_message(embed=embed)

    def xp_pour_niveau(self, niveau):
        return niveau * 2000 

    #-----Niveau--------------------------------------------------------------------------------------------------------

    # Commande pour afficher le niveau actuel d'un utilisateur
    @app_commands.command(name="niveau", description="Affiche votre niveau actuel et vos points d'expérience.")
    async def niveau(self, interaction: discord.Interaction):
    
        user_id = str(interaction.user.id)

        
        self.xp_data = self.load_data(self.XP_FILE, self.DEFAULT_XP)
        self.stats_data = self.load_data(self.STATS_FILE, self.DEFAULT_STATS)

        if user_id not in self.xp_data:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Erreur ❌",
                    description="Vous n'avez pas encore de niveau.",
                    color=discord.Color.red()
                )
            )
            return

        
        niveau_actuel = self.xp_data[user_id]["niveau"]
        xp_actuel = self.xp_data[user_id]["xp"]
        xp_pour_prochain_niveau = self.xp_pour_niveau(niveau_actuel)

        
        embed = discord.Embed(
            title=f"Informations sur votre niveau",
            description=(f"**Niveau actuel :** {niveau_actuel}\n"
                         f"**XP actuel :** {xp_actuel}\n"
                         f"**XP nécessaire pour le prochain niveau :** {xp_pour_prochain_niveau - xp_actuel} XP"),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="ajouter_niveau", description="Ajoute des niveaux à un utilisateur (administrateurs uniquement).")
    @app_commands.checks.has_permissions(administrator=True)
    async def ajouter_niveau(self, interaction: discord.Interaction, membre: discord.Member, niveaux: int):
       
        user_id = str(membre.id)

        
        if user_id not in self.xp_data:
            self.xp_data[user_id] = {"niveau": 1, "xp": 0}

        
        self.xp_data[user_id]["niveau"] += niveaux
        xp_pour_prochain_niveau = self.xp_pour_niveau(self.xp_data[user_id]["niveau"])

       
        self.save_data(self.XP_FILE, self.xp_data)

        
        embed = discord.Embed(
            title=f"Niveaux ajoutés avec succès ⭐",
            description=(
                f"{niveaux} niveaux ont été ajoutés à {membre.mention}.\n"
                f"**Nouveau niveau :** {self.xp_data[user_id]['niveau']}\n"
                f"**XP nécessaire pour le prochain niveau :** {xp_pour_prochain_niveau} XP"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=membre.avatar.url if membre.avatar else None)
        embed.set_footer(
            text="Commande réservée aux administrateurs",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )

        
        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="retirer_niveau", description="Retire des niveaux à un utilisateur (administrateurs uniquement).")
    @app_commands.checks.has_permissions(administrator=True)
    async def retirer_niveau(self, interaction: discord.Interaction, membre: discord.Member, niveaux: int):
       
        user_id = str(membre.id)

        
        if user_id not in self.xp_data:
            embed = discord.Embed(
                title="Erreur ❌",
                description=f"L'utilisateur {membre.mention} n'a pas encore de niveau.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        current_level = self.xp_data[user_id]["niveau"]
        new_level = max(current_level - niveaux, 1)
        self.xp_data[user_id]["niveau"] = new_level

        
        self.save_data(self.XP_FILE, self.xp_data)

        
        embed = discord.Embed(
            title=f"Niveaux retirés avec succès 🔻",
            description=(
                f"{niveaux} niveaux ont été retirés à {membre.mention}.\n"
                f"**Nouveau niveau :** {new_level}"
            ),
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=membre.avatar.url if membre.avatar else None)
        embed.set_footer(
            text="Commande réservée aux administrateurs",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )

        
        await interaction.response.send_message(embed=embed)

#--------------------------------------------------------------------------------------------------------


async def setup(bot):
    await bot.add_cog(Xp(bot)) 