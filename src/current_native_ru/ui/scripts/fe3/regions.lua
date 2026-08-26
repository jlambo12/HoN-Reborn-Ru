----------------------------------------------------------
--	Name:		Regions									--
--  (C) 2025 Juvio, LLC									--
----------------------------------------------------------
local _G = getfenv(0)
local interface = object
local interfaceName = object:GetName()

local ipairs, pairs, select, string, table, next, type, unpack, tinsert, tconcat, tremove, format, tostring, tonumber, tsort, ceil, floor, sub, find, gfind = 
_G.ipairs, _G.pairs, _G.select, _G.string, _G.table, _G.next, _G.type, _G.unpack, _G.table.insert, _G.table.concat, _G.table.remove, _G.string.format, 
_G.tostring, _G.tonumber, _G.table.sort, _G.math.ceil, _G.math.floor, _G.string.sub, _G.string.find, _G.string.gfind

HoN_Region = _G['HoN_Region'] or {}

------------------------------------------------------
--						VARS						--
------------------------------------------------------

HoN_Region.formInfo = [[, 'account_id', GetAccountID(), 'cookie', GetCookie(), 'region', GetRegion()]]
HoN_Region.regionOverride = GetCvarString('ui_overrideRegion', true)
HoN_Region.activeRegion = nil

local function getLangCodes()
	if GetCvarBool('releaseStage_stable') then
		return {'en', 'ru', 'th'}
	else
		return {'en', 'ru', 'th'}
	end
end

