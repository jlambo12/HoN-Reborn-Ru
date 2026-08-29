----------------------------------------------------------
--	Name: 		Store Featured FE3						--
--  (C) 2025 Juvio, LLC									--
----------------------------------------------------------

local _G = getfenv(0)
local ipairs, pairs, select, string, table, next, type, unpack, tinsert, tconcat, tremove, format, tostring, tonumber, tsort, ceil, floor, sub, find, gfind =
_G.ipairs, _G.pairs, _G.select, _G.string, _G.table, _G.next, _G.type, _G.unpack, _G.table.insert, _G.table.concat, _G.table.remove, _G.string.format,
_G.tostring, _G.tonumber, _G.table.sort, _G.math.ceil, _G.math.floor, _G.string.sub, _G.string.find, _G.string.gfind
local interface, interfaceName = object, object:GetName()

StoreFeatured = _G['StoreFeatured'] or {}

----------------------------------------------
--					Vars					--
----------------------------------------------

---- WIDGETS ----
local widgets =
{
	bannerRoot	= WExt:InitWidget('store_featured_banner_root', StoreFeatured),
	bannerImage = WExt:InitWidget('store_featured_banner_image', StoreFeatured),
	bannerTitle = WExt:InitWidget('store_featured_banner_title', StoreFeatured),
	bannerPrice = WExt:InitWidget('store_featured_banner_price', StoreFeatured),
	bannerTag	= WExt:InitWidget('store_featured_banner_tag', StoreFeatured),
	bannerDesc	= WExt:InitWidget('store_featured_banner_description', StoreFeatured),
	bannerFeatures = WExt:InitWidget('store_featured_banner_features', StoreFeatured),
	bannerDots	= WExt:InitWidget('store_featured_banner_dots', StoreFeatured),
	gridRow0	= WExt:InitWidget('store_featured_grid_row0', StoreFeatured),
	gridRow1	= WExt:InitWidget('store_featured_grid_row1', StoreFeatured),
	marketRow	= WExt:InitWidget('store_featured_row_cards_marketplace', StoreFeatured),
}

---- CONFIGS ----
local FEATURED_BANNER_ROTATE_MS = 15000

local BANNER_PRODUCTS =
{
	{
		name = 'Warforged Chipper',
		key = 'Hero.Chipper.Warforged',
		priceKeys = { 'Hero.Chipper.Warforged' },
		rarity = 'legendary',
		route = { tab = Enum.StoreTabs.Avatars },
		bannerImage = '/ui/fe3/store/featured/featured_banner_1.tga',
		tag = 'НОВЫЙ ЛЕГЕНДАРНЫЙ ОБЛИК',
		description = '',
		featureFlags = {
			vfx = true,
			sfx = true,
			voice = true,
			anims = true,
			icons = true,
		},
	},
	{
		name = 'Headmistress Succubus',
		key = 'Hero.Succubus.Headmistress',
		priceKeys = { 'Hero.Succubus.Headmistress' },
		rarity = 'epic',
		route = { tab = Enum.StoreTabs.Avatars },
		bannerImage = '/ui/fe3/store/featured/featured_banner_2.tga',
		tag = 'НОВЫЙ ЭПИЧЕСКИЙ ОБЛИК',
		description = '',
		featureFlags = {
			vfx = true,
			sfx = true,
			voice = true,
			anims = true,
			icons = false,
		},
	},
	{
		name = 'Loki',
		key = 'Hero.CorruptedDisciple.Loki',
		priceKeys = { 'Hero.CorruptedDisciple.Loki' },
		rarity = 'legendary',
		route = { tab = Enum.StoreTabs.Avatars },
		bannerImage = '/ui/fe3/store/featured/featured_banner_3.tga',
		tag = 'НОВЫЙ ЛЕГЕНДАРНЫЙ ОБЛИК',
		description = '',
		featureFlags = {
			vfx = true,
			sfx = false,
			voice = true,
			anims = true,
			icons = true,
		},
	},
	{
		name = 'Lion Nighthound',
		key = 'Hero.NightHound.Lion',
		priceKeys = { 'Hero.NightHound.Lion' },
		rarity = 'legendary',
		route = { tab = Enum.StoreTabs.Avatars },
		bannerImage = '/ui/fe3/store/featured/featured_banner_4.tga',
		tag = 'НОВЫЙ ЛЕГЕНДАРНЫЙ ОБЛИК',
		description = '',
		featureFlags = {
			vfx = true,
			sfx = false,
			voice = true,
			anims = true,
			icons = true,
		},
	}
}

