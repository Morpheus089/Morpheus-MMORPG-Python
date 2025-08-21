#-----Initialisation--------------------------------------------------------------------------------------------------------

import discord
from discord import app_commands
from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--------------------------------------------------------------------------------------------------------

#-----Code--------------------------------------------------------------------------------------------------------

class Perssonalisation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="créer_embed", description="Créer un embed personnalisé (réservé au staff).")
    async def create_embed(
            self,
            interaction: discord.Interaction,
            title: str,
            description: str,
            color: str = "blue",
            image_url: str = None,
            thumbnail_url: str = None,
            footer: str = None
        ):
        """
        Crée un embed personnalisé avec les informations fournies.
        """

        
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "🚫 Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True
            )
            return

        
        await interaction.response.defer()

        
        color_map = {
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "purple": discord.Color.purple(),
            "yellow": discord.Color.gold()
        }
        embed_color = color_map.get(color.lower(), discord.Color.default())

        
        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color
        )

       
        if image_url:
            embed.set_image(url=image_url)

        
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        
        if footer:
            embed.set_footer(text=footer)

        
        await interaction.followup.send(embed=embed)

#--------------------------------------------------------------------------------------------------------

async def setup(bot):
    await bot.add_cog(Perssonalisation(bot))