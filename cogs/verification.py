import disnake
from disnake.ext import commands
from cogs.mangocog import MangoCog
from cogs.dotastats import opendota_query
from utils.tools.globals import botdata
from utils.tools.helpers import UserError

RANK_NAMES = ["Unranked", "Herald", "Guardian", "Crusader", 
              "Archon", "Legend", "Ancient", "Divine", "Immortal"]


class Verification(MangoCog):
    """Cog for Dota 2 rank verification and role assignment"""

    def __init__(self, bot):
        MangoCog.__init__(self, bot)

    def get_rank_name(self, rank_tier: int, leaderboard_rank: int = None) -> str:
        """Convert rank_tier to rank name string"""
        if leaderboard_rank:
            return "Immortal"
        tier = (rank_tier or 0) // 10
        return RANK_NAMES[min(tier, 8)]

    @commands.slash_command(name="get-verified")
    async def get_verified(self, inter: disnake.CmdInter):
        """Verify your Dota 2 rank and get the corresponding role"""
        await self.safe_defer(inter)
        
        userinfo = botdata.userinfo(inter.author.id)
        if userinfo.steam is None:
            raise UserError("You haven't linked your Steam account yet! "
                          "Use `/userconfig steam <your_steam_id>` first.")
        
        steam32 = userinfo.steam
        
        playerinfo = await opendota_query(f"/players/{steam32}")
        
        rank_tier = playerinfo.get("rank_tier")
        leaderboard_rank = playerinfo.get("leaderboard_rank")
        rank_name = self.get_rank_name(rank_tier, leaderboard_rank)
        
        guildinfo = botdata.guildinfo(inter.guild_id)
        rank_role_ids = guildinfo.rank_role_ids
        
        if not rank_role_ids:
            raise UserError("Rank roles haven't been configured for this server. "
                          "An admin needs to run `/setupranks` first.")
        
        roles_to_remove = []
        for rname, role_id in rank_role_ids.items():
            role = inter.guild.get_role(role_id)
            if role and role in inter.author.roles:
                roles_to_remove.append(role)
        
        if roles_to_remove:
            await inter.author.remove_roles(*roles_to_remove)
        
        if rank_name == "Unranked":
            linked_role_id = rank_role_ids.get("LinkedSteam")
            if not linked_role_id:
                raise UserError("You don't have a ranked medal yet, and no 'Linked Steam' role is configured. "
                              "Play some ranked games first, or ask an admin to configure the Linked Steam role.")
            
            linked_role = inter.guild.get_role(linked_role_id)
            if not linked_role:
                raise UserError("The 'Linked Steam' role no longer exists.")
            
            await inter.author.add_roles(linked_role)
            await inter.send(f"✅ Verified! You don't have a ranked medal yet, so you've been given the **Linked Steam** role.")
            return
        
        new_role_id = rank_role_ids.get(rank_name)
        if not new_role_id:
            raise UserError(f"No role configured for {rank_name}.")
        
        new_role = inter.guild.get_role(new_role_id)
        if not new_role:
            raise UserError(f"The {rank_name} role no longer exists.")
        
        await inter.author.add_roles(new_role)
        
        await inter.send(f"✅ Verified! You are now **{rank_name}**")

    @commands.slash_command()
    @commands.has_permissions(administrator=True)
    async def setupranks(
        self, 
        inter: disnake.CmdInter,
        herald: disnake.Role,
        guardian: disnake.Role,
        crusader: disnake.Role,
        archon: disnake.Role,
        legend: disnake.Role,
        ancient: disnake.Role,
        divine: disnake.Role,
        immortal: disnake.Role,
        linked_steam: disnake.Role = None
    ):
        """Configure rank roles for this server (Admin only)
        
        Parameters
        ----------
        herald: The Herald rank role
        guardian: The Guardian rank role
        crusader: The Crusader rank role
        archon: The Archon rank role
        legend: The Legend rank role
        ancient: The Ancient rank role
        divine: The Divine rank role
        immortal: The Immortal rank role
        linked_steam: The role for users with linked Steam but no ranked medal (optional)
        """
        guildinfo = botdata.guildinfo(inter.guild_id)
        role_config = {
            "Herald": herald.id,
            "Guardian": guardian.id,
            "Crusader": crusader.id,
            "Archon": archon.id,
            "Legend": legend.id,
            "Ancient": ancient.id,
            "Divine": divine.id,
            "Immortal": immortal.id
        }
        if linked_steam:
            role_config["LinkedSteam"] = linked_steam.id
        
        guildinfo.rank_role_ids = role_config
        
        msg = "✅ Rank roles configured successfully!"
        if linked_steam:
            msg += f"\n📎 Linked Steam role: {linked_steam.mention}"
        await inter.send(msg)


def setup(bot):
    bot.add_cog(Verification(bot))