local BANNER_FEATURE_BADGES =
{
	{ id = 'vfx', label = 'VFX' },
	{ id = 'sfx', label = 'SFX' },
	{ id = 'voice', label = 'VOICE' },
	{ id = 'anims', label = 'ANIMS' },
	{ id = 'icons', label = 'ICONS' },
}

local BANNER_FEATURE_SPACING_H = 4.65
local BANNER_TITLE_RARITIES = { 'common', 'uncommon', 'rare', 'epic', 'legendary' }

local GRID_PRODUCTS =
{
	{ name = 'VRZO English Announcer', key = 'Announcer.ThaiEnglish', new = true },
	{ name = 'Katana Kane', key = 'Hero.Kane.Katana', new = false },
	{ name = 'Demon Emerald Warden', key = 'Hero.EmeraldWarden.Demon', new = false },
	{ name = 'Vampira Dark Lady', key = 'Hero.DarkLady.Vampira', new = false },

}

local CATEGORY_INFO =
{
	[Enum.ActivationType.HeroSkins]   = { name = 'Avatar',         icon = '/ui/hd_ui/icons/ck.tga'        },
	[Enum.ActivationType.Announcers]  = { name = 'Announcer Pack', icon = '/ui/hd_ui/icons/mic.tga'       },
	[Enum.ActivationType.Couriers]    = { name = 'Courier',        icon = '/ui/hd_ui/icons/courier.tga'   },
	[Enum.ActivationType.Ravens]      = { name = 'Raven',          icon = '/ui/hd_ui/icons/raven.tga'     },
	[Enum.ActivationType.Wards]       = { name = 'Ward',           icon = '/ui/hd_ui/icons/eye.tga'       },
	[Enum.ActivationType.KillEffects] = { name = 'Kill Effect',    icon = '/ui/hd_ui/icons/dead.tga'      },
	[Enum.ActivationType.Teleports]   = { name = 'Teleport Effect', icon = '/content/icons/teleport.tga'   },
	[Enum.ActivationType.Gestures]    = { name = 'Gesture',        icon = '/ui/hd_ui/icons/thumbs-up.tga' },
	[Enum.ActivationType.Roasts]      = { name = 'Roast',          icon = '/ui/hd_ui/icons/roast.tga'     },
	[Enum.ActivationType.Shoutouts]   = { name = 'Shoutout',       icon = '/ui/hd_ui/icons/mic.tga'       },
	[Enum.ActivationType.Icons]       = { name = 'Account Icon',   icon = '/content/icons/account_icon.tga' },
	[Enum.ActivationType.NameColors]  = { name = 'Name Color',     icon = '/content/icons/account_icon.tga' },
}

local ACCOUNT_UPGRADE_CATEGORY_INFO = { name = 'Account Upgrade', icon = '/content/icons/account_icon.tga' }

local RARITY_DISPLAY =
{
	common    = 'Обычный',
	uncommon  = 'Необычный',
	rare      = 'Редкий',
	epic      = 'Эпический',
	legendary = 'Легендарный',
}

local TILE_VARIANTS =
{
	square =
	{
		prefix            = 'store_featured_square_',
		allowIconFallback = true,
		showNewEffect     = true,
	},
	card =
	{
		prefix            = 'store_featured_card_',
		allowIconFallback = false,
		showNewEffect     = false,
	},
}

local MARKETPLACE_DEAL_POOL_SIZE = 20
local MARKETPLACE_DEAL_MAX_PRICE = 260

local CLICK_MODE = 'navigate' -- 'navigate' | 'buy'

---- STATE ----
local populated	= false
local bannerEntry	= nil
local activeBannerIndex = 1
local currentBannerItems = {}
local currentGridEntries	= {}
local productByName	= nil
local productInfoCache	= {}
local randomSeeded	= false
local bannerRotationToken = 0

----------------------------------------------
--				   Helpers					--
----------------------------------------------

local function GetDayOfYearSeed()
	return floor(GetHostTime() / 86400)
end

local function EnsureRandomSeeded()
	if randomSeeded then return end
	randomSeeded = true
	math.randomseed(GetHostTime())