HoN_Region.regionTable = {

	-- default International region
	['international'] = {
		['regionCondition'] = ( (Empty(GetRegion()) or GetRegion() == 'int' or GetRegion() == 'en')),	-- If these conditions are met, activate this region
		['langCodes'] = getLangCodes(),	-- Language codes, used to populate language selection and various labels
		['serverCodes'] = { 'US', 'USE', 'USW', 'EU', 'AU', 'BR', 'RU', 'TOUR' },																		-- Server area codes, used in public games
		['tmmRegions'] = { 'usw', 'use', 'eu', 'au', 'br', 'ru' },																									-- Active Matchmaking regions
		['tmmRegionInfo'] = {																													-- Matchmaking regions info
			['usw'] = {FLAG = '/ui/icons/flags/unitedstates.tga', ID = 'USW'},
			['use'] = {FLAG = '/ui/icons/flags/unitedstates.tga', ID = 'USE'},
			['eu'] = {FLAG = '/ui/icons/flags/eu.tga', ID = 'EU'},
			['au'] = {FLAG = '/ui/icons/flags/australia.tga', ID = 'AU', DEFAULT_OFF = true},
			['lat'] = {FLAG = '/ui/icons/flags/lat.tga', ID = 'LAT', DEFAULT_OFF = true},
			['br'] = {FLAG = '/ui/icons/flags/brazil.tga', ID = 'BR', DEFAULT_OFF = true},
			['ru'] = {FLAG = '/ui/icons/flags/russia.tga', ID = 'RU', DEFAULT_OFF = true},
		},
		['cvars'] = {
			{'ui_regionalPartner', 'string', 'Juvio'},											-- Regional partner name
			{'ui_staffIconPath', 'string', '/ui/icons/frostburn.tga'},							-- Staff Icon path
			{'ui_staffStringName', 'string', 'mainlobby_icon_key_chat_staff'},					-- Staff name string
			{'ui_launcherRequiredString', 'string', 'main_label_login_garena'},					-- String displayed if login system disabled for this region and hon is executed
			{'ui_canCreateGame', 'bool', 'true'},												-- Condition for accounts to create a game
			{'ui_promoCornerLeft', 'bool', 'true'},												-- Left corner button (HoN TV)
			{'ui_promoCornerRight', 'bool', 'true'},											-- Right corner button (Mentoring)
			{'ui_promoSpotlight', 'bool', 'true'},												-- Popup spotlights in this region
			{'ui_promoMOTD', 'bool', 'true'},													-- Popup news in this region
			{'ui_disableAccountCreation', 'bool', 'false'},										-- Standard 'slide panel' account creation forms. includes subaccounts, upgrades, gifting, name changes, and stat resets
			{'ui_disableAccountForms', 'bool', 'true'},											-- Standard 'slide panel' account creation forms. includes subaccounts, upgrades, gifting, name changes, and stat resets
			{'cg_altInfoColorScheme', 'int', '2', true},										-- Health bar style default
			{'ui_useRegionalCurrencyName', 'string', 'general_usd'},							-- Unit of currency measurement
			{'ui_useRegionalCurrencyIcon', 'string', ''},										-- Icon for regional currency (eg garena shell)
			{'ui_buyCoinsBlurb', 'string', 'mstore_buycoins_form_blurb'},						-- Explaination of coin purchasing, different in regions using regional currency
			{'ui_buyRegCurBlurb', 'string', ''},												-- Where the player can purchase regional currency (eg garena website - mstore_buycoins_regcur_info_garena)
			{'ui_background', 'int', '2'},														-- Which background to use (0 == none, 1 == ledge, 2 == newest)
			{'ui_showSpecialEventLogo', 'bool', 'false', true},									-- Show the current special event logo (e.g. honniversary)
			{'ui_dev_button', 'bool', 'true'},													-- Does this region have dev options
			{'ui_enableAllHeroes', 'bool', 'true'},
			{'ui_canBuyCoinsForFriend', 'bool', 'false'},										-- Enabled friend option in buy coins form
			{'ui_showCodeRedemption', 'bool', 'true'},											-- Enabled promo code redemption
			{'ui_lobby_showOldAAPicker', 'bool', 'false'},
			{'ui_region_accountCreationType', 'int', '0', true},
			{'ui_support_url', 'string', 'http://www.heroesofnewerth.com/support/'},
			{'ui_hon_url', 'string', 'http://www.heroesofnewerth.com'},
			{'ui_rap_enabled', 'bool', 'true'},
			{'ui_allow_store_tutorial', 'bool', 'true'},
			{'ui_raf_enabled', 'bool', 'false'},
			{'ui_options_referral_url', 'string', '!hon/whitelistfolder/referral_new/referral.php'},
			{'ui_raf_region_string', 'string', 'int'},
			{'ui_stats_eventStats', 'bool', 'true'}, 											-- Should the tournament stats show in the player stats area
			{'ui_regionLogoPath', 'string', '/ui/common/logo_garena.tga'},						-- region logo
		},
		['forms'] = {
			-- ClientLoginResponse error account creation prompt and nickname check (the orange one). These aren't used in international.
			--['createNewAccount'] = [[]], --['checkNickname'] = [[]]
		},
		['loginSytem'] = true,			-- Use the client login system
		['regionalCurrency'] = false,	-- Use regional currency instead of USD (shells, treecash)
		['replaySytem'] = true,			-- Activate replays in the UI
		['guidesEnabled'] = true,		-- Enable/disable entire guides system
		['guideCreation'] = false,
		['guideDetails'] = true,		-- Author and popularity
		['displayCCU'] = true,			-- Display CCU on the system bar
		['displayCCUBreakdown'] = function() return IsStaff() end, -- Display CCU breakdown on the system bar
		['scheduledMatches'] = true,	-- Enable scheduled match system (e.g. HoN Tour)
		['fbsplash'] = false,			-- Use the secondary Frostburn splash screen
		['customAccountIcons'] = true,	-- Enable purchasing custom account icons
		['canBuyCoins'] = true,			-- Enable the buy coins buttons (Disable in test cycles etc)
		['ladder'] = true,				-- Activate Player ladder in the UI
		['emailInactive'] = true, 		-- Whether the Bring Back To HoN Dialog allows them to email or not
		['useGoldCoinButton'] = true,	-- If gold coins can be purchased in-game
		['useGoldCoinWebpage'] = false,	-- If the gold coins window is actually awesomium
		['goldCoinsMessage'] = "region_naeu_buy_coins",		-- the string to display if gold coins can't be purchased in-game.
		['goldCoinsWebpage'] = 'https://www.heroesofnewerth.com/store/gold/',	-- the web address for the gold coins page if one is being used, the cookie and account id is appended to the end
		['goldCoinButtonTemplates'] 		= {'paperform_radiobutton_5_state1', 'paperform_radiobutton_5_state2', 'paperform_radiobutton_5_state3', 'paperform_radiobutton_5_state4', 'paperform_radiobutton_5_state5'},	-- Templates used by the buy coins screen
		['goldCoinButtonTemplateWidths'] 	= {'9.7h', '9.7h', '9.7h', '9.7h', '9.7h'},	-- Widths used by the buy coins screen
		['goldCoinButtonTemplateTooltips']  = {'mstore_tip_package_1', 'mstore_tip_package_2', 'mstore_tip_package_3', 'mstore_tip_package_4', 'mstore_tip_package_5'},	-- Tooltips used by the buy coins screen
		['goldCoinButtonAction'] 	= {'41', '42', '43', '44', '45'},	-- Shopkeeper actions used by the buy coins screen
		['hasEAP'] = false,				-- EAP or Special Avatars in Early Access, mostly just string changes
		['hasHolidayNotification'] = true,
		['questSystem']		= false,
		['playerTourURL'] = '!ascension/html/index.html',
		['playerTourStatsURL'] = '!ascension/?r=season/stats',
		['playerTourMatchURL'] = '!ascension/?r=season/matchList',
		['playerTourNewsURL'] = '!ascension/?r=news/index',
		['playerTourLevelURL'] = '!ascension/?r=master/index',
		['playerTourTreasureURL'] = '!ascension/html/treasure.html',
		['playerTourProgressURL'] = '!ascension/?r=master/crossfunding',
		['playerLadderURL'] = 'http://naeu-icb2.s3.amazonaws.com/web/Player-Ladder/index.html',
		['questLadderURL'] = 'http://naeu-icb2.s3.amazonaws.com/web/Quest-Ladder/index.html',
		['codexLevelLadderURL'] = '',
		-- ['strikerLadderURL'] = '!ascension/?r=site/soccerladder',
		['masteryLadderAllURL'] = '!ascension/?r=site/masteryallladder', 
		['masteryLadderFriendsURL'] = '!ascension/?r=site/masteryfriendsladder', 
		['hasDice'] = false,		-- Rift wars
		['hasTokens'] = false,
		['hasPasses'] = false,
		['tmmAllowLeavers'] = false,
		['motdURL'] = {			-- Prefix for motd
			sbt		= 'http://fun.sbt.naeu.heroesofnewerth.com/events/common/client/motd/index.php',
			rct		= 'http://fun.rct.naeu.heroesofnewerth.com/events/common/client/motd/index.php',
			retail	= 'http://fun.naeu.heroesofnewerth.com/events/common/client/motd/index.php',
		},
		['tos_paths'] = {
			en		= 'tos',
			es		= 'tos_es',
			br		= 'tos_br',
		},
		['globalMessaging'] = true,
		['refereeControlPage'] = '!ascension/?r=match/bindpage',
		['gcaControlPage'] = 'http://www.hon.in.th/events/common/client/gca/benefit.php',
	},
	-- development region
	['internal_dev'] = {
		['regionCondition'] = ((GetCvarString('build_branch') == 'dev')),	-- If these conditions are met, activate this region
		['langCodes'] = getLangCodes(),	-- Language codes, used to populate language selection and various labels
		['serverCodes'] = { 'US', 'USE', 'USW', 'EU', 'AU', 'BR', 'RU', 'TOUR' }, -- Server area codes, used in public games
		['tmmRegions'] = { 'usw', 'use', 'eu', 'au', 'br', 'ru' },-- Active Matchmaking regions
		['tmmRegionInfo'] = { -- Matchmaking regions info
			['usw'] = {FLAG = '/ui/icons/flags/unitedstates.tga', ID = 'USW'},
			['use'] = {FLAG = '/ui/icons/flags/unitedstates.tga', ID = 'USE'},
			['eu'] = {FLAG = '/ui/icons/flags/eu.tga', ID = 'EU'},
			['au'] = {FLAG = '/ui/icons/flags/australia.tga', ID = 'AU', DEFAULT_OFF = true},
			['lat'] = {FLAG = '/ui/icons/flags/lat.tga', ID = 'LAT', DEFAULT_OFF = true},
			['br'] = {FLAG = '/ui/icons/flags/brazil.tga', ID = 'BR', DEFAULT_OFF = true},
			['ru'] = {FLAG = '/ui/icons/flags/russia.tga', ID = 'RU', DEFAULT_OFF = true},
		},
		['cvars'] = {
			{'ui_regionalPartner', 'string', 'Juvio'},											-- Regional partner name
			{'ui_staffIconPath', 'string', '/ui/icons/frostburn.tga'},							-- Staff Icon path
			{'ui_staffStringName', 'string', 'mainlobby_icon_key_chat_staff'},					-- Staff name string
			{'ui_launcherRequiredString', 'string', 'main_label_login_garena'},					-- String displayed if login system disabled for this region and hon is executed
			{'ui_canCreateGame', 'bool', 'true'},												-- Condition for accounts to create a game
			{'ui_promoCornerLeft', 'bool', 'true'},												-- Left corner button (HoN TV)
			{'ui_promoCornerRight', 'bool', 'true'},											-- Right corner button (Mentoring)
			{'ui_promoSpotlight', 'bool', 'true'},												-- Popup spotlights in this region
			{'ui_promoMOTD', 'bool', 'true'},													-- Popup news in this region
			{'ui_disableAccountCreation', 'bool', 'false'},										-- Standard 'slide panel' account creation forms. includes subaccounts, upgrades, gifting, name changes, and stat resets
			{'ui_disableAccountForms', 'bool', 'true'},											-- Standard 'slide panel' account creation forms. includes subaccounts, upgrades, gifting, name changes, and stat resets
			{'cg_altInfoColorScheme', 'int', '2', true},										-- Health bar style default
			{'ui_useRegionalCurrencyName', 'string', 'general_usd'},							-- Unit of currency measurement
			{'ui_useRegionalCurrencyIcon', 'string', ''},										-- Icon for regional currency (eg garena shell)
			{'ui_buyCoinsBlurb', 'string', 'mstore_buycoins_form_blurb'},						-- Explaination of coin purchasing, different in regions using regional currency
			{'ui_buyRegCurBlurb', 'string', ''},												-- Where the player can purchase regional currency (eg garena website - mstore_buycoins_regcur_info_garena)
			{'ui_background', 'int', '2'},														-- Which background to use (0 == none, 1 == ledge, 2 == newest)
			{'ui_showSpecialEventLogo', 'bool', 'false', true},									-- Show the current special event logo (e.g. honniversary)
			{'ui_showMalikenMessage', 'bool', 'false', true},									-- Show the current message from maliken
			{'ui_malikenMessagePath', 'string', '/ui/fe2/elements/hon_message_scroll.tga'},			-- Maliken message texture path
			{'ui_malikenMessageString', 'string', 'maliken_says'},								-- Maliken message string
			{'ui_dev_button', 'bool', 'true'},													-- Does this region have dev options
			{'ui_enableAllHeroes', 'bool', 'true'},
			{'ui_canBuyCoinsForFriend', 'bool', 'false'},										-- Enabled friend option in buy coins form
			{'ui_showCodeRedemption', 'bool', 'true'},											-- Enabled promo code redemption
			{'ui_lobby_showOldAAPicker', 'bool', 'false'},
			{'ui_region_accountCreationType', 'int', '0', true},
			{'ui_support_url', 'string', 'http://www.heroesofnewerth.com/support/'},
			{'ui_hon_url', 'string', 'http://www.heroesofnewerth.com'},
			{'ui_rap_enabled', 'bool', 'true'},
			{'ui_allow_store_tutorial', 'bool', 'true'},
			{'ui_raf_enabled', 'bool', 'false'},
			{'ui_options_referral_url', 'string', '!hon/whitelistfolder/referral_new/referral.php'},
			{'ui_raf_region_string', 'string', 'int'},
			{'ui_stats_eventStats', 'bool', 'true'}, 											-- Should the tournament stats show in the player stats area
			{'ui_regionLogoPath', 'string', '/ui/common/logo_garena.tga'},						-- region logo
		},
		['forms'] = {
			-- ClientLoginResponse error account creation prompt and nickname check (the orange one). These aren't used in international.
			--['createNewAccount'] = [[]], --['checkNickname'] = [[]]
		},
		['loginSytem'] = true,			-- Use the client login system
		['regionalCurrency'] = false,	-- Use regional currency instead of USD (shells, treecash)
		['replaySytem'] = true,			-- Activate replays in the UI
		['guidesEnabled'] = true,		-- Enable/disable entire guides system
		['guideCreation'] = false,
		['guideDetails'] = true,		-- Author and popularity
		['displayCCU'] = true,			-- Display CCU on the system bar
		['displayCCUBreakdown'] = function() return IsStaff() end, -- Display CCU breakdown on the system bar
		['scheduledMatches'] = true,	-- Enable scheduled match system (e.g. HoN Tour)
		['fbsplash'] = false,			-- Use the secondary Frostburn splash screen
		['customAccountIcons'] = true,	-- Enable purchasing custom account icons
		['canBuyCoins'] = true,			-- Enable the buy coins buttons (Disable in test cycles etc)
		['ladder'] = true,				-- Activate Player ladder in the UI
		['emailInactive'] = true, 		-- Whether the Bring Back To HoN Dialog allows them to email or not
		['useGoldCoinButton'] = true,	-- If gold coins can be purchased in-game
		['useGoldCoinWebpage'] = false,	-- If the gold coins window is actually awesomium
		['goldCoinsMessage'] = "region_naeu_buy_coins",		-- the string to display if gold coins can't be purchased in-game.
		['goldCoinsWebpage'] = 'https://www.heroesofnewerth.com/store/gold/',	-- the web address for the gold coins page if one is being used, the cookie and account id is appended to the end
		['goldCoinButtonTemplates'] 		= {'paperform_radiobutton_5_state1', 'paperform_radiobutton_5_state2', 'paperform_radiobutton_5_state3', 'paperform_radiobutton_5_state4', 'paperform_radiobutton_5_state5'},	-- Templates used by the buy coins screen
		['goldCoinButtonTemplateWidths'] 	= {'9.7h', '9.7h', '9.7h', '9.7h', '9.7h'},	-- Widths used by the buy coins screen
		['goldCoinButtonTemplateTooltips']  = {'mstore_tip_package_1', 'mstore_tip_package_2', 'mstore_tip_package_3', 'mstore_tip_package_4', 'mstore_tip_package_5'},	-- Tooltips used by the buy coins screen
		['goldCoinButtonAction'] 	= {'41', '42', '43', '44', '45'},	-- Shopkeeper actions used by the buy coins screen
		['hasEAP'] = false,				-- EAP or Special Avatars in Early Access, mostly just string changes
		['hasHolidayNotification'] = true,
		['questSystem']		= false,
		['playerTourURL'] = '!ascension/html/index.html',
		['playerTourStatsURL'] = '!ascension/?r=season/stats',
		['playerTourMatchURL'] = '!ascension/?r=season/matchList',
		['playerTourNewsURL'] = '!ascension/?r=news/index',
		['playerTourLevelURL'] = '!ascension/?r=master/index',
		['playerTourTreasureURL'] = '!ascension/html/treasure.html',
		['playerTourProgressURL'] = '!ascension/?r=master/crossfunding',
		['playerLadderURL'] = 'http://naeu-icb2.s3.amazonaws.com/web/Player-Ladder/index.html',
		['questLadderURL'] = 'http://naeu-icb2.s3.amazonaws.com/web/Quest-Ladder/index.html',
		['codexLevelLadderURL'] = '',
		-- ['strikerLadderURL'] = '!ascension/?r=site/soccerladder',
		['masteryLadderAllURL'] = '!ascension/?r=site/masteryallladder', 
		['masteryLadderFriendsURL'] = '!ascension/?r=site/masteryfriendsladder', 
		['hasDice'] = false,		-- Rift wars
		['hasTokens'] = false,
		['hasPasses'] = false,
		['tmmAllowLeavers'] = false,
		['motdURL'] = {			-- Prefix for motd
			sbt		= 'http://fun.sbt.naeu.heroesofnewerth.com/events/common/client/motd/index.php',
			rct		= 'http://fun.rct.naeu.heroesofnewerth.com/events/common/client/motd/index.php',
			retail	= 'http://fun.naeu.heroesofnewerth.com/events/common/client/motd/index.php',
		},
		['tos_paths'] = {
			en		= 'tos',
			es		= 'tos_es',
			br		= 'tos_br',
		},
		['globalMessaging'] = true,
		['refereeControlPage'] = '!ascension/?r=match/bindpage',
		['gcaControlPage'] = 'http://www.hon.in.th/events/common/client/gca/benefit.php',
	},

}

