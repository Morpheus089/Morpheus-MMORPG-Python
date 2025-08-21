#-----Initialisation--------------------------------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--------------------------------------------------------------------------------------------------------

#-----Lancement-JSON--------------------------------------------------------------------------------------------------------

def load_data(file_name, default_data):
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(default_data, file, indent=4, ensure_ascii=False)
        return default_data
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON dans {file_name}: {e}")
        return default_data

def save_data(file_name, data):
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans {file_name}: {e}")

class Creatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
        self.DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
        self.creatures_file = os.path.join(self.DATA_FOLDER, "creatures.json")
        self.ressources_file = os.path.join(self.DATA_FOLDER, "ressources.json")
        self.inventaire_file = os.path.join(self.DATA_FOLDER, "inventaire.json")
        self.honneur_file = os.path.join(self.DATA_FOLDER, "honneur.json")

        if not os.path.exists(self.DATA_FOLDER):
            os.makedirs(self.DATA_FOLDER)

        self.creatures_data = load_data(self.creatures_file, {})
        self.ressources_data = load_data(self.ressources_file, {"liste_ressources": []})
        self.inventaire_data = load_data(self.inventaire_file, {})
        self.honneur_data = load_data(self.honneur_file, {})

        self.active_combat_sessions = {}

    def item_details(self, item_name):
        try:
            with open('items.json', 'r') as f:
                item_data = json.load(f)
                return item_data.get(item_name)
        except FileNotFoundError:
            print("items.json not found. Creating an empty one.")
            with open('items.json', 'w') as f:
                json.dump({}, f)
            return None
        except json.JSONDecodeError:
            print("items.json is not valid JSON. Returning None.")
            return None

    def ajouter_creature(self, nom, niveau, rarete, hp, puissance, ressources, items, honneur, exp_donner):
        self.creatures_data[nom] = {
            "niveau": niveau,
            "rarete": rarete,
            "hp": hp,
            "puissance": puissance,
            "ressources": ressources,
            "items": items,
            "honneur": honneur,
            "exp_donner": exp_donner
        }
        save_data(self.creatures_file, self.creatures_data)

#--------------------------------------------------------------------------------------------------------