end

local function SetWidgetVisible(widget, visible)
	if widget then widget:SetVisible(visible and 1 or 0) end
end

local function BuildProductLookup()
	if productByName then return end

	productByName = {}
	for category in pairs(Enum.ShopCategory) do
		local products = Store:GetProductData(category)
		if products then
			for _, wrapper in ipairs(products) do
				local entry = wrapper[1]
				if entry then
					if entry.productName and not productByName[entry.productName] then
						productByName[entry.productName] = entry
					end
					-- Activation-derived entries (kill effects, teleports, etc.) often have no
					-- productName, only key. Index by key so the config can reference them.
					if entry.key and not productByName[entry.key] then
						productByName[entry.key] = entry
					end
				end
			end
		end
	end
	local accountUpgrades = Store:GetProductData('AccountUpgrade')
	if accountUpgrades then
		for _, wrapper in ipairs(accountUpgrades) do
			local entry = wrapper[1]
			if entry then
				if entry.productName and not productByName[entry.productName] then
					productByName[entry.productName] = entry
				end
				if entry.key and not productByName[entry.key] then
					productByName[entry.key] = entry
				end
			end
		end
	end
end

local function FindProductByName(productName)
	if not productName then return nil end
	BuildProductLookup()
	return productByName and productByName[productName] or nil
end

local function FindProductByAnyIdentifier(identifiers)
	if type(identifiers) ~= 'table' then return FindProductByName(identifiers) end
	for i = 1, #identifiers do
		local entry = FindProductByName(identifiers[i])
		if entry then return entry end
	end
	return nil
end

local function GetProductInfoCached(entry)
	if not entry or not entry.key then return nil end
	local cached = productInfoCache[entry.key]
	if cached then return cached end
	local productInfo = GetProductInfo(entry.key)
	if productInfo then
		productInfoCache[entry.key] = productInfo
		return productInfo
	end
	return nil
end

local function GetCategoryInfo(entry)
	if not entry or not entry.key then return nil end
	if entry.productCategory == 'AccountUpgrade' then return ACCOUNT_UPGRADE_CATEGORY_INFO end
	local productInfo = GetProductInfoCached(entry)
	if productInfo and productInfo[1] and productInfo[1].type then
		return CATEGORY_INFO[productInfo[1].type]
	end
	return nil
end

local function IsHeroSkinEntry(entry)
	if not entry or not entry.key then return false end
	local productInfo = GetProductInfoCached(entry)
	return productInfo and productInfo[1] and productInfo[1].type == Enum.ActivationType.HeroSkins
end

local function IsTruthyFlag(value)
	if value == true or value == 1 then return true end
	if type(value) ~= 'string' then return false end
	local valueLower = string.lower(value)
	return valueLower == '1' or valueLower == 'true' or valueLower == 'new'
end

local function IsFeaturedNewProductConfig(configEntry)
	return type(configEntry) == 'table' and IsTruthyFlag(configEntry.new)
end

local function IsNewProductEntry(entry, configEntry)
	if not entry then return false end
	if IsFeaturedNewProductConfig(configEntry) then return true end
	if IsTruthyFlag(entry.isNew) or IsTruthyFlag(entry.new) then return true end
	if not entry.key then return false end
	local productInfo = GetProductInfoCached(entry)
	return productInfo and (IsTruthyFlag(productInfo.isNew) or IsTruthyFlag(productInfo.new)) or false
end

local function BuildSubtitle(entry, catInfo)
	local categoryName = (catInfo and catInfo.name) or 'Avatar'
	local rarity = entry and entry.rarity or 'common'
	local rarityName = RARITY_DISPLAY[rarity]
	if rarityName then
		return rarityName .. ' ' .. categoryName
	end
	return categoryName
end

local function GetDisplayRarity(entry, config)
	return (config and config.rarity) or (entry and entry.rarity) or 'common'
end

local function GetDisplayRarityName(rarity)
	return RARITY_DISPLAY[rarity] or rarity or ''
end

local function StripAlpha(hex)
	if not hex then return nil end
	if #hex == 9 then return hex:sub(1, 7) end
	return hex
end