------------------------------------------------------
--						CODE						--
------------------------------------------------------

local function RegionalCurrencySystem(isEnabled)
	if (isEnabled) then
		Cvar.CreateCvar('ui_useRegionalCurrency', 'bool', 'true')
		Main:GetWidget('store_form_buycoins_regional_currency_display'):SetVisible(true)
		Main:GetWidget('store_form_buycoins_regcur_submit'):SetVisible(true)
		Main:GetWidget('store_form_buycoins_regcur_shellinfo'):SetVisible(true)

		Main:GetWidget('store_form_buycoins_normal_submit'):SetVisible(false)
		Main:GetWidget('store_form_buycoins_paypal_label'):SetVisible(false)
		Main:GetWidget('store_form_buycoins_cc_input'):SetVisible(false)
	else
		Cvar.CreateCvar('ui_useRegionalCurrency', 'bool', 'false')
		Main:GetWidget('store_form_buycoins_regional_currency_display'):SetVisible(false)
		Main:GetWidget('store_form_buycoins_regcur_submit'):SetVisible(false)
		Main:GetWidget('store_form_buycoins_regcur_shellinfo'):SetVisible(false)

		Main:GetWidget('store_form_buycoins_normal_submit'):SetVisible(true)
		Main:GetWidget('store_form_buycoins_paypal_label'):SetVisible(true)
		Main:GetWidget('store_form_buycoins_cc_input'):SetVisible(true)
	end

	Main:GetWidget('store_form_buycoins_blurb_label'):SetText(Translate(GetCvarString('ui_buyCoinsBlurb')))
	Main:GetWidget('store_form_buy_regcur_info'):SetText(Translate(GetCvarString('ui_buyRegCurBlurb')))
