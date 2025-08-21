#-----Initialisation--------------------------------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord import app_commands
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--------------------------------------------------------------------------------------------------------

#-----Lancement-JSON--------------------------------------------------------------------------------------------------------

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
        self.DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
        self.STATS_FILE = os.path.join(self.DATA_FOLDER, "stats.json")
        self.EQUIPEMENT_FILE = os.path.join(self.DATA_FOLDER, "equipement.json")

        
        self.DEFAULT_STATS = {}
        self.DEFAULT_EQUIPEMENT = {}

        
        self.stats_data = self.load_data(self.STATS_FILE, self.DEFAULT_STATS)
        self.equipement_data = self.load_data(self.EQUIPEMENT_FILE, self.DEFAULT_EQUIPEMENT)

    def load_data(self, file_name, default_data):
        """Charge les données depuis un fichier JSON ou crée le fichier avec les données par défaut si nécessaire."""
        if not os.path.exists(file_name):
            os.makedirs(os.path.dirname(file_name), exist_ok=True)  
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump(default_data, file, indent=4)
        
        with open(file_name, "r", encoding="utf-8") as file:
            return json.load(file)

    def save_data(self, file_name, data):
        
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def get_stats(self, user_id):
        
        
        base_stats = {
            "force": 0,
            "agilite": 0,
            "vitesse": 0,
            "intelligence": 0,
            "dexterite": 0,
            "vitalite": 0,
            "charisme": 0,
            "chance": 0
        }

       
        if user_id in self.equipement_data:
            for item in self.equipement_data[user_id].values():
                if item and "bonus" in item:
                    for stat, value in item["bonus"].items():
                        base_stats[stat] = base_stats.get(stat, 0) + value

       
        if user_id in self.stats_data:
            for stat, value in self.stats_data[user_id].items():
                if stat == "points_a_distribuer":
                    continue  
                base_stats[stat] += value

        return base_stats
        
#--------------------------------------------------------------------------------------------------------