local function ApplyBannerTitleGradient(entry, config)
	local rarity = GetDisplayRarity(entry, config)
	local theme = Store:GetRarityTheme(rarity)
	local titleText = entry and entry.productName or ''
	local hasRarityLabel = false

	for i = 1, #BANNER_TITLE_RARITIES do
		local rarityName = BANNER_TITLE_RARITIES[i]
		local titleLabel = Main:GetWidget('store_featured_banner_title_' .. rarityName)
		if titleLabel then
			local active = rarityName == rarity
			titleLabel:SetText(titleText)
			titleLabel:SetVisible(active and 1 or 0)
			hasRarityLabel = hasRarityLabel or active
		end
	end

	if widgets.bannerTitle then
		local themeColor = StripAlpha(theme and theme.border_color)
		widgets.bannerTitle:SetText((theme and theme.name_prefix or '') .. titleText .. '^*')
		widgets.bannerTitle:SetColor(themeColor or '1 1 1 1')
		widgets.bannerTitle:SetVisible(hasRarityLabel and 0 or 1)
	end

	return rarity
end

local function ApplyBannerFeatures(config)
	local flags = config and config.featureFlags or {}
	local activeBadges = {}

	for i = 1, #BANNER_FEATURE_BADGES do
		local badge = BANNER_FEATURE_BADGES[i]
		local root = Main:GetWidget('store_featured_banner_feature_' .. badge.id)
		if root then root:SetVisible(0) end
		if flags[badge.id] then activeBadges[#activeBadges + 1] = badge end
	end

	SetWidgetVisible(widgets.bannerFeatures, #activeBadges > 0)

	for i = 1, #activeBadges do
		local badge = activeBadges[i]
		local root = Main:GetWidget('store_featured_banner_feature_' .. badge.id)
		local offsetX = (i - 1) * BANNER_FEATURE_SPACING_H

		if root then
			root:SetX(format('%.2fh', offsetX))
			root:SetVisible(1)
		end
	end
end

local function PickRandomProductFromCategory(category)
	local products = Store:GetProductData(category)
	if not products or #products == 0 then return nil end

	local candidates = {}
	for _, wrapper in ipairs(products) do
		local entry = wrapper[1]
		if entry and not entry.isBase then
			candidates[#candidates + 1] = entry
		end
	end

	if #candidates == 0 then return nil end
	EnsureRandomSeeded()
	return candidates[math.random(#candidates)]
end

local function GetGridProductName(configEntry)
	if type(configEntry) == 'table' then return configEntry.name end
	return configEntry
end

local function ResolveGridEntry(configEntry)
	local productName = GetGridProductName(configEntry)
	if not productName then return nil end
	local entry = type(configEntry) == 'table' and FindProductByName(configEntry.key) or nil
	entry = entry or FindProductByName(productName)
	if entry and not entry.isBase then return entry end

	if Enum.ShopCategory[productName] ~= nil then
		return PickRandomProductFromCategory(productName)
	end
	return entry
end

local function IsBannerProductName(productName)
	if not productName then return false end
	for i = 1, #BANNER_PRODUCTS do
		local bannerProduct = BANNER_PRODUCTS[i]
		if bannerProduct.name == productName or bannerProduct.key == productName then
			return true
		end
		if type(bannerProduct.priceKeys) == 'table' then
			for j = 1, #bannerProduct.priceKeys do
				if bannerProduct.priceKeys[j] == productName then return true end
			end
		end
	end
	return false
end

local function BuildMarketplaceList()
	local products = Store:GetProductData('HeroSkin')
	if not products then return {} end

	local priced = {}
	for _, wrapper in ipairs(products) do
		local entry = wrapper[1]
		if entry and not entry.isBase then
			local price = Store:ResolveJadePrice(entry)
			if price and price > 0 then
				tinsert(priced, { entry = entry, price = price })
			end
		end
	end

	if #priced == 0 then return {} end

	tsort(priced, function(a, b) return a.price > b.price end)

	local result = {}
	local usedNames = {}
	for i = 1, math.min(3, #priced) do
		result[#result + 1] = priced[i].entry
		usedNames[priced[i].entry.productName] = true
	end

	local cheapPool = {}
	for i = #priced, 1, -1 do
		local name = priced[i].entry.productName
		if not usedNames[name] and not IsBannerProductName(name) and priced[i].price <= MARKETPLACE_DEAL_MAX_PRICE then
			cheapPool[#cheapPool + 1] = priced[i].entry
			if #cheapPool >= MARKETPLACE_DEAL_POOL_SIZE then break end
		end
	end
	if #cheapPool > 0 then
		local dealIndex = (GetDayOfYearSeed() % #cheapPool) + 1
		result[#result + 1] = cheapPool[dealIndex]
	end

	return result
end

local function ResolveTileImage(imageW, entry, allowIconFallback)
	if allowIconFallback and IsHeroSkinEntry(entry) then
		imageW:SetWidth('200@')
	else
		imageW:SetWidth('100%')
	end

	if entry then
		if entry.storeIcon and entry.storeIcon ~= '' then
			imageW:SetTexture(entry.storeIcon)
			imageW:SetColor(1, 1, 1, 1)
			return
		end
		if allowIconFallback and entry.icon and entry.icon ~= '' then
			imageW:SetTexture(entry.icon)
			imageW:SetColor(1, 1, 1, 1)
			return
		end
	end
	imageW:SetTexture('$white')
	imageW:SetColor(.18, .18, .18, 1)
end

local function PopulateTile(variant, cardId, entry, configEntry)
	local cfg = TILE_VARIANTS[variant]
	local prefix = cfg.prefix

	local function w(suffix) return Main:GetWidget(prefix .. suffix .. '_' .. cardId) end

	local imageW = w('image')
	if imageW then ResolveTileImage(imageW, entry, cfg.allowIconFallback) end

	local rarityTheme = Store:GetRarityTheme(entry.rarity or 'common')
	local nameW = w('name')
	if nameW then
		nameW:SetText(entry.productName or '')
		if rarityTheme then nameW:SetColor(rarityTheme['border_color']) end
	end

	local catInfo = GetCategoryInfo(entry)
	local subtitleText = (variant == 'card' and cardId == 'market_3')
		and 'Deal of the Day'
		or BuildSubtitle(entry, catInfo)
	local subtitleW = w('subtitle')
	if subtitleW then subtitleW:SetText(subtitleText) end

	local catIconW = w('caticon')
	if catIconW and catInfo and catInfo.icon then catIconW:SetTexture(catInfo.icon) end

	local priceW = w('price')
	if priceW then
		local jadePrice = Store:ResolveJadePrice(entry)
		priceW:SetText(jadePrice and tostring(jadePrice) or '')
	end

	local rarityW = w('rarity')
	if rarityW and rarityTheme then rarityW:SetBorderColor(rarityTheme['border_color']) end

	if cfg.showNewEffect then
		local newEffectW = w('new_effect')
		if newEffectW then
			newEffectW:SetEffect('/ui/effects/product_new_featured.effect')
			if IsNewProductEntry(entry, configEntry) and (IsFeaturedNewProductConfig(configEntry) or not entry.owned) then
				newEffectW:FadeIn(150)
			else
				newEffectW:FadeOut(150)
			end
		end
	end

	local btn = Main:GetWidget(prefix .. cardId)
	if btn then
		btn:SetCallback('onclick', function() StoreFeatured:OnTileClick(entry) end)
	end
end

local function RefreshTilePrice(widgetName, entry)
	if not entry then return end
	local priceW = Main:GetWidget(widgetName)
	if not priceW then return end
	local jadePrice = Store:ResolveJadePrice(entry)
	priceW:SetText(jadePrice and tostring(jadePrice) or '')
end

local function ResolveBannerItems()
	currentBannerItems = {}
	for i = 1, #BANNER_PRODUCTS do
		local config = BANNER_PRODUCTS[i]
		local catalogEntry = FindProductByName(config.key)
			or FindProductByAnyIdentifier(config.priceKeys)
			or FindProductByName(config.name)
		if catalogEntry and catalogEntry.isBase then catalogEntry = nil end

		-- Banner configuration is authoritative. Catalog data adds live pricing and
		-- purchase metadata, but a missing catalog record must not remove the slide.
		local displayEntry = catalogEntry or {
			key = config.key,
			productName = config.name or config.key or '',
			rarity = config.rarity,
			isBase = false,
		}
		local priceEntry = FindProductByAnyIdentifier(config.priceKeys) or catalogEntry
		currentBannerItems[#currentBannerItems + 1] = {
			config = config,
			entry = displayEntry,
			catalogEntry = catalogEntry,
			priceEntry = priceEntry,
		}
	end
end

local function UpdateBannerPagination()
	local bannerCount = #currentBannerItems
	SetWidgetVisible(widgets.bannerDots, bannerCount > 1)

	for i = 0, 3 do
		local visible = i < bannerCount
		local active = i + 1 == activeBannerIndex
		local dot = Main:GetWidget('store_featured_banner_dot_' .. tostring(i))
		local frame = Main:GetWidget('store_featured_banner_dot_frame_' .. tostring(i))
		local label = Main:GetWidget('store_featured_banner_dot_label_' .. tostring(i))

		SetWidgetVisible(dot, visible)
		if visible and dot then dot:SetColor(active and '.08 .08 .08 .9' or '.08 .08 .08 .7') end
		if visible and frame then frame:SetBorderColor(active and '1 1 1 1' or '.4 .4 .4 1') end
		if visible and label then label:SetColor(active and '1 1 1 1' or '.75 .75 .75 1') end
	end
end

local function PopulateBanner(index)
	local bannerCount = #currentBannerItems
	if bannerCount == 0 then return end

	activeBannerIndex = ((index or activeBannerIndex or 1) - 1) % bannerCount + 1
	local bannerItem = currentBannerItems[activeBannerIndex]
	local entry = bannerItem and bannerItem.entry
	local priceEntry = bannerItem and bannerItem.priceEntry or entry
	local config = bannerItem and bannerItem.config
	bannerEntry = entry
	if not entry or not config then return end

	widgets.bannerImage:SetTexture(config.bannerImage or '$invis')
	widgets.bannerTitle:SetText(entry.productName or '')
	local rarity = ApplyBannerTitleGradient(entry, config)
	local jadePrice = Store:ResolveJadePrice(priceEntry)
	widgets.bannerPrice:SetText(jadePrice and tostring(jadePrice) or '')
	widgets.bannerTag:SetText(config.tag or ('NEW ' .. string.upper(GetDisplayRarityName(rarity)) .. ' AVATAR'))
	widgets.bannerDesc:SetText(config.description or '')
	ApplyBannerFeatures(config)
	UpdateBannerPagination()
end

local function StartBannerRotation()
	bannerRotationToken = bannerRotationToken + 1
	local token = bannerRotationToken
	if #currentBannerItems <= 1 or not widgets.bannerRoot then return end

	widgets.bannerRoot:Sleep(FEATURED_BANNER_ROTATE_MS, function()
		if token ~= bannerRotationToken or not populated then return end
		PopulateBanner(activeBannerIndex + 1)
		StartBannerRotation()
	end)
end

local function PopulateGrid()
	local rowPanels = { widgets.gridRow0, widgets.gridRow1 }
	for row = 0, 1 do
		local rowPanel = rowPanels[row + 1]
		for col = 0, 1 do
			local idx = row * 2 + col
			local configEntry = GRID_PRODUCTS[idx + 1]
			local entry = ResolveGridEntry(configEntry)
			local cardId = 'grid_' .. tostring(idx)

			rowPanel:InstantiateAndReturn('store_featured_square_tile', 'id', cardId, 'align', col == 0 and 'left' or 'right')

			if entry then
				currentGridEntries[idx + 1] = entry
				PopulateTile('square', cardId, entry, configEntry)
			end
		end
	end
end

local function PopulateMarketplaceRow()
	widgets.marketRow:ClearChildren()
	local entries = BuildMarketplaceList()
	for i = 1, 4 do
		local entry = entries[i]
		local cardId = 'market_' .. tostring(i - 1)
		widgets.marketRow:InstantiateAndReturn('store_featured_card', 'id', cardId)
		if entry then PopulateTile('card', cardId, entry) end
	end
end

local function ClearBanner()
	widgets.bannerImage:SetTexture('$invis')
	widgets.bannerTitle:SetText('')
	widgets.bannerPrice:SetText('')
	widgets.bannerTag:SetText('')
	widgets.bannerDesc:SetText('')
	ApplyBannerFeatures(nil)
	bannerEntry = nil
	activeBannerIndex = 1
	currentBannerItems = {}
	bannerRotationToken = bannerRotationToken + 1
	UpdateBannerPagination()
end

----------------------------------------------
--					Code					--
----------------------------------------------

function StoreFeatured:Populate()
	if populated then return end

	ClearBanner()
	widgets.gridRow0:ClearChildren()
	widgets.gridRow1:ClearChildren()
	widgets.marketRow:ClearChildren()
	currentGridEntries = {}

	local products = Store:GetProductData('HeroSkin')
	if not products or #products == 0 then return end
	BuildProductLookup()

	populated = true

	ResolveBannerItems()
	PopulateBanner(1)
	StartBannerRotation()
	PopulateGrid()
	PopulateMarketplaceRow()
end

function StoreFeatured:RefreshPrices()
	if not populated then
		StoreFeatured:Populate()
		return
	end

	if bannerEntry then
		local bannerItem = currentBannerItems[activeBannerIndex]
		RefreshTilePrice('store_featured_banner_price', (bannerItem and bannerItem.priceEntry) or bannerEntry)
	end
	for idx = 0, 3 do
		RefreshTilePrice('store_featured_square_price_grid_' .. tostring(idx), currentGridEntries[idx + 1])
	end
	PopulateMarketplaceRow()
end

function StoreFeatured:Reset()
	populated = false
	bannerEntry = nil
	activeBannerIndex = 1
	currentBannerItems = {}
	currentGridEntries = {}
	productByName = nil
	productInfoCache = {}
	bannerRotationToken = bannerRotationToken + 1
end

function StoreFeatured:OnTileClick(entry)
	if not entry then return end
	if CLICK_MODE == 'navigate' then
		Store:NavigateToProduct(entry)
	else
		Store:ShowPurchaseConfirmationWindow('buy', nil, entry)
	end
end

function StoreFeatured:OnBannerDemo()
	if not bannerEntry or not bannerEntry.key then return end

	local productKey = bannerEntry.key
	local slug = Store:ExtractHeroSlugFromProductKey(productKey)
	if not slug then return end

	local heroName = 'Hero_' .. slug

	if not HeroList:CanFieldTest() then return end

	local gameVars = {}
	gameVars.map = 'fieldtest'
	gameVars.gameName = 'Field Test'
	gameVars.teamSize = 5

	SetSave('practice_team', 0, 'int')
	SetSave('practice_fakeplayers', 0, 'int')
	SetSave('practice_hero', heroName, 'string')
	SetSave('practice_avatar', productKey, 'string')

	if (Testing.IsPracticeGame and Testing.IsPracticeGame()) or (Testing.IsLocalGame and Testing.IsLocalGame()) then
		local owner = GetLocalClientNumber()

		-- SpawnUnit reads back its own entity index, so the chain has to land on the main thread as one unit.
		Testing.RunOnMainThread(function()
			local team = Testing.GetLocalPlayerTeamID()
			local entityId = Testing.GetPlayerHeroIndex(owner)
			local entityInfo = Testing.GetEntityInfo(entityId)
			local pos = entityInfo.position

			Testing.Precache(heroName)
			local unit = Testing.SpawnUnit(heroName, owner, team, pos.x, pos.y)
			if (Testing.EntityIsHero(unit)) then
				Testing.SetPlayerHero(owner, unit)
				Testing.Delete(entityId)
			else
				Testing.Delete(unit)
			end
		end)

		SelectAvatar(productKey, nil)
		Cmd('Action ToggleOverlayMenuGame')
	else
		PlayerHosted:CreatePracticeGame(gameVars)
	end
end

function StoreFeatured:OnBannerPreview()
	if not bannerEntry then return end

	local bannerItem = currentBannerItems[activeBannerIndex]
	local route = Store:GetProductRoute(bannerEntry) or (bannerItem and bannerItem.config and bannerItem.config.route)
	if not route then return end

	Store:SwitchTab(route.tab)
	if route.subTab then
		Store:SwitchSubTab(route.subTab)
	end
	Store:SelectProductByEntry(bannerEntry, true)
end

function StoreFeatured:OnBannerUnlock()
	if bannerEntry then
		Store:ShowPurchaseConfirmationWindow('buy', nil, bannerEntry)
	end
end

function StoreFeatured:OnBannerPage(pageIndex)
	local index = tonumber(pageIndex)
	if not index then return end
	index = index + 1
	if not currentBannerItems[index] then return end

	PopulateBanner(index)
	StartBannerRotation()
end

----------------------------------------------
--					Init					--
----------------------------------------------

function StoreFeatured:Init()
	WExt:ProcessInitWidgets(StoreFeatured, Main)
end