end

local function LoginSystem(isEnabled)
	if (isEnabled) then
		Cvar.CreateCvar('ui_useClientLoginSystem', 'bool', 'true')
		Main:GetWidget('sysbar_center_langpicker'):SetVisible(false)
		Main:GetWidget('sysbar_center_account_info'):SetVisible(true)
		Main:GetWidget('prelogin_options_panel_login'):SetVisible(true)
		Main:GetWidget('prelogin_options_panel_nologin'):SetVisible(false)
		Main:GetWidget('main_logging_in_warn'):SetVisible(false)
		Main:GetWidget('main_logging_in'):SetVisible(true)
		Main:GetWidget('prelogin_loginbox_disabled_nologin'):FadeOut(50)
		Main:GetWidget('prelogin_loginbox_disabled_login'):SetVisible(true)
	else
		Cvar.CreateCvar('ui_useClientLoginSystem', 'bool', 'false')
		Main:GetWidget('sysbar_center_langpicker'):SetVisible(true)
		Main:GetWidget('sysbar_center_account_info'):SetVisible(true)
		Main:GetWidget('prelogin_options_panel_login'):SetVisible(false)
		Main:GetWidget('prelogin_options_panel_nologin'):SetVisible(true)
		Main:GetWidget('main_logging_in_warn'):SetVisible(true)
		Main:GetWidget('main_status_label'):SetText(Translate(GetCvarString('ui_launcherRequiredString')))
		if GetCvarBool('ui_dev') and (GetCvarBool('releaseStage_dev') or GetCvarBool('releaseStage_test')) then
			Main:GetWidget('main_login_launcher_skip'):SetVisible(true)
		end
		Main:GetWidget('prelogin_loginbox_disabled_nologin'):SetVisible(true)
		Main:GetWidget('prelogin_loginbox_disabled_login'):SetVisible(false)
	end
