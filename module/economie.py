#-----Initialisation--------------------------------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--------------------------------------------------------------------------------------------------------

#-----Lancement-JSON--------------------------------------------------------------------------------------------------------

class Economie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
        self.DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
        self.INVENTAIRE_FILE = os.path.join(self.DATA_FOLDER, "inventaire.json")
        self.SOLDE_FILE = os.path.join(self.DATA_FOLDER, "solde.json")
        self.BOUTIQUE_FILE = os.path.join(self.DATA_FOLDER, "boutique.json")
        self.EQUIPEMENT_FILE = os.path.join(self.DATA_FOLDER, "equipement.json")
        
       
        self.DEFAULT_INVENTAIRE = {}
        self.DEFAULT_SOLDE = {}
        self.DEFAULT_BOUTIQUE = {"boutique": [], "dark_boutique": [], "vip_boutique": []}
        self.DEFAULT_EQUIPEMENT = {}

       
        self.inventaire_data = self.load_data(self.INVENTAIRE_FILE, self.DEFAULT_INVENTAIRE)
        self.solde_data = self.load_data(self.SOLDE_FILE, self.DEFAULT_SOLDE)
        self.boutique_data = self.load_data(self.BOUTIQUE_FILE, self.DEFAULT_BOUTIQUE)
        self.equipement_data = self.load_data(self.EQUIPEMENT_FILE, self.DEFAULT_EQUIPEMENT)

    def load_data(self, file_name, default_data):
        
        if not os.path.exists(file_name):
            
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump(default_data, file, indent=4)
        
        with open(file_name, "r", encoding="utf-8") as file:
            return json.load(file)

    def save_data(self, file_name, data):
        
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

#--------------------------------------------------------------------------------------------------------

