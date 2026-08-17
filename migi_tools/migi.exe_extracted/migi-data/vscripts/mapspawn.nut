/*
	███╗   ███╗██╗ ██████╗ ██╗
	████╗ ████║██║██╔════╝ ██║
	██╔████╔██║██║██║  ███╗██║
	██║╚██╔╝██║██║██║   ██║██║
	██║ ╚═╝ ██║██║╚██████╔╝██║
	╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝.nut
		By @ZooL_Smith
*/


// use mapspawn_csgo.nut for your old stuff (who uses mapspawn anyway..)
try{DoIncludeScript("mapspawn_csgo.nut", null);}catch(e){}

// don't run on clientside
if (!("SendToConsole" in this))	return;

// runs on worldspawn's scope > doesn't anymore
::migi_init <- function() 
{
	
	printl("\n")
	printl("\t███╗   ███╗██╗ ██████╗ ██╗")
	printl("\t████╗ ████║██║██╔════╝ ██║")
	printl("\t██╔████╔██║██║██║  ███╗██║")
	printl("\t██║╚██╔╝██║██║██║   ██║██║")
	printl("\t██║ ╚═╝ ██║██║╚██████╔╝██║")
	printl("\t╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝.nut")
	printl("\t\tBy @ZooL_Smith")
	printl("\n")
	
	DoIncludeScript("migi/commands.nut", null);
	DoIncludeScript("migi/weapons.nut", null);
	DoIncludeScript("migi/includes.nut",null);
	
	roundCheckHandle <- null;
	migi_initNewRoundCheckTimer();
}

::migi_printl <- function(m){printl("[MIGI] "+m);}

::migi_initNewRoundCheckTimer <- function()
{
	timer <- Entities.CreateByClassname("logic_timer");
    timer.__KeyValueFromString("targetname", "migi_newRoundCheckTimer");
    EntFireByHandle(timer, "AddOutput", "RefireTime 0.3", 0, null, null);
    EntFireByHandle(timer, "AddOutput", "classname move_rope", 0, null, null);
    EntFireByHandle(timer, "AddOutput", "OnTimer worldspawn:RunScriptCode:migi_newRoundCheck():0:-1", 0, null, null);
    EntFireByHandle(timer, "Enable", "", 0.1, null, null);   
}

::migi_newRoundCheck <- function()
{
	if(roundCheckHandle && roundCheckHandle.IsValid())
		return;
	
	roundCheckHandle = Entities.CreateByClassname("info_null");
	EntFire("migi.nut_*", "RunScriptCode", "OnNewRound()");
	::migi_player <- Entities.FindByClassname(null, "player")
	migi_printl("New round!");
}

// overwrite so it doesn't crash when ran on sub scripts
::OnNewRound <- function(){} 

::migi_includeScript <- function(script)
{
	try
	{
		DoIncludeScript(script, this);
		migi_printl("Loaded "+script+" on "+this);
	}
	catch(e){}
}

::migi_allocateEntityScope <- function(script)
{
	local ent = Entities.CreateByClassname("info_target");
	local targetname = "migi.nut_"+script.slice(0,script.len()-9);
	ent.__KeyValueFromString("targetname", targetname);
	ent.ValidateScriptScope()
	local scope = ent.GetScriptScope();
	scope.migi_include <- migi_includeScript;
	scope.migi_include(script);	
}

migi_init();
//Entities.First().ConnectOutput("OnUser4", "migi_init");
//DoEntFire("worldspawn", "FireUser4", "", 0, null, null);