end

local function ReplaySytem(isEnabled)
	Main:GetWidget('match_replays_download_replay_btn'):SetVisible(isEnabled)
	Main:GetWidget('sysbar_replays_button'):SetVisible(isEnabled)
end

local function GuidesSystem(isEnabled, canCreate, showDetails)
	Main:GetWidget('compendium_guides_cover'):SetVisible(not isEnabled)
	Main:GetWidget('compendium_guide_vote_thumbs_up_button'):SetVisible(showDetails)
	Main:GetWidget('compendium_guide_vote_thumbs_down_button'):SetVisible(showDetails)
	Main:GetWidget('learnatorium_guidePopularity'):SetVisible(showDetails)
	Main:GetWidget('learnatorium_guideCreation'):SetVisible(canCreate)
end

local function CanBuyCoins(isEnabled)
	local wdgBuyCoin = GetCvarBool('cg_store2_') and Main:GetWidget('store2_store_common_elements_button_buy_coin') or Main:GetWidget('mstore_front_buycoins_btn')
	if (wdgBuyCoin) then
		if (isEnabled) then
			--println('CanBuyCoins: Enabled')
			Main:GetWidget('sysbar_coins_gold'):UICmd([[SetOnClick('CallEvent(\'store_open_purchase_helper\', 2);')]])
			wdgBuyCoin:UICmd([[SetWatch('MicroStoreProcessing')]])
			wdgBuyCoin:SetEnabled(true)
			Main:GetWidget('mstore_purchase_coins_submit_btn'):UICmd([[SetWatch('MicroStoreProcessing')]])
			Main:GetWidget('mstore_purchase_coins_submit_btn'):UICmd([[SetWatch(1, 'UpdatePurchaseCoinsForm')]])
			Main:GetWidget('mstore_purchase_coins_submit_btn'):SetEnabled(true)
			Main:GetWidget('mstore_buycoins_form_blocker'):SetVisible(false)
		else
			--println('CanBuyCoins: Disabled')
			Main:GetWidget('sysbar_coins_gold'):UICmd([[SetOnClick('')]])
			wdgBuyCoin:UICmd([[SetWatch('')]])
			wdgBuyCoin:SetEnabled(false)
			Main:GetWidget('mstore_purchase_coins_submit_btn'):UICmd([[SetWatch('')]])
			Main:GetWidget('mstore_purchase_coins_submit_btn'):UICmd([[SetWatch(1, '')]])
			Main:GetWidget('mstore_purchase_coins_submit_btn'):SetEnabled(false)
			Main:GetWidget('mstore_buycoins_form_blocker'):SetVisible(true)
		end
	end
end

local function CustomAccountIcons(isEnabled)
	if (isEnabled) then
		Cvar.CreateCvar('ui_enableCustomAccIcons', 'bool', 'true')
	else
		Cvar.CreateCvar('ui_enableCustomAccIcons', 'bool', 'false')
	end
end

local function UpdateRegionCvars()
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) and (HoN_Region.regionTable[HoN_Region.activeRegion].cvars) then
		for index, cvarTable in pairs((HoN_Region.regionTable[HoN_Region.activeRegion].cvars)) do
			if (type(cvarTable[3]) == 'function') then
				--Cvar.CreateCvar(cvarTable[1], cvarTable[2], tostring(cvarTable[3]()) )
				Set(cvarTable[1], tostring(cvarTable[3]()), cvarTable[2], cvarTable[4])
			else
				--Cvar.CreateCvar(cvarTable[1], cvarTable[2], tostring(cvarTable[3]))
				Set(cvarTable[1],  tostring(cvarTable[3]), cvarTable[2], cvarTable[4])
				-- ( name				value				  type		  nooverwrite
			end
		end
	end
end

local function LoginStatus(self, accountStatus, statusDescription, isLoggedIn, pwordExpired, isLoggedInChanged, updaterStatus)
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) then
		if AtoB(isLoggedIn) then
			UpdateRegionCvars()
			if (HonTour) and (HonTour.Initialize) then
				HonTour.isMatchScheduled = HonTour.isMatchScheduled or false
				HonTour.Initialize(HoN_Region.regionTable[HoN_Region.activeRegion].scheduledMatches)
			end
		else
			if (HonTour) and (HonTour.Initialize) then
				HonTour.isMatchScheduled = false
			end
		end
		if (Main:GetWidget('midbar_button_ladder', nil, true)) then
			if (HoN_Region.regionTable[HoN_Region.activeRegion].ladder) then
				Main:GetWidget('midbar_button_ladder'):SetEnabled(true)
				Main:GetWidget('playerLadderTabCodexLevelParent'):SetVisible(HoN_Region:GetCodexLevelLadder() ~= '')
			else
				Main:GetWidget('midbar_button_ladder'):SetEnabled(false)
			end
		end
	end