#-----Economie--------------------------------------------------------------------------------------------------------

    
    @app_commands.command(name="solde", description="Voir votre solde d'écus, cristaux noirs et points de fidélité.")
    async def solde(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

       
        if user_id not in self.solde_data:
            self.solde_data[user_id] = {"ecus": 0, "cristaux_noirs": 0, "points_fidelite": 0}
            self.save_data(self.SOLDE_FILE, self.solde_data)
        
        solde = self.solde_data[user_id]

        
        embed = discord.Embed(title="Votre Solde", color=discord.Color.blue())
        embed.add_field(name="💰 Écus", value=solde['ecus'], inline=False)
        embed.add_field(name="💎 Cristaux Noirs", value=solde['cristaux_noirs'], inline=False)
        embed.add_field(name="⭐ Points de Fidélité", value=solde['points_fidelite'], inline=False)
        embed.set_footer(text=f"Requête de {interaction.user.name}")

        
        await interaction.response.send_message(embed=embed)


    
    @app_commands.command(name="boutique", description="Voir les articles disponibles dans la boutique.")
    async def boutique(self, interaction: discord.Interaction):
        if not self.boutique_data["boutique"]:
            await interaction.response.send_message("La boutique est vide pour le moment. 😢")
        else:
            embed = discord.Embed(
                title="🛒 Boutique",
                description="Voici les articles disponibles dans la boutique :",
                color=discord.Color.blue()
            )
            
            for item in self.boutique_data["boutique"]:
               
                embed.add_field(
                    name=f"✨ {item['nom']}",
                    value=f"{item['prix']} écus",
                    inline=False
                )
            
            
            embed.set_footer(text="Faites vos achats avec plaisir! 🛍️")
            
            await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="dark_boutique", description="Voir les articles disponibles dans la Dark-Boutique.")
    async def dark_boutique(self, interaction: discord.Interaction):
        if not self.boutique_data["dark_boutique"]:
            embed = discord.Embed(
                title="🛒 Dark-Boutique",
                description="La Dark-Boutique est vide pour le moment. 😢",
                color=discord.Color.dark_purple()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="🛒 Dark-Boutique",
                description="Voici les articles disponibles dans la Dark-Boutique :",
                color=discord.Color.dark_purple()
            )
            
            for item in self.boutique_data["dark_boutique"]:
                embed.add_field(
                    name=f"🔹 {item['nom']}",
                    value=f"{item['prix']} cristaux noirs",
                    inline=False
                )
            
            embed.set_footer(text="Profitez de votre shopping! 🛍️")
            await interaction.response.send_message(embed=embed)

   
    @app_commands.command(name="vip_boutique", description="Voir les articles disponibles dans la boutique VIP.")
    async def vip_boutique(self, interaction: discord.Interaction):
        if not self.boutique_data["vip_boutique"]:
            embed = discord.Embed(
                title="🛍️ Boutique VIP",
                description="La boutique VIP est vide pour le moment.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="🛍️ Boutique VIP",
                description="Voici les articles disponibles dans la boutique VIP :",
                color=0x00ff00
            )
            for item in self.boutique_data["vip_boutique"]:
                embed.add_field(
                    name=item['nom'],
                    value=f"{item['prix']} points de fidélité",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="ajouter_item", description="Ajouter un article dans la boutique.")
    @app_commands.describe(
        boutique="La boutique où ajouter l'article (boutique, dark_boutique, vip_boutique)",
        nom="Nom de l'article",
        prix="Prix de l'article",
        equipable="Si l'article est équipable ou non",
        slot="Le slot où l'article sera équipé (si applicable)",
        bonus="Les bonus sous forme de 'stat=value' séparés par des virgules"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ajouter_item(self, interaction: discord.Interaction, boutique: str, nom: str, prix: int, equipable: bool, slot: str = None, bonus: str = None):
        if boutique not in self.boutique_data:
            embed = discord.Embed(
                title="Erreur", 
                description="Boutique invalide. Utilisez 'boutique', 'dark_boutique', ou 'vip_boutique'.", 
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        if equipable:
            valid_slots = ["arme", "Bouclier", "accessoire", "heaume", "cuirasse", "grèves", "gantelets", "bottes", "espallières", "ceinturon", "cape"]
            if not slot or slot not in valid_slots:
                embed = discord.Embed(
                    title="Erreur", 
                    description=f"Slot invalide ou manquant pour un objet équipable. Utilisez l'un des suivants : {', '.join(valid_slots)}.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

            try:
                bonus_dict = {}
                if bonus:
                    for b in bonus.split(","):
                        stat, value = b.split("=")
                        bonus_dict[stat.strip()] = int(value)
            except Exception as e:
                embed = discord.Embed(
                    title="Erreur", 
                    description=f"Erreur lors de l'analyse des bonus : {e}", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

            item = {"nom": nom, "prix": prix, "equipable": True, "slot": slot, "bonus": bonus_dict}
        else:
            item = {"nom": nom, "prix": prix, "equipable": False}

        self.boutique_data[boutique].append(item)
        self.save_data(self.BOUTIQUE_FILE, self.boutique_data)

        equipable_text = "✅ Oui" if equipable else "❌ Non"
        slot_text = slot if slot else "N/A"
        bonus_text = bonus_dict if equipable else "Aucun"
        embed = discord.Embed(
            title="Article ajouté", 
            description=f"L'article '{nom}' a été ajouté à la boutique '{boutique}'.", 
            color=discord.Color.green()
        )
        embed.add_field(name="Prix", value=prix, inline=True)
        embed.add_field(name="Équipable", value=equipable_text, inline=True)
        embed.add_field(name="Slot", value=slot_text, inline=True)
        embed.add_field(name="Bonus", value=bonus_text, inline=True)
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="ajouter_devise", description="Ajouter des devises à un utilisateur (administrateurs uniquement).")
    @app_commands.checks.has_permissions(administrator=True)
    async def ajouter_devise(self, interaction: discord.Interaction, membre: discord.Member, devise: str, montant: int):
        
        if devise not in ["ecus", "cristaux_noirs", "points_fidelite"]:
            embed = discord.Embed(title="Erreur", description="Devise invalide. Utilisez 'ecus', 'cristaux_noirs', ou 'points_fidelite'.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        user_id = str(membre.id)

        
        if user_id not in self.solde_data:
            self.solde_data[user_id] = {"ecus": 0, "cristaux_noirs": 0, "points_fidelite": 0}

        
        self.solde_data[user_id][devise] += montant
        self.save_data(self.SOLDE_FILE, self.solde_data)

       
        embed = discord.Embed(title="Succès", description=f"{montant} {devise.replace('_', ' ')} ont été ajoutés au solde de {membre.mention}.", color=discord.Color.green())
        embed.set_footer(text="✅ Opération réussie")
        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="retirer_devise", description="Retirer des devises d'un utilisateur (administrateurs uniquement).")
    @app_commands.checks.has_permissions(administrator=True)
    async def retirer_devise(self, interaction: discord.Interaction, membre: discord.Member, devise: str, montant: int):
        
        
        if devise not in ["ecus", "cristaux_noirs", "points_fidelite"]:
            embed = discord.Embed(title="Erreur", description="Devise invalide. Utilisez 'ecus', 'cristaux_noirs', ou 'points_fidelite'.", color=discord.Color.red())
            embed.set_footer(text="⚠️ Veuillez réessayer.")
            await interaction.response.send_message(embed=embed)
            return

        user_id = str(membre.id)

        
        if user_id not in self.solde_data:
            self.solde_data[user_id] = {"ecus": 0, "cristaux_noirs": 0, "points_fidelite": 0}

       
        self.solde_data[user_id][devise] = max(self.solde_data[user_id][devise] - montant, 0)

       
        self.save_data(self.SOLDE_FILE, self.solde_data)

       
        embed = discord.Embed(title="Succès", description=f"{montant} {devise.replace('_', ' ')} ont été retirés du solde de {membre.mention}.", color=discord.Color.green())
        embed.set_footer(text="✅ Opération réussie.")
        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="acheter", description="Acheter un article dans une boutique.")
    async def acheter(self, interaction: discord.Interaction, boutique: str, nom_item: str):
        
        user_id = str(interaction.user.id)

        
        if user_id not in self.solde_data:
            self.solde_data[user_id] = {"ecus": 0, "cristaux_noirs": 0, "points_fidelite": 0}
            self.save_data(self.SOLDE_FILE, self.solde_data)

       
        if boutique not in self.boutique_data:
            embed = discord.Embed(description="❌ Boutique invalide. Utilisez 'boutique', 'dark_boutique', ou 'vip_boutique'.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

       
        article = next(
            (item for item in self.boutique_data[boutique] if item["nom"].lower() == nom_item.lower()),
            None
        )
        if not article:
            embed = discord.Embed(description=f"❌ L'article '{nom_item}' n'existe pas dans la {boutique.replace('_', ' ')}.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        
        devise = "ecus" if boutique == "boutique" else "cristaux_noirs" if boutique == "dark_boutique" else "points_fidelite"
        prix = article["prix"]

        
        if self.solde_data[user_id][devise] < prix:
            embed = discord.Embed(description=f"❌ Vous n'avez pas assez de {devise.replace('_', ' ')} pour acheter cet article.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return
        
        self.solde_data[user_id][devise] -= prix
        self.save_data(self.SOLDE_FILE, self.solde_data)

        if user_id not in self.inventaire_data:
            self.inventaire_data[user_id] = []
        self.inventaire_data[user_id].append(article)
        self.save_data(self.INVENTAIRE_FILE, self.inventaire_data)

        
        embed = discord.Embed(description=f"🎉 Vous avez acheté **{article['nom']}** pour **{prix} {devise.replace('_', ' ')}** !\n📦 Il a été ajouté à votre inventaire.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="vendre_item", description="Vendre un article de votre inventaire.")
    async def vendre_item(self, interaction: discord.Interaction, nom_item: str):
        
        user_id = str(interaction.user.id)

       
        if user_id not in self.inventaire_data or not self.inventaire_data[user_id]:
            embed = discord.Embed(
                title="Inventaire vide",
                description="❌ Vous n'avez aucun article dans votre inventaire à vendre.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        
        inventaire = self.inventaire_data[user_id]
        article_index = next((i for i, item in enumerate(inventaire) if item["nom"].lower() == nom_item.lower()), None)

        if article_index is None:
            embed = discord.Embed(
                title="Article introuvable",
                description=f"❌ L'article '{nom_item}' n'est pas présent dans votre inventaire.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return

        
        article = inventaire.pop(article_index)
        prix_revente = article["prix"] 

        devise = "écus"  
        user_solde = self.solde_data.get(user_id, {"ecus": 0, "cristaux_noirs": 0, "points_fidelite": 0})
        user_solde["ecus"] += prix_revente

        
        self.solde_data[user_id] = user_solde
        self.inventaire_data[user_id] = inventaire

        self.save_data(self.SOLDE_FILE, self.solde_data)
        self.save_data(self.INVENTAIRE_FILE, self.inventaire_data)

        embed = discord.Embed(
            title="Article vendu !",
            description=f"✅ Vous avez vendu **{article['nom']}** pour **{prix_revente} écus**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Votre solde actuel", value=f"💰 {user_solde['ecus']} écus", inline=False)
        embed.set_footer(text="Merci d'utiliser notre système de revente !", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventaire", description="Affiche l'inventaire de l'utilisateur avec détails des objets.")
    async def inventaire(self, interaction: discord.Interaction):
        """Affiche l'inventaire d'un utilisateur."""
        user_id = str(interaction.user.id)

        
        if user_id not in self.inventaire_data or not self.inventaire_data[user_id]:
            embed = discord.Embed(
                title="Inventaire vide",
                description="📦 Votre inventaire est vide.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        
        item_counts = {}
        for item in self.inventaire_data[user_id]:
            item_name = item['nom']
            if item_name in item_counts:
                item_counts[item_name]['count'] += 1
            else:
                item_counts[item_name] = {'count': 1, 'details': item}

      
        embed = discord.Embed(
            title="📜 Votre inventaire",
            color=discord.Color.blue()
        )

        for item_name, data in item_counts.items():
            count = data['count']
            details = data['details']
            equipable = "Équipable" if details.get("equipable", False) else "Non-équipable"
            slot = details.get("slot", "N/A")
            bonus = details.get("bonus", "Aucun")

            embed.add_field(
                name=f"{item_name} x{count}",
                value=f"🛠️ {equipable}\n🗂️ Slot : {slot}\n✨ Bonus : {bonus}",
                inline=False
            )

        embed.set_footer(text="Consultez vos objets et préparez-vous à l'aventure !", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

#--------------------------------------------------------------------------------------------------------

#-----Equipement--------------------------------------------------------------------------------------------------------

    
    @app_commands.command(name="equiper", description="Permet d'équiper un objet de votre inventaire.")
    async def equiper(self, interaction: discord.Interaction, nom_item: str):
        """Permet à un utilisateur d'équiper un objet de son inventaire."""
        user_id = str(interaction.user.id)

       
        if user_id not in self.inventaire_data or not self.inventaire_data[user_id]:
            embed = discord.Embed(
                title="Inventaire vide",
                description="❌ Votre inventaire est vide.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        
        item = next(
            (obj for obj in self.inventaire_data[user_id] if obj["nom"].lower() == nom_item.lower()), 
            None
        )
        if not item:
            embed = discord.Embed(
                title="Objet introuvable",
                description=f"❌ L'objet '{nom_item}' n'est pas dans votre inventaire.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        
        if not item.get("equipable", False):
            embed = discord.Embed(
                title="Objet non-équipable",
                description=f"❌ L'objet '{item['nom']}' n'est pas équipable.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        
        slot = item["slot"]

        
        if user_id not in self.equipement_data:
            self.equipement_data[user_id] = {}

        
        if slot in self.equipement_data[user_id] and self.equipement_data[user_id][slot]:
            embed = discord.Embed(
                title="Slot occupé",
                description=f"❌ Vous avez déjà un objet équipé dans le slot **{slot}**. Déséquipez-le d'abord.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

       
        self.equipement_data[user_id][slot] = item
        self.inventaire_data[user_id].remove(item)

       
        self.save_data(self.EQUIPEMENT_FILE, self.equipement_data)
        self.save_data(self.INVENTAIRE_FILE, self.inventaire_data)

      
        embed = discord.Embed(
            title="Objet équipé",
            description=f"✅ Vous avez équipé **{item['nom']}** dans le slot **{slot}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="✨ Bonus", value=item.get('bonus', 'Aucun'), inline=False)
        embed.set_footer(text="Préparez-vous pour l'aventure !", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="desequiper", description="Déséquipe un objet d'un slot spécifique.")
    @app_commands.describe(slot="Le slot de l'objet à déséquiper (ex: casque, arme, etc.)")
    async def desequiper(self, interaction: discord.Interaction, slot: str):
        """Permet à un utilisateur de déséquiper un objet d'un slot spécifique."""
        user_id = str(interaction.user.id)

        
        if user_id not in self.equipement_data or not self.equipement_data[user_id].get(slot):
            embed = discord.Embed(
                title="Slot vide",
                description=f"❌ Vous n'avez aucun objet équipé dans le slot **{slot}**.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        
        item = self.equipement_data[user_id][slot]
        self.equipement_data[user_id][slot] = None  

       
        if user_id not in self.inventaire_data:
            self.inventaire_data[user_id] = []
        self.inventaire_data[user_id].append(item)

        
        self.save_data(self.EQUIPEMENT_FILE, self.equipement_data)
        self.save_data(self.INVENTAIRE_FILE, self.inventaire_data)

        
        embed = discord.Embed(
            title="Objet déséquipé",
            description=f"✅ Vous avez déséquipé **{item['nom']}** du slot **{slot}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="📦 Inventaire", value="L'objet a été ajouté à votre inventaire.", inline=False)
        embed.set_footer(text="Réorganisez vos équipements selon vos besoins !", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=False)

 
    @app_commands.command(name="equipement", description="Affiche les objets que vous avez équipés.")
    async def afficher_equipement(self, interaction: discord.Interaction):
        """Affiche les équipements actuels d'un utilisateur."""
        user_id = str(interaction.user.id)

        
        if user_id not in self.equipement_data or not any(self.equipement_data[user_id].values()):
            embed = discord.Embed(
                title="Aucun équipement",
                description="❌ Vous n'avez aucun objet équipé.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

       
        embed = discord.Embed(
            title="Vos équipements",
            description="Voici les objets actuellement équipés :",
            color=discord.Color.blue()
        )

        for type_objet, item in self.equipement_data[user_id].items():
            if item:
                embed.add_field(
                    name=f"{type_objet.capitalize()} :",
                    value=f"**{item['nom']}** (✨ Bonus : {item['bonus']})",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"{type_objet.capitalize()} :",
                    value="Aucun objet équipé",
                    inline=False
                )

        embed.set_footer(
            text="Gérez vos équipements pour maximiser vos performances !",
            icon_url=interaction.user.avatar.url
        )

        await interaction.response.send_message(embed=embed, ephemeral=False)

#--------------------------------------------------------------------------------------------------------


async def setup(bot):
    await bot.add_cog(Economie(bot)) 