#-----Initialisation--------------------------------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--------------------------------------------------------------------------------------------------------

#-----Lancement-JSON--------------------------------------------------------------------------------------------------------

class Craft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Définition des chemins vers les fichiers JSON
        self.DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
        self.INVENTAIRE_FILE = os.path.join(self.DATA_FOLDER, "inventaire.json")
        self.RESSOURCES_FILE = os.path.join(self.DATA_FOLDER, "ressources.json")
        self.RECETTES_FILE = os.path.join(self.DATA_FOLDER, "recettes.json")

        # Données par défaut
        self.DEFAULT_INVENTAIRE = {}
        self.DEFAULT_RESSOURCES = {"liste_ressources": []}  
        self.DEFAULT_RECETTES = {}

        # Chargement des données
        self.inventaire_data = self.load_data(self.INVENTAIRE_FILE, self.DEFAULT_INVENTAIRE)
        self.ressources_data = self.load_data(self.RESSOURCES_FILE, self.DEFAULT_RESSOURCES)
        self.recettes_data = self.load_data(self.RECETTES_FILE, self.DEFAULT_RECETTES)
    
    def load_data(self, file_name, default_data):
        """Charge les données depuis un fichier JSON ou crée le fichier avec les données par défaut si nécessaire."""
        if not os.path.exists(file_name):
            
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump(default_data, file, indent=4)
        
        with open(file_name, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        
        for key, value in default_data.items():
            if key not in data:
                data[key] = value

        return data

    def save_data(self, file_name, data):
        """Sauvegarde les données dans un fichier JSON."""
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

#--------------------------------------------------------------------------------------------------------

#-----Craft--------------------------------------------------------------------------------------------------------

    @app_commands.command(name="ajouter_recette", description="Ajoute une nouvelle recette.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ajouter_recette(self, interaction: discord.Interaction, nom_recette: str, ressources: str,
                              equipable: bool, slot: str = None, prix: int = 0, bonus: str = None):
        try:
            ressources_dict = {}
            for r in ressources.split(","):
                try:
                    k, v = r.split("=")
                    ressources_dict[k.strip()] = int(v.strip())
                    print(ressources_dict)
                except ValueError:
                    await interaction.response.send_message(
                        "Invalid resource format. Use ' resource=quantity,resource=quantity '.", ephemeral=True)
                    return

            bonus_dict = {}
            if bonus:
                for b in bonus.split(","):
                    try:
                        k, v = b.split("=")
                        bonus_dict[k.strip()] = int(v.strip())
                        print(bonus_dict)
                    except ValueError:
                        await interaction.response.send_message("Invalid bonus format. Use 'stat=value,stat=value'.",
                                                                ephemeral=True)
                        return
        except ValueError:
            await interaction.response.send_message("Invalid price. Please enter a number.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

        recette = {
            "nom": nom_recette,
            "ressources": ressources_dict,
            "equipable": equipable,
            "slot": slot if equipable else None,
            "prix": prix,
            "bonus": bonus_dict
        }

        self.recettes_data[nom_recette] = recette
        self.save_data(self.RECETTES_FILE, self.recettes_data)

        embed = discord.Embed(
            title="✅ Recette ajoutée avec succès !",
            description=f"La recette **{nom_recette}** a été ajoutée.",
            color=discord.Color.green()
        )
        embed.add_field(name="Ressources nécessaires",
                        value="\n".join([f"• {k}: {v}" for k, v in ressources_dict.items()]), inline=False)
        embed.add_field(name="Équipable", value="Oui ✅" if equipable else "Non ❌", inline=True)
        if equipable and slot:
            embed.add_field(name="Slot d'équipement", value=f"{slot.capitalize()}", inline=True)
        embed.add_field(name="Prix", value=f"{prix} 💰", inline=True)
        if bonus_dict:
            embed.add_field(name="Bonus", value="\n".join([f"• {k.capitalize()}: {v}" for k, v in bonus_dict.items()]),
                            inline=False)
        embed.set_footer(text="Commande exécutée par " + interaction.user.name, icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="crafter", description="Craft un objet à partir d'une recette.")
    async def crafter(self, interaction: discord.Interaction, nom_recette: str):
        user_id = str(interaction.user.id)

        
        if nom_recette not in self.recettes_data:
            embed = discord.Embed(
                title="❌ Recette introuvable",
                description=f"La recette **{nom_recette}** n'existe pas. Veuillez vérifier le nom et réessayer !",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        recette = self.recettes_data[nom_recette]
        ressources_requises = recette["ressources"]


        for ressource, quantite in ressources_requises.items():
            for ressource_obj in self.ressources_data["liste_ressources"]:
                if ressource_obj["nom"] == ressource:
                    if "joueurs" not in ressource_obj or user_id not in ressource_obj["joueurs"] or \
                            ressource_obj["joueurs"][user_id]["count"] < quantite:
                        embed = discord.Embed(
                            title="⛔ Ressources insuffisantes",
                            description=(f"{interaction.user.mention}, vous n'avez pas assez de **{ressource}**.\n"
                                         f"Nécessaire : `{quantite}` | Possédé : `{self.ressources_data[user_id].get(ressource, 0)}`"),
                            color=discord.Color.orange()
                        )
                        await interaction.response.send_message(embed=embed)
                        return
                    break

        for ressource, quantite in ressources_requises.items():
            for ressource_obj in self.ressources_data["liste_ressources"]:
                if ressource_obj["nom"] == ressource:
                    ressource_obj["joueurs"][user_id]["count"] -= quantite
                    if ressource_obj["joueurs"][user_id]["count"] <= 0:
                        del ressource_obj["joueurs"][user_id]
                    break

        self.save_data(self.RESSOURCES_FILE, self.ressources_data)

        nouvel_objet = {
            "nom": recette["nom"],
            "prix": recette["prix"],
            "equipable": recette["equipable"],
            "slot": recette.get("slot", None),
            "bonus": recette.get("bonus", {})
        }

        if user_id not in self.inventaire_data:
            self.inventaire_data[user_id] = []

        self.inventaire_data[user_id].append(nouvel_objet)
        self.save_data(self.INVENTAIRE_FILE, self.inventaire_data)

       
        embed = discord.Embed(
            title="✅ Craft réussi !",
            description=f"{interaction.user.mention}, vous avez crafté **{recette['nom']}** avec succès ! \nCe nouvel objet a été ajouté à votre inventaire.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/190/190411.png")
        embed.add_field(name="Nom de l'objet", value=f"{recette['nom']}", inline=False)
        embed.add_field(name="Prix", value=f"{recette['prix']} pièces", inline=True)
        embed.add_field(name="Équipable", value=f"{'Oui' if recette['equipable'] else 'Non'}", inline=True)

        if "slot" in recette:
            embed.add_field(name="Slot", value=recette["slot"], inline=True)
        if "bonus" in recette and recette["bonus"]:
            bonus_text = "\n".join(f"{k}: {v}" for k, v in recette["bonus"].items())
            embed.add_field(name="Bonus", value=bonus_text, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="voir_recettes", description="Voir la liste des recettes disponibles.")
    async def voir_recettes(self, interaction: discord.Interaction):
        if not self.recettes_data:
            embed = discord.Embed(
                title="📜 Recettes disponibles",
                description="Aucune recette disponible pour le moment.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title="📜 Recettes disponibles",
            description="Voici la liste des recettes disponibles :",
            color=discord.Color.blue()
        )

        for nom, recette in self.recettes_data.items():
            ressources = ", ".join([f"{r} x{q}" for r, q in recette["ressources"].items()])
            description = recette.get("description", "Aucune description disponible.")
            slot = recette.get("slot", "Non spécifié")
            bonus = ", ".join([f"{stat} +{val}" for stat, val in recette.get("bonus", {}).items()]) or "Aucun"

            embed.add_field(
                name=recette["nom"],
                value=(
                    f"**Ressources nécessaires :** {ressources}\n"
                    f"**Description :** {description}\n"
                    f"**Slot :** {slot}\n"
                    f"**Bonus :** {bonus}"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="voir_ressources", description="Affiche la liste des ressources.")
    @app_commands.checks.has_permissions(administrator=True)
    async def voir_ressources(self, interaction: discord.Interaction):
        ressources_list = self.ressources_data.get("liste_ressources")

        if not ressources_list:
            await interaction.response.send_message("Aucune ressource n'est enregistrée!",
                                                    ephemeral=True)
            return

        embed = discord.Embed(title="Liste des Ressources", color=discord.Color.blue())

        for ressource in ressources_list:
            embed.add_field(name=ressource["nom"], value=f"Taux de drop : {ressource['drop_chance']}%", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="creer_ressource",
                          description="Créer une nouvelle ressource (administrateurs uniquement).")
    @app_commands.checks.has_permissions(administrator=True)
    async def creer_ressource(self, interaction: discord.Interaction, nom: str, drop_chance: int):

        if nom in self.ressources_data.get("liste_ressources", []):
            embed = discord.Embed(
                title="⚠️ Ressource existante",
                description=f"La ressource `{nom}` existe déjà dans le système.",
                color=0xFFAA00
            )
            await interaction.response.send_message(embed=embed)
            return

        if drop_chance < 1 or drop_chance > 100:
            embed = discord.Embed(
                title="⚠️ Taux de drop invalide",
                description="Le taux de drop doit être compris entre 1 et 100.",
                color=0xFFAA00
            )
            await interaction.response.send_message(embed=embed)
            return

        self.ressources_data["liste_ressources"].append({
            "nom": nom,
            "drop_chance": drop_chance
        })

        self.save_data(self.RESSOURCES_FILE, self.ressources_data)

        embed = discord.Embed(
            title="✅ Ressource créée",
            description=f"La ressource `{nom}` a été créée avec un taux de drop de {drop_chance}%.",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="ajouter_ressource", description="Ajouter une ressource à un utilisateur (administrateurs uniquement).")
    @app_commands.checks.has_permissions(administrator=True)
    async def ajouter_ressource(self, interaction: discord.Interaction, user: discord.Member, nom: str, quantite: int):
       
        if quantite <= 0:
            embed = discord.Embed(
                title="⚠️ Quantité invalide",
                description="La quantité doit être un **nombre entier positif**.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed)
            return

        
        user_id = str(user.id)

       
        if user_id not in self.ressources_data:
            self.ressources_data[user_id] = {}

        
        if nom in self.ressources_data[user_id]:
            self.ressources_data[user_id][nom] += quantite
        else:
            self.ressources_data[user_id][nom] = quantite

        
        self.save_data(self.RESSOURCES_FILE, self.ressources_data)

        
        embed = discord.Embed(
            title="✅ Ressource ajoutée",
            description=(f"**{quantite} unités** de la ressource `{nom}` ont été ajoutées "
                         f"à l'inventaire de {user.mention}."),
            color=0x00FF00
        )
        embed.set_thumbnail(url="https://emoji.gg/assets/emoji/4425-check.png")
        await interaction.response.send_message(embed=embed)

#--------------------------------------------------------------------------------------------------------

async def setup(bot):
    await bot.add_cog(Craft(bot))