/*
	███╗   ███╗██╗ ██████╗ ██╗
	████╗ ████║██║██╔════╝ ██║
	██╔████╔██║██║██║  ███╗██║
	██║╚██╔╝██║██║██║   ██║██║
	██║ ╚═╝ ██║██║╚██████╔╝██║
	╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝.nut
		By @ZooL_Smith
*/

::migi_undefined <- "undefined"

::migi_player <- Entities.FindByClassname(null, "player")

// ====================================================
::migi_money <- Entities.FindByName(null, "migi_money"); if(migi_money == null)
{
	migi_money = Entities.CreateByClassname("game_money");
	migi_money.__KeyValueFromString("targetname", "migi_money");
	EntFireByHandle(migi_money, "SetMoneyAmount", "10000000", 0, null, null);
}
::migi_armor <- Entities.FindByName(null, "migi_armor"); if(migi_armor == null)
{
	migi_armor = Entities.CreateByClassname("game_player_equip");
	migi_armor.__KeyValueFromInt("spawnflags", 1+4);
	migi_armor.__KeyValueFromString("targetname", "migi_armor");
	migi_armor.__KeyValueFromString("item_assaultsuit", "1");
}
// ====================================================

::migi_giveWeapon <- function(weapon)
{
	local gpe = Entities.CreateByClassname("game_player_equip");
	gpe.__KeyValueFromInt(weapon, 5000);
	gpe.__KeyValueFromInt("spawnflags", 1+4);
	EntFireByHandle(gpe, "Use", "", 0, migi_player, migi_player);
	EntFireByHandle(gpe, "Kill", "", 0.01, null, null);
}

::migi_setHealth <- function(hp)
{
	migi_player.SetHealth(hp);
}

::migi_refillMoney <- function()
{
	EntFireByHandle(migi_money, "AddMoneyPlayer", "", 0, migi_player, migi_player);
}

::migi_refillArmor <- function()
{
	EntFireByHandle(migi_armor, "Use", "", 0, migi_player, migi_player);
}

::migi_setTeam <- function(team)
{
	migi_player.__KeyValueFromInt("teamnumber", team);
}

::migi_setViewmodel <- function(x,y,z,fov)
{
	if(x != migi_undefined) SendToConsole("viewmodel_offset_x "+x);
	if(x != migi_undefined) SendToConsole("viewmodel_offset_y "+y);
	if(x != migi_undefined) SendToConsole("viewmodel_offset_z "+z);
	if(x != migi_undefined) SendToConsole("viewmodel_fov "+fov);
}
