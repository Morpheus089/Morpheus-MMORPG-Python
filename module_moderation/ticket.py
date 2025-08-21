#-----Initialisation--------------------------------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import io

#--------------------------------------------------------------------------------------------------------

#-----Code--------------------------------------------------------------------------------------------------------

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket", description="Créer un ticket d'assistance.")
    async def create_ticket(self, interaction: discord.Interaction, raison: str):
        """
        Crée un ticket d'assistance dans un salon spécifique.
        """
        support_channel_id = 1330242691883208817  
        support_channel = self.bot.get_channel(support_channel_id)
        
        if interaction.channel.id != support_channel.id:
            await interaction.response.send_message(
                "🚫 Vous devez utiliser cette commande dans le salon de support.", 
                ephemeral=True
            )
            return

        category = discord.utils.get(interaction.guild.categories, name="Tickets")
        if not category:
            category = await interaction.guild.create_category("Tickets")

        existing_ticket = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name}")
        if existing_ticket:
            await interaction.response.send_message("🚫 Vous avez déjà un ticket ouvert.", ephemeral=True)
            return

        ticket_channel = await category.create_text_channel(f"ticket-{interaction.user.name}")
        await ticket_channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await ticket_channel.set_permissions(interaction.user, view_channel=True)

        staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
        if staff_role:
            await ticket_channel.set_permissions(staff_role, view_channel=True)

        if staff_role:
            await ticket_channel.send(content=f"{staff_role.mention}, un nouveau ticket a été ouvert !")

        embed = discord.Embed(
            title="🎟️ Ticket d'assistance créé",
            description=f"Salut {interaction.user.mention}, votre ticket a été créé !\n\n"
                        f"**Raison** : {raison}\n"
                        "Un membre du staff va vous répondre rapidement.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Ticket créé avec succès")
        await ticket_channel.send(embed=embed)
        await interaction.response.send_message(f"Votre ticket a été créé : {ticket_channel.mention}", ephemeral=True)

    @app_commands.command(name="fermer_ticket", description="Fermer un ticket.")
    async def fermer_ticket(self, interaction: discord.Interaction, raison: str):
        
        ticket_channel = interaction.channel
        if not ticket_channel.name.startswith("ticket-"):
            await interaction.response.send_message("🚫 Cette commande ne peut être utilisée que dans un salon de ticket.", ephemeral=True)
            return

        
        await interaction.response.send_message(
            "⚠️ Êtes-vous sûr de vouloir fermer ce ticket ? Répondez par 'oui' pour confirmer.",
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.content.lower() == "oui"

        try:
            await self.bot.wait_for("message", check=check, timeout=30.0)
        except TimeoutError:
            await interaction.followup.send("⏳ Temps écoulé, la commande a été annulée.", ephemeral=True)
            return

        
        transcript = io.StringIO()
        async for message in ticket_channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            transcript.write(f"[{timestamp}] {message.author.name}: {message.content}\n")

        transcript.seek(0)
        transcript_file = discord.File(transcript, filename=f"transcript-{ticket_channel.name}.txt")

        
        logs_channel = discord.utils.get(interaction.guild.text_channels, name="logs-tickets")
        if logs_channel:
            embed = discord.Embed(
                title="🗒️ Ticket fermé",
                description=f"**Auteur :** {interaction.user.mention}\n"
                            f"**Salon :** {ticket_channel.name}\n"
                            f"**Raison :** {raison}\n"
                            f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                color=discord.Color.red()
            )
            embed.set_footer(text="Logs de ticket")
            await logs_channel.send(embed=embed, file=transcript_file)

        await ticket_channel.send("🔒 Ce ticket va être fermé...")
        await ticket_channel.delete()
        await interaction.followup.send("✅ Le ticket a été fermé avec succès.", ephemeral=True)

#--------------------------------------------------------------------------------------------------------

async def setup(bot):
    await bot.add_cog(Ticket(bot))