import disnake
from disnake.ext import commands
from cogs.mangocog import MangoCog
from cogs.dotastats import opendota_query
from utils.tools.globals import botdata
from utils.tools.helpers import UserError

RANK_NAMES = ["Unranked", "Herald", "Guardian", "Crusader", 
              "Archon", "Legend", "Ancient", "Divine", "Immortal"]

# Rank tiers for comparison (higher number = higher rank)
RANK_TIERS = {
    "Unranked": 0, "Uncalibrated": 0,
    "Herald": 1, "Guardian": 2, "Crusader": 3, "Archon": 4,
    "Legend": 5, "Ancient": 6, "Divine": 7, "Immortal": 8
}


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
    
    def get_user_current_rank(self, member: disnake.Member, rank_role_ids: dict) -> str | None:
        """Get the user's current rank role name, if any"""
        for rank_name in ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"]:
            role_id = rank_role_ids.get(rank_name)
            if role_id:
                role = member.guild.get_role(role_id)
                if role and role in member.roles:
                    return rank_name
        return None

    @commands.slash_command(name="get-badge")
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
        new_rank_name = self.get_rank_name(rank_tier, leaderboard_rank)
        
        guildinfo = botdata.guildinfo(inter.guild_id)
        rank_role_ids = guildinfo.rank_role_ids
        
        if not rank_role_ids:
            raise UserError("Rank roles haven't been configured for this server. "
                          "An admin needs to run `/setupranks` first.")
        
        # Get user's current rank badge (if any)
        current_rank_name = self.get_user_current_rank(inter.author, rank_role_ids)
        current_tier = RANK_TIERS.get(current_rank_name, 0) if current_rank_name else 0
        new_tier = RANK_TIERS.get(new_rank_name, 0)
        
        # Handle Unranked/Uncalibrated users
        if new_rank_name == "Unranked":
            # Remove existing rank roles (but NOT LinkedSteam)
            roles_to_remove = []
            for rname, role_id in rank_role_ids.items():
                if rname == "LinkedSteam":
                    continue
                role = inter.guild.get_role(role_id)
                if role and role in inter.author.roles:
                    roles_to_remove.append(role)
            
            if roles_to_remove:
                await inter.author.remove_roles(*roles_to_remove)
            
            uncalibrated_role_id = rank_role_ids.get("Uncalibrated")
            if not uncalibrated_role_id:
                raise UserError("You don't have a ranked medal yet, and no 'Uncalibrated' role is configured. "
                              "Play some ranked games first, or ask an admin to configure the Uncalibrated role.")
            
            uncalibrated_role = inter.guild.get_role(uncalibrated_role_id)
            if not uncalibrated_role:
                raise UserError("The 'Uncalibrated' role no longer exists.")
            
            await inter.author.add_roles(uncalibrated_role)
            await inter.send(f"✅ Verified! You don't have a ranked medal yet, so you've been given the **Uncalibrated** role.")
            return
        
        # Rank protection logic
        tier_difference = current_tier - new_tier
        
        # Case 1: Rank UP or same rank or no previous rank
        if new_tier >= current_tier or current_rank_name is None:
            # Remove existing rank roles (but NOT LinkedSteam)
            roles_to_remove = []
            for rname, role_id in rank_role_ids.items():
                if rname == "LinkedSteam":
                    continue
                role = inter.guild.get_role(role_id)
                if role and role in inter.author.roles:
                    roles_to_remove.append(role)
            
            if roles_to_remove:
                await inter.author.remove_roles(*roles_to_remove)
            
            new_role_id = rank_role_ids.get(new_rank_name)
            if not new_role_id:
                raise UserError(f"No role configured for {new_rank_name}.")
            
            new_role = inter.guild.get_role(new_role_id)
            if not new_role:
                raise UserError(f"The {new_rank_name} role no longer exists.")
            
            await inter.author.add_roles(new_role)
            
            if new_tier > current_tier and current_rank_name:
                await inter.send(f"🎉 Congratulations! You've ranked up from **{current_rank_name}** to **{new_rank_name}**!")
            else:
                await inter.send(f"✅ Verified! You are now **{new_rank_name}**")
            return
        
        # Case 2: Dropped by 1 tier - retain old rank
        if tier_difference == 1:
            await inter.send(f"📉 You have fallen to **{new_rank_name}**, but you may still retain your **{current_rank_name}** badge. Keep grinding!")
            return
        
        # Case 3: Dropped by 2+ tiers - update to new rank
        roles_to_remove = []
        for rname, role_id in rank_role_ids.items():
            if rname == "LinkedSteam":
                continue
            role = inter.guild.get_role(role_id)
            if role and role in inter.author.roles:
                roles_to_remove.append(role)
        
        if roles_to_remove:
            await inter.author.remove_roles(*roles_to_remove)
        
        new_role_id = rank_role_ids.get(new_rank_name)
        if not new_role_id:
            raise UserError(f"No role configured for {new_rank_name}.")
        
        new_role = inter.guild.get_role(new_role_id)
        if not new_role:
            raise UserError(f"The {new_rank_name} role no longer exists.")
        
        await inter.author.add_roles(new_role)
        
        await inter.send(f"📉 Your rank has been updated from **{current_rank_name}** to **{new_rank_name}**.")

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
        linked_steam: disnake.Role = None,
        uncalibrated: disnake.Role = None
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
        linked_steam: Role given when user links Steam via /userconfig (optional)
        uncalibrated: Role for verified users without a ranked medal (optional)
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
        if uncalibrated:
            role_config["Uncalibrated"] = uncalibrated.id
        
        guildinfo.rank_role_ids = role_config
        
        msg = "✅ Rank roles configured successfully!"
        if linked_steam:
            msg += f"\n🔗 Linked Steam role: {linked_steam.mention}"
        if uncalibrated:
            msg += f"\n🎮 Uncalibrated role: {uncalibrated.mention}"
        await inter.send(msg)


def setup(bot):
    bot.add_cog(Verification(bot))