#-----Stats--------------------------------------------------------------------------------------------------------

   
    @app_commands.command(name="distribuer_points", description="Attribuez des points à une statistique spécifique.")
    async def distribuer_points(self, interaction: discord.Interaction, stat: str, points: int):
        user_id = str(interaction.user.id)

        
        valid_stats = ["force", "agilite", "vitesse", "intelligence", "dexterite", "vitalite", "charisme", "chance"]
        if stat not in valid_stats:
            embed = discord.Embed(
                title="⚠️ Statistique invalide",
                description=f"Utilisez l'une des statistiques suivantes : {', '.join(valid_stats)}.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        
        if user_id not in self.stats_data:
            self.stats_data[user_id] = {
                "force": 0,
                "agilite": 0,
                "vitesse": 0,
                "intelligence": 0,
                "dexterite": 0,
                "vitalite": 0,
                "charisme": 0,
                "chance": 0,
                "points_a_distribuer": 0
            }

        
        points_a_distribuer = self.stats_data[user_id].get("points_a_distribuer", 0)
        if points_a_distribuer < points:
            embed = discord.Embed(
                title="🚫 Pas assez de points",
                description=f"Vous avez {points_a_distribuer} points disponibles, mais vous essayez d'en attribuer {points}.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

      
        self.stats_data[user_id][stat] += points
        self.stats_data[user_id]["points_a_distribuer"] -= points 
        self.save_data(self.STATS_FILE, self.stats_data)  

       
        embed = discord.Embed(
            title="✅ Points attribués",
            description=f"Vous avez ajouté **{points}** points à la statistique **{stat}**.\n"
                        f"Il vous reste **{self.stats_data[user_id]['points_a_distribuer']}** points à distribuer.",
            color=0x00FF00
        )
        embed.set_footer(text="Système de distribution de points")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="stats", description="Affiche vos statistiques actuelles.")
    async def afficher_stats(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        
        if user_id not in self.stats_data:
            self.stats_data[user_id] = {
                "force": 0,
                "agilite": 0,
                "vitesse": 0,
                "intelligence": 0,
                "dexterite": 0,
                "vitalite": 0,
                "charisme": 0,
                "chance": 0,
                "points_a_distribuer": 0
            }
            self.save_data(self.STATS_FILE, self.stats_data)

       
        stats = self.get_stats(user_id)

        
        embed = discord.Embed(
            title="📊 Vos statistiques",
            color=0x00FF00,
            description="Voici vos statistiques actuelles :"
        )

        emoji_map = {
            "force": "💪",
            "agilite": "🏃",
            "vitesse": "⚡",
            "intelligence": "🧠",
            "dexterite": "🤹",
            "vitalite": "❤️",
            "charisme": "🗣️",
            "chance": "🍀"
        }

        for stat, value in stats.items():
            if stat != "points_a_distribuer":
                embed.add_field(
                    name=f"{emoji_map.get(stat, '')} {stat.capitalize()}",
                    value=value,
                    inline=True
                )

        points_a_distribuer = self.stats_data[user_id]["points_a_distribuer"]
        embed.add_field(
            name="📈 Points à distribuer",
            value=points_a_distribuer,
            inline=False
        )

        embed.set_footer(text="Système de gestion des statistiques")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="reset_stats", description="Réinitialise vos statistiques et vous donne les points à redistribuer.")
    async def reset_stats(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

       
        if user_id not in self.stats_data:
            self.stats_data[user_id] = {
                "force": 0,
                "agilite": 0,
                "vitesse": 0,
                "intelligence": 0,
                "dexterite": 0,
                "vitalite": 0,
                "charisme": 0,
                "chance": 0,
                "points_a_distribuer": 0
            }
            self.save_data(self.STATS_FILE, self.stats_data)

        
        total_points = sum(self.stats_data[user_id].values()) - self.stats_data[user_id]["points_a_distribuer"]

        
        for stat in ["force", "agilite", "vitesse", "intelligence", "dexterite", "vitalite", "charisme", "chance"]:
            self.stats_data[user_id][stat] = 0

        
        self.stats_data[user_id]["points_a_distribuer"] += total_points

        
        self.save_data(self.STATS_FILE, self.stats_data)

        
        embed = discord.Embed(
            title="♻️ Réinitialisation des statistiques",
            color=0x00FF00,
            description=f"Vos statistiques ont été réinitialisées avec succès !\n\nVous avez désormais `{total_points}` points à redistribuer."
        )

        embed.set_footer(text="Système de gestion des statistiques")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="ajouter_points", description="Ajoute des points à une statistique spécifique d'un membre.")
    @app_commands.checks.has_permissions(administrator=True)  # Vérifier si l'utilisateur a les permissions administrateur
    async def ajouter_points(self, interaction: discord.Interaction, membre: discord.Member, stat: str, montant: int):
        user_id = str(membre.id)

       
        if user_id not in self.stats_data:
            self.stats_data[user_id] = {
                "force": 0,
                "agilite": 0,
                "vitesse": 0,
                "intelligence": 0,
                "dexterite": 0,
                "vitalite": 0,
                "charisme": 0,
                "chance": 0,
                "points_a_distribuer": 0
            }

        
        valid_stats = list(self.stats_data[user_id].keys())
        if stat not in valid_stats:
            embed = discord.Embed(
                title="❌ Statistique invalide",
                color=0xFF0000,
                description=f"La statistique `{stat}` est invalide.\n\nStatistiques valides : {', '.join(valid_stats)}."
            )
            await interaction.response.send_message(embed=embed)
            return

       
        self.stats_data[user_id][stat] += montant

        
        self.save_data(self.STATS_FILE, self.stats_data)

        
        embed = discord.Embed(
            title="✅ Points ajoutés avec succès",
            color=0x00FF00,
            description=f"{montant} points ont été ajoutés à la statistique `{stat}` de {membre.mention}."
        )
        embed.add_field(name="Nouvelle valeur", value=f"`{self.stats_data[user_id][stat]}`", inline=True)
        embed.set_footer(text="Gestion des statistiques")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="retirer_points", description="Retire des points d'une statistique spécifique d'un membre.")
    @app_commands.checks.has_permissions(administrator=True)  # Vérifier si l'utilisateur a les permissions administrateur
    async def retirer_points(self, interaction: discord.Interaction, membre: discord.Member, stat: str, montant: int):
        user_id = str(membre.id)

        
        if user_id not in self.stats_data:
            self.stats_data[user_id] = {
                "force": 0,
                "agilite": 0,
                "vitesse": 0,
                "intelligence": 0,
                "dexterite": 0,
                "vitalite": 0,
                "charisme": 0,
                "chance": 0,
                "points_a_distribuer": 0
            }

        
        if stat not in self.stats_data[user_id]:
            embed = discord.Embed(
                title="❌ Statistique invalide",
                color=0xFF0000,
                description=f"La statistique `{stat}` est invalide.\n\nStatistiques valides : {', '.join(self.stats_data[user_id].keys())}."
            )
            await interaction.response.send_message(embed=embed)
            return

        
        self.stats_data[user_id][stat] = max(self.stats_data[user_id][stat] - montant, 0)

        
        self.save_data(self.STATS_FILE, self.stats_data)

        
        embed = discord.Embed(
            title="✅ Points retirés avec succès",
            description=f"{montant} points ont été retirés de la statistique `{stat}` de {membre.mention}.",
            color=discord.Color.green()
        )
        embed.add_field(name="Nouvelle valeur", value=str(self.stats_data[user_id][stat]), inline=True)
        embed.set_footer(text="Opération effectuée par " + interaction.user.name)

        
        embed.set_thumbnail(url="https://emoji.url/to/some/emoji.png")

        
        await interaction.response.send_message(embed=embed)

#--------------------------------------------------------------------------------------------------------


async def setup(bot):
    await bot.add_cog(Stats(bot)) 