end

local function ActivateRegionPostLoad(_, region)

	Trigger('UIUpdateRegions')

	--Main:GetWidget('systembar'):RegisterWatch('LoginStatus', LoginStatus)
	--LoginSystem(HoN_Region.regionTable[region].loginSytem)
	--ReplaySytem(HoN_Region.regionTable[region].replaySytem)
	--GuidesSystem(HoN_Region.regionTable[region].guidesEnabled, HoN_Region.regionTable[region].guideCreation, HoN_Region.regionTable[region].guideDetails)
	--CanBuyCoins(HoN_Region.regionTable[region].canBuyCoins)
	--CustomAccountIcons(HoN_Region.regionTable[region].customAccountIcons)
	--RegionalCurrencySystem(HoN_Region.regionTable[region].regionalCurrency)

	--Trigger('UIUpdateRegion')

	--interface:HoNMainF('UICheckForErrors')
	--if (Main:GetWidget('midbar_button_ladder', nil, true)) then
	--	if (HoN_Region.regionTable[HoN_Region.activeRegion].ladder) then
	--		Main:GetWidget('midbar_button_ladder'):SetEnabled(true)
	--	else
	--		Main:GetWidget('midbar_button_ladder'):SetEnabled(false)
	--	end
	--end
	
	--Main.InitMain(HoN_Region.regionTable[region].loginSytem)
end

local function ActivateRegion(_, region)

	println('^cUI: Region is ' .. tostring(region))

	if (HoN_Region.regionTable) and (HoN_Region.regionTable[region]) then

		if GetCvarBool('_loggedin') then
			interface:UICmd("LogOut()")
		end

		HoN_Region.activeRegion = region
		Cvar.CreateCvar('ui_useClientLoginSystem', 'bool', tostring(HoN_Region.regionTable[region].loginSytem))
		SetActiveRegion(region)
		UpdateRegionCvars()
		
		if (HoN_Region.regionTable[region].fbsplash) then
			Main:GetWidget('fe3_sleeper'):Sleep(1,
				function()
					Main:GetWidget('main_login_logo_splash_image'):SetTexture(GetCvarString('ui_regionLogoPath'))
					if (HoN_Region.regionTable[region].koreaRatings) then
						Main:GetWidget('main_login_logo_splash_image_2'):SetTexture('/ui/icons/korea_rating_1.tga')
						Main:GetWidget('main_login_logo_splash_image_3'):SetTexture('/ui/icons/korea_rating_3.tga')
					end
					--Main:GetWidget('main_login_logo_splash'):SetVisible(1)  -- I commented this out (Xewl)
					Main:GetWidget('fe3_sleeper'):Sleep(2800,
						function()
							--Main:GetWidget('main_login_logo_splash'):FadeOut(50)  -- I commented this out (Xewl)
							ActivateRegionPostLoad(_, region)
						end
					)
				end
			)
		else
			Main:GetWidget('fe3_sleeper'):Sleep(1,
				function()
					--Main:GetWidget('main_login_logo_splash'):SetVisible(0) -- I commented this out (Xewl)
					ActivateRegionPostLoad(_, region)
				end
			)
		end
		
	end
end

local function UIFindRegion()
	if (HoN_Region.regionOverride) and NotEmpty(HoN_Region.regionOverride) then

		ActivateRegion(nil, HoN_Region.regionOverride)

	elseif (HoN_Region.regionTable) then

		local useDefault = true

		for region, regionTable in pairs(HoN_Region.regionTable) do
			if (regionTable) and (regionTable.regionCondition) then
				useDefault = false
				ActivateRegion(nil, region)
				break
			end
		end

		if (useDefault) then
			ActivateRegion(nil, 'international')
			interface:Sleep(1, function() interface:HoNMainF('UICriticalError', 'UIFindRegion Failed', 2) end)
		end

	else
		interface:Sleep(1, function() interface:HoNMainF('UICriticalError', 'Region Table Failed To Load', 1) end)
	end

	UIFindRegion = nil

end

local function ClientLoginResponse(sourceWidget, param0, param1)
	println('^o ClientLoginResponse: ' .. param0)
end

function HoN_Region:OpenGoldCoinsWebpage()
	-- append the cookie to the URL
	local url = HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinsWebpage
	url = url..'?ingame=true&cookie='..Client.GetCookie()..'&accountid='..Client.GetAccountID()

	UIManager.GetInterface('webpanel'):HoNWebPanelF('LoadURLWithThrob', url, Main:GetWidget("storePopupBuyCoinsForm_web"))
end

