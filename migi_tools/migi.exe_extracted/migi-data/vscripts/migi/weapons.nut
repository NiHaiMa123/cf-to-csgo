/*
	███╗   ███╗██╗ ██████╗ ██╗
	████╗ ████║██║██╔════╝ ██║
	██╔████╔██║██║██║  ███╗██║
	██║╚██╔╝██║██║██║   ██║██║
	██║ ╚═╝ ██║██║╚██████╔╝██║
	╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝.nut
		By @ZooL_Smith
*/

// -------------------------------------
// Find Weapons

::migi_getWeaponDataByKV <- function( k, v )
{
	foreach( i in migi_weapons )
	{
		if( !(k in i) ) return null
		if( i[k] == v ) return i
	}
	return null
}

::migi_getWeaponsByAddon <- function( addonName )
{
	local l = []
	foreach( i in migi_weapons )
		if( i.migi_addon == addonName )
			l.append(i)
	return l
}

// -------------------------------------
// Find Values

::migi_getValueFromWeaponData <- function( weaponData, dict, key )
{ 
	local d = null
	if( dict == "" || dict == null || dict == 0 )
		d = weaponData
	else if( dict in weaponData )
		d = weaponData[dict]
	else 
		return null
	
	if( key in d )
		return d[key]
	return null
}

// -------------------------------------
// Weapon array

::migi_weapons <- []

// =============================
//		The big append™
// =============================