#------Creature--------------------------------------------------------------------------------------------------

    @app_commands.command(name="ajouter_creature", description="Ajoute une nouvelle créature.")
    async def ajouter_creature_cmd(self, interaction: discord.Interaction,
                                   nom: str, niveau: int, rarete: str, hp: int,
                                   puissance: int, ressources: str, items: str, honneur: int, exp_donner: int):

        ressources_list = [r.strip() for r in ressources.split(',') if r.strip()]
        items_list = [i.strip() for i in items.split(',') if i.strip()]

        craft_cog = self.bot.get_cog("Craft")
        if craft_cog is None:
            await interaction.response.send_message("Le cog Craft n'a pas été trouvé.", ephemeral=True)
            return

        ressources_existantes = [
            ressource["nom"] for ressource in craft_cog.ressources_data.get("liste_ressources", [])
        ]
        ressources_invalides = [r for r in ressources_list if r not in ressources_existantes]

        if ressources_invalides:
            await interaction.response.send_message(f"Ressources inexistantes: {', '.join(ressources_invalides)}",
                                                    ephemeral=True)
            return

        try:
            exp_donner = int(exp_donner)  # Attempt to convert to integer
        except ValueError:
            await interaction.response.send_message(f"{exp_donner} n'est pas un nombre entier valide.", ephemeral=True)
            return

        self.ajouter_creature(nom, niveau, rarete, hp, puissance, ressources_list, items_list, honneur, exp_donner)
        await interaction.response.send_message(f"Créature '{nom}' ajoutée!")

    @app_commands.command(name="voir_creatures", description="Affiche toutes les créatures enregistrées.")
    async def voir_creatures_cmd(self, interaction: discord.Interaction):
        if not self.creatures_data:
            await interaction.response.send_message("Aucune créature enregistrée.")
            return
        embed = discord.Embed(title="Liste des Créatures", color=discord.Color.green())
        for nom, details in self.creatures_data.items():
            embed.add_field(
                name=nom, 
                value=(
                    f"Niveau: {details['niveau']}\n"
                    f"Rareté: {details['rarete']}\n"
                    f"HP: {details['hp']}\n"
                    f"Puissance: {details['puissance']}\n"
                    f"Honneur: {details['honneur']}\n"
                    f"Ressources: {', '.join(details['ressources'])}\n"
                    f"Exp donné: {details['exp_donner']}\n"
                ), 
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="apparaitre_creature_aléatoire", description="Fait apparaître une créature aléatoire.")
    async def apparaitre_creature_aleatoire_cmd(self, interaction: discord.Interaction):
        if not self.creatures_data:
            await interaction.response.send_message("Aucune créature disponible pour apparaître.")
            return

        creature_name = random.choice(list(self.creatures_data.keys()))
        creature = self.creatures_data[creature_name]
        creature['etat'] = "vivant"
        embed = discord.Embed(title=f"Une créature apparaît: {creature_name}", color=discord.Color.red())
        embed.add_field(name="Niveau", value=creature['niveau'])
        embed.add_field(name="Rareté", value=creature['rarete'])
        embed.add_field(name="HP", value=creature['hp'])
        embed.add_field(name="Puissance", value=creature['puissance'])
        embed.add_field(name="Ressources", value=", ".join(creature['ressources']))
        embed.add_field(name="Items", value=", ".join(creature['items']))
        embed.add_field(name="Honneur", value=creature['honneur'])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="apparaitre_creature", description="Fait apparaître une créature choisie.")
    async def apparaitre_creature_cmd(self, interaction: discord.Interaction, nom: str):
        if nom not in self.creatures_data:
            await interaction.response.send_message(f"La créature '{nom}' n'existe pas.", ephemeral=True)
            return

        creature = self.creatures_data[nom]
        creature['etat'] = "vivant"
        embed = discord.Embed(title=f"Une créature apparaît: {nom}", color=discord.Color.red())
        embed.add_field(name="Niveau", value=creature['niveau'])
        embed.add_field(name="Rareté", value=creature['rarete'])
        embed.add_field(name="HP", value=creature['hp'])
        embed.add_field(name="Puissance", value=creature['puissance'])
        embed.add_field(name="Ressources", value=", ".join(creature['ressources']))
        embed.add_field(name="Items", value=", ".join(creature['items']))
        embed.add_field(name="Honneur", value=creature['honneur'])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="terminer_combat", description="Force la fin d'un combat (admin uniquement).")
    @app_commands.checks.has_permissions(administrator=True)
    async def terminer_combat_cmd(self, interaction: discord.Interaction, creature_name: str):
        if creature_name not in self.creatures_data:
            await interaction.response.send_message(f"La créature '{creature_name}' n'existe pas.", ephemeral=True)
            return

        creature = self.creatures_data[creature_name]
        if "etat" in creature and creature["etat"] == "vivant":
            creature["etat"] = "non vivant"
            save_data(self.creatures_file, self.creatures_data)
            await interaction.response.send_message(
                f"L'état de la créature '{creature_name}' a été mis à jour. Le combat est terminé.", ephemeral=True)
        else:
            await interaction.response.send_message(f"La créature '{creature_name}' n'est pas en combat.",
                                                    ephemeral=True)

    @app_commands.command(name="creatures_vivantes", description="Affiche les créatures actuellement en vie.")
    async def creatures_vivantes_cmd(self, interaction: discord.Interaction):
        creatures_vivantes = [nom for nom, details in self.creatures_data.items() if details.get("etat") == "vivant"]

        if creatures_vivantes:
            embed = discord.Embed(title="Créatures vivantes", color=discord.Color.green())
            for creature_name in creatures_vivantes:
                embed.add_field(name=creature_name, value="Est en vie", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Aucune créature n'est actuellement en vie.", ephemeral=True)

    @app_commands.command(name="supprimer_creatures", description="Supprime une créature.")
    async def supprimer_creatures_cmd(self, interaction: discord.Interaction, nom: str):
        if nom not in self.creatures_data:
            await interaction.response.send_message(f"La créature '{nom}' n'existe pas.", ephemeral=True)
            return

        del self.creatures_data[nom]
        save_data(self.creatures_file, self.creatures_data)
        await interaction.response.send_message(f"La créature '{nom}' a été supprimée avec succès!")

    @app_commands.command(name="combat", description="Lance un combat contre une créature.")
    async def combat_cmd(self, interaction: discord.Interaction, creature_name: str):
        user_id = str(interaction.user.id)

        if creature_name not in self.creatures_data:
            await interaction.response.send_message(f"La créature '{creature_name}' n'existe pas.", ephemeral=True)
            return

        creature = self.creatures_data[creature_name]

        if creature.get("etat") != "vivant":
            await interaction.response.send_message(
                f"La créature '{creature_name}' n'est pas apparue.",
                ephemeral=True)
            return

        self.active_combat_sessions[user_id] = {
            "creature_name": creature_name,
            "creature_hp": creature["hp"],
            "player_hp": 100,
        }

        embed = discord.Embed(title=f"Combat contre {creature_name}!", color=discord.Color.red())
        embed.add_field(name="Vos HP", value=100)
        embed.add_field(name=f"HP de {creature_name}", value=creature["hp"])
        await interaction.response.send_message(embed=embed)
        await interaction.followup.send("Choisissez une action: `/attaque` ou `/fuir`.", ephemeral=True)

    def obtenir_loot(self, creature_name: str, user_id: str):
        if creature_name not in self.creatures_data:
            print(f"Erreur: La créature '{creature_name}' n'existe pas.")
            return None

        creature = self.creatures_data[creature_name]
        ressources = creature.get("ressources", [])

        if not ressources:
            print(f"Aucun objet à looter pour {creature_name}.")
            return None

        for item in ressources:
            for resource in self.ressources_data["liste_ressources"]:
                if resource["nom"] == item:
                    if "joueurs" not in resource:
                        resource["joueurs"] = {}
                    if user_id not in resource["joueurs"]:
                        resource["joueurs"][user_id] = {"count": 1}
                    else:
                        resource["joueurs"][user_id]["count"] += 1
                    break

        save_data(self.ressources_file, self.ressources_data)
        print(f"Objets obtenus: {ressources} pour le joueur {user_id}.")
        return ressources

    def donner_honneur(self, creature, user_id):
        honneur_donner = creature["honneur"]
        if user_id not in self.honneur_data:
            self.honneur_data[user_id] = {"honneur": 0}

        self.honneur_data[user_id]["honneur"] += honneur_donner

        save_data(self.honneur_file, self.honneur_data)

        print(f"Joueur {user_id} a gagné {honneur_donner} points d'honneur.")
        return honneur_donner

    def donner_xp(self, creature, user_id):
        xp_donne = creature["exp_donner"]
        xp_cog = self.bot.get_cog("Xp")
        if xp_cog:
            xp_cog.ajouter_xp(user_id, xp_donne)
            return xp_donne
        else:
            print("Le cog Xp n'a pas été trouvé.")
            return None

    @app_commands.command(name="attaque", description="Utilise une attaque contre la créature.")
    async def attaque_cmd(self, interaction: discord.Interaction, nom_attaque: str):
        user_id = str(interaction.user.id)

        if user_id not in self.active_combat_sessions:
            await interaction.response.send_message("Vous n'êtes pas en combat.", ephemeral=True)
            return

        attaque_cog = self.bot.get_cog("Attaque")
        if not attaque_cog:
            await interaction.response.send_message("Le cog Attaque n'a pas été trouvé.", ephemeral=True)
            return

        attaque = attaque_cog.attaque_data.get(nom_attaque)
        if not attaque:
            await interaction.response.send_message("Cette attaque n'existe pas.", ephemeral=True)
            return

        stats_cog = self.bot.get_cog("Stats")
        if not stats_cog:
            await interaction.response.send_message("Le cog Stats n'a pas été trouvé.", ephemeral=True)
            return

        combat = self.active_combat_sessions[user_id]
        creature_name = combat["creature_name"]
        creature = self.creatures_data[creature_name]

        stat_a_utiliser = attaque["stats_scale"]
        joueur_stats = stats_cog.get_stats(user_id)
        stat_joueur = joueur_stats.get(stat_a_utiliser, 0)
        player_damage = int(attaque["base damage"] + (stat_joueur * attaque["coefficient_de_damage"]))

        creature_damage = creature["puissance"]

        combat["player_hp"] -= creature_damage
        combat["creature_hp"] -= player_damage

        await interaction.response.send_message(f"Vous avez utilisé {nom_attaque} et infligé {player_damage} dégâts !")
        await interaction.followup.send(f"{creature_name} vous inflige {creature_damage} dégâts !")

        if combat["creature_hp"] > 0 and combat["player_hp"] > 0:
            embed = discord.Embed(title=f"Combat contre {creature_name}!", color=discord.Color.red())
            embed.add_field(name="Vos HP", value=combat["player_hp"])
            embed.add_field(name=f"HP de {creature_name}", value=combat["creature_hp"])
            await interaction.followup.send(embed=embed)

        if combat["creature_hp"] <= 0:
            await interaction.followup.send(f"Vous avez vaincu {creature_name}! Félicitations!")
            loot = self.obtenir_loot(creature_name, user_id)
            xp_donne = self.donner_xp(creature, user_id)
            honneur_donne = self.donner_honneur(creature, user_id)
            if honneur_donne > 0:
                await interaction.followup.send(f"Honneur gagné: {honneur_donne}")
            if loot:
                await interaction.followup.send(f"Vous avez obtenu : {', '.join(loot)} !")
            await interaction.followup.send(f"XP gagné: {xp_donne}")
            del self.active_combat_sessions[user_id]

        elif combat["player_hp"] <= 0:
            await interaction.followup.send(f"Vous avez été vaincu par {creature_name}...")
            del self.active_combat_sessions[user_id]

    @app_commands.command(name="fuir", description="Fuir le combat.")
    async def fuir_cmd(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id in self.active_combat_sessions:
            del self.active_combat_sessions[user_id]
            await interaction.response.send_message("Vous avez fui le combat!", ephemeral=True)
        else:
            await interaction.response.send_message("Vous n'êtes pas en combat.", ephemeral=True)

#--------------------------------------------------------------------------------------------------------

async def setup(bot):
    await bot.add_cog(Creatures(bot))