function HoN_Region:PopulatePointPackageButtons(widget)
	Echo('HoN_Region:PopulatePointPackageButtons HoN_Region.activeRegion: '..tostring(HoN_Region.activeRegion))
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) then
		if (HoN_Region.regionTable[HoN_Region.activeRegion].useGoldCoinButton) and (HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates) and (widget) then
			Main:GetWidget("storePopupBuyCoinsForm_cover"):SetVisible(0)

			if (HoN_Region.regionTable[HoN_Region.activeRegion].useGoldCoinWebpage) then
				Main:GetWidget("storePopupBuyCoinsForm_main"):SetVisible(0)
				Main:GetWidget("storePopupBuyCoinsForm_web"):SetVisible(1)
			else
				Main:GetWidget("storePopupBuyCoinsForm_main"):SetVisible(1)
				Main:GetWidget("storePopupBuyCoinsForm_web"):SetVisible(0)

				if (HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[1]) then
					widget:Instantiate('form_radiobutton',
						'group', 'store_buycoins_radiobuttons_group',
						'tip_id', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateTooltips[1]),
						'updatetrigger', 'UpdatePurchaseCoinsForm',
						'cvar', '_microStore_buyCoins_package',
						'value', '1',
						'color', 'white',
						'displaytemplate', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[1]),
						'height', '100%',
						'width', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateWidths[1]),
						'onclick', 'Trigger(\'ShopkeeperAction\', ' .. tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonAction[1]) .. ');',
						'radiobutton_name', 'microStorePackageButton1'
					)
				end
				if (HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[2]) then
					widget:Instantiate('form_radiobutton',
						'group', 'store_buycoins_radiobuttons_group',
						'tip_id', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateTooltips[2]),
						'updatetrigger', 'UpdatePurchaseCoinsForm',
						'cvar', '_microStore_buyCoins_package',
						'value', '2',
						'color', 'white',
						'displaytemplate', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[2]),
						'height', '100%',
						'width', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateWidths[2]),
						'onclick', 'Trigger(\'ShopkeeperAction\', ' .. tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonAction[2]) .. ');',
						'radiobutton_name', 'microStorePackageButton2'
					)
				end
				if (HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[3]) then
					widget:Instantiate('form_radiobutton',
						'group', 'store_buycoins_radiobuttons_group',
						'tip_id', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateTooltips[3]),
						'updatetrigger', 'UpdatePurchaseCoinsForm',
						'cvar', '_microStore_buyCoins_package',
						'value', '3',
						'color', 'white',
						'displaytemplate', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[3]),
						'height', '100%',
						'width', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateWidths[3]),
						'onclick', 'Trigger(\'ShopkeeperAction\', ' .. tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonAction[3]) .. ');',
						'radiobutton_name', 'microStorePackageButton3'
					)
				end
				if (HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[4]) then
					widget:Instantiate('form_radiobutton',
						'group', 'store_buycoins_radiobuttons_group',
						'tip_id', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateTooltips[4]),
						'updatetrigger', 'UpdatePurchaseCoinsForm',
						'cvar', '_microStore_buyCoins_package',
						'value', '4',
						'color', 'white',
						'displaytemplate', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[4]),
						'height', '100%',
						'width', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateWidths[4]),
						'onclick', 'Trigger(\'ShopkeeperAction\', ' .. tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonAction[4]) .. ');',
						'radiobutton_name', 'microStorePackageButton4'
					)
				end
				if (HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[5]) then
					widget:Instantiate('form_radiobutton',
						'group', 'store_buycoins_radiobuttons_group',
						'tip_id', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateTooltips[5]),
						'updatetrigger', 'UpdatePurchaseCoinsForm',
						'cvar', '_microStore_buyCoins_package',
						'value', '5',
						'color', 'white',
						'displaytemplate', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplates[5]),
						'height', '100%',
						'width', tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonTemplateWidths[5]),
						'onclick', 'Trigger(\'ShopkeeperAction\', ' .. tostring(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinButtonAction[5]) .. ');',
						'radiobutton_name', 'microStorePackageButton5'
					)
				end
				widget:Instantiate('form_radiobutton',
					'visible', '0',
					'group', 'store_buycoins_radiobuttons_group',
					'tip_id', 'mstore_tip_package_1',
					'updatetrigger', 'UpdatePurchaseCoinsForm',
					'cvar', '_microStore_buyCoins_package',
					'value', '0',
					'color', 'white',
					'displaytemplate', 'paperform_radiobutton_state1',
					'height', '0',
					'width', '0',
					'onclick', '',
					'radiobutton_name', 'microStorePackageButton0'
				)
			end
		elseif (not HoN_Region.regionTable[HoN_Region.activeRegion].useGoldCoinButton) then
			Main:GetWidget("storePopupBuyCoinsForm_main"):SetVisible(0)
			Main:GetWidget("storePopupBuyCoinsForm_web"):SetVisible(0)
			Main:GetWidget("storePopupBuyCoinsForm_cover"):SetVisible(1)

			if (HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinsMessage) then
				Main:GetWidget("storePopupBuyCoinsForm_cover_text"):SetText(Translate(HoN_Region.regionTable[HoN_Region.activeRegion].goldCoinsMessage))
			end
		end
	end
end

function HoN_Region:PopulatePublicGameStaff(widget)
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) and (HoN_Region.regionTable[HoN_Region.activeRegion].cvars) and (widget) then
		groupcall('icon_staff_keys', 'DoEvent(7)')
		widget:Instantiate('icon_key_item', 'image', GetCvarString('ui_staffIconPath'), 'label', Translate(GetCvarString('ui_staffStringName')), 'group', 'icon_staff_keys')
	end
end

function HoN_Region:PopulatePublicGameRegion(widget)
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) and (widget) then
		widget:ClearItems()
		widget:AddTemplateListItem('Ncombobox_item', '', 'label', 'main_lobby_filter_any')
		for index, serverCode in pairs(HoN_Region.regionTable[HoN_Region.activeRegion].serverCodes) do
			widget:AddTemplateListItem('Ncombobox_item', serverCode, 'label', 'mainlobby_label_custom_game_'..serverCode)
		end
	end
end

function HoN_Region:GetLadderRegionInfo()
	if (HoN_Region.activeRegion) then
		return HoN_Region.activeRegion, HoN_Region.regionTable[HoN_Region.activeRegion].ladder
	end
end

function HoN_Region:GetEmailInactiveRegionInfo()
	if (HoN_Region.activeRegion) then
		return HoN_Region.activeRegion, HoN_Region.regionTable[HoN_Region.activeRegion].emailInactive
	end
end

function HoN_Region:GetMatchmakingRegionInfo()
	if (HoN_Region.activeRegion) then
		return HoN_Region.activeRegion, HoN_Region.regionTable[HoN_Region.activeRegion].tmmRegions, HoN_Region.regionTable[HoN_Region.activeRegion].tmmRegionInfo
	end
