#-----Initialisation--------------------------------------------------------------------------------------------------------

from random import choices
from types import NoneType

import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os

RIEN=None

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--------------------------------------------------------------------------------------------------------

#-----Lancement-JSON--------------------------------------------------------------------------------------------------------

def load_data(file_path, default_data):
    if not os.path.exists(file_path):
        save_data(file_path, default_data)
        return default_data
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


class Attaque(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.DEFAULT_ATTAQUE = {}


        self.DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
        self.ATTAQUE_FILE = os.path.join(self.DATA_FOLDER,"attaque.json")

        self.attaque_data = self.load_data(self.ATTAQUE_FILE, self.DEFAULT_ATTAQUE)

    def load_data(self, file_name, default_data):
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump(default_data, file, indent=4, ensure_ascii=False)
            print(f"Fichier créé avec les données par défaut : {default_data}") 
            return default_data
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON dans {file_name}: {e}")
            print("Contenu du fichier:")
            with open(file_name, "r", encoding="utf-8") as file:
                print(file.read()) 
            return default_data

    def save_data(self, file_name, data):
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def ajouter_attaque(self,interaction: discord.Interaction , nom, type , stats_scale , niveau_requis, scale_coef, base_damage):

        stats_valides = ["force", "agilite", "vitesse", "intelligence", "dexterite", "vitalite", "charisme", "chance"]
        if stats_scale not in stats_valides:
            return "Stat invalide"
        elif not isinstance(niveau_requis, int) or niveau_requis < 0:
            return "Le niveau requis doit être un entier positif."
        elif not isinstance(scale_coef, float) or scale_coef < 0:
            return "Le niveau de scale doit être un entier positif."
        elif not isinstance(base_damage, int) or base_damage < 1:
            return "Le niveau de damage doit être un entier positif et supérieur à 1."

        self.attaque_data[nom] = {
            "type" : type ,
            "stats_scale" : stats_scale ,
            "niveau_requis" : niveau_requis,
            "coefficient_de_damage" : scale_coef,
            "base damage" : base_damage
        }
        save_data(self.ATTAQUE_FILE, self.attaque_data)
        return None
    
#--------------------------------------------------------------------------------------------------------

#-----attaque-------------------------------------------------------------------------------------------------------

    @app_commands.command(name="ajouter_attaque", description="Ajoute une nouvelle attaque.")
    async def ajouter_attaque_cmd(self, interaction: discord.Interaction, nom: str, type: str, stats_scale: str,
                                  niveau_requis: int,scale_coef:float,base_damage:int):
        resultat = self.ajouter_attaque(self,nom, type, stats_scale, niveau_requis,scale_coef,base_damage)

        if resultat:
            embed = discord.Embed(
                title=resultat,
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Attaque '{nom}' ajoutée et sauvegardée avec succès!")


    @app_commands.command(name="voir_attaques", description="Affiche la liste des attaques.")
    async def voir_attaques_cmd(self, interaction: discord.Interaction):
        if not self.attaque_data:
            await interaction.response.send_message("Aucune attaque enregistrée.")
            return

        embed = discord.Embed(title="Liste des Attaques", color=discord.Color.blue())

        for nom, details in self.attaque_data.items():
            embed.add_field(
                name=nom,
                value=f"Type: {details['type']}\nStat de scale: {details['stats_scale']}\nniveau requis: {details['niveau_requis']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="supprimer_attaque", description="Supprime une attaque.")
    async def supprimer_attaque_cmd(self, interaction: discord.Interaction, nom: str):
        if nom not in self.attaque_data:
            await interaction.response.send_message(f"L'attaque '{nom}' n'existe pas.", ephemeral=True)
            return

        del self.attaque_data[nom]
        self.save_data(self.ATTAQUE_FILE, self.attaque_data)

        xp_cog = self.bot.get_cog("Xp")
        if xp_cog:
            for user_id in list(xp_cog.unlocked_attacks.keys()):
                if nom in xp_cog.unlocked_attacks[user_id]:
                    xp_cog.unlocked_attacks[user_id].remove(nom)
                    print(f"L'attaque '{nom}' a été supprimée des attaques débloquées de {user_id}")

            xp_cog.save_unlocked_attacks()
        else:
            print("Cog Xp non trouvé, impossible de mettre à jour les attaques débloquées.")

        await interaction.response.send_message(f"L'attaque '{nom}' a été supprimée avec succès !")

#--------------------------------------------------------------------------------------------------------

async def setup(bot):
    await bot.add_cog(Attaque(bot))