end

function HoN_Region:GetHasEAP()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].hasEAP
	else
		-- default to having EAP, as most regions will have it
		return true
	end
end

function HoN_Region:GetPlayerTour()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].playerTourURL
	else
		return ""
	end
end

function HoN_Region:GetPlayerTourStats()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].playerTourStatsURL
	else
		return ""
	end
end

function HoN_Region:GetPlayerTourLevel()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].playerTourLevelURL
	else
		return ""
	end
end

function HoN_Region:GetPlayerTourMatch()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].playerTourMatchURL
	else
		return ""
	end
end

function HoN_Region:GetPlayerTourNews()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].playerTourNewsURL
	else
		return ""
	end
end

function HoN_Region:GetPlayerTourProgress()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].playerTourProgressURL
	else
		return ""
	end
end

function HoN_Region:GetPlayerTourTreasure()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].playerTourTreasureURL
	else
		return ""
	end
end

function HoN_Region:GetPlayerLadder()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].playerLadderURL..'#?lang='..GetCvarString('host_locale')
	else
		return ""
	end
end

function HoN_Region:GetGCAControlPage()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].gcaControlPage
	else
		return ""
	end
end

function HoN_Region:GetRefereeControlPage()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].refereeControlPage
	else
		return ""
	end
end

function HoN_Region:GetQuestLadder()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].questLadderURL..'#?lang='..GetCvarString('host_locale')
	else
		return ""
	end
end

function HoN_Region:GetCodexLevelLadder()
	if (HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].codexLevelLadderURL
	else
		return ""
	end
end

function HoN_Region:GetMasteryAllLadder()
	if(HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].masteryLadderAllURL
	else
		return ""
	end
end

function HoN_Region:GetMasteryFriendsLadder()
	if(HoN_Region.activeRegion) then
		return HoN_Region.regionTable[HoN_Region.activeRegion].masteryLadderFriendsURL
	else
		return ""
	end
end

function HoN_Region:PopulateCustomGameRegion(widget)
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) and (widget) then
		widget:ClearItems()
		widget:AddTemplateListItem('Ncombobox_item', '', 'label', 'main_lobby_filter_any')
		for index, serverCode in pairs(HoN_Region.regionTable[HoN_Region.activeRegion].serverCodes) do
			widget:AddTemplateListItem('Ncombobox_item', serverCode, 'label', 'mainlobby_label_custom_game_'..serverCode)
		end
	end
end

function HoN_Region:PopulateLanguageSelector(widget)
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) and (widget) then

		--local prevLang = widget:UICmd("GetSelectedItemName()")
		--if Empty(prevLang) then prevLang = GetCvarString('host_locale') end

		local targetLang = GetCvarString('host_locale')

		widget:ClearItems()

		for index, langCode in pairs(HoN_Region.regionTable[HoN_Region.activeRegion].langCodes) do
			widget:AddTemplateListItem('sysbar_combobox_lang_item', langCode, 'code', langCode, 'texture', '/ui/fe2/elements/flag_'..langCode..'.tga', 'label', 'lang_'..langCode)
		end

		--println(targetLang)
		
		widget:Sleep(500, widget:UICmd("SetSelectedItemByValue('"..targetLang.."', false)"))
	end
end

function HoN_Region:PopulateRegionSelector(widget)
	if (HoN_Region.regionTable) and (widget) then
		widget:ClearItems()
		for index, regionCode in pairs(HoN_Region.regionTable) do
			widget:AddTemplateListItem('sysbar_combobox_lang_item', index, 'label', index)
		end
		widget:Sleep(500, widget:UICmd("SetSelectedItemByValue('"..HoN_Region.activeRegion.."', false)"))
	end
end

function HoN_Region:ChangeLanguage(value)
	SetHostLocale(tostring(value))
	Main:ShowLanguageChangeRestartDialog()
end

function HoN_Region:CreateAccount(widget)
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) and (HoN_Region.regionTable[HoN_Region.activeRegion].forms) and (HoN_Region.regionTable[HoN_Region.activeRegion].forms.createNewAccount) then
		println('^g Submit Form')
		println(HoN_Region.regionTable[HoN_Region.activeRegion].forms.createNewAccount)
		interface:UICmd(HoN_Region.regionTable[HoN_Region.activeRegion].forms.createNewAccount)
	else
		println('^r Error: No form exists for this region')
	end
end

function HoN_Region:CheckNickname(widget)
	if (HoN_Region.regionTable) and (HoN_Region.regionTable[HoN_Region.activeRegion]) and (HoN_Region.regionTable[HoN_Region.activeRegion].forms) and (HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname) then
		if type(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname) == 'string' then
			interface:UICmd(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname)
		elseif type(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname) == 'table'	then
			SetFormHost(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[2], HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[3])
			if type(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[5]) == 'string' then
				SetFormTarget(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[2], (HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[4] .. interface:UICmd(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[5]) ))
			elseif type(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[5]) == 'function' then
				SetFormTarget(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[2], (HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[4] .. HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[5]() ))
			end
			interface:UICmd(HoN_Region.regionTable[HoN_Region.activeRegion].forms.checkNickname[1])
		end
	end
end

function HoN_Region:HoNRegionF(func, ...)
	if (HoN_Region[func]) then
		print(HoN_Region[func](self, ...))
	else
		print('HoNRegionF failed to find: ' .. tostring(func) .. '\n')
	end
end

------------------------------------------------------
--						INIT						--
------------------------------------------------------

local function SetupRegisters()
	interface:RegisterWatch('ClientLoginResponse', ClientLoginResponse)
	interface:RegisterWatch('GarenaClientLoginResponse', ClientLoginResponse)
	interface:RegisterWatch('SetActiveRegion', ActivateRegion)
end

function HoN_Region:Init()
	SetupRegisters()
	UIFindRegion()
end