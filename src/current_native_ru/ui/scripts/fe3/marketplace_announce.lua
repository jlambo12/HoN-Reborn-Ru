----------------------------------------------------------
--	Name: 		Marketplace Announce FE3				--
--  (C) 2026 Juvio, LLC									--
----------------------------------------------------------

local _G = getfenv(0)
local ipairs, pairs, select, string, table, next, type, unpack, tinsert, tconcat, tremove, format, tostring, tonumber, tsort, ceil, floor, sub, find, gfind = 
_G.ipairs, _G.pairs, _G.select, _G.string, _G.table, _G.next, _G.type, _G.unpack, _G.table.insert, _G.table.concat, _G.table.remove, _G.string.format, 
_G.tostring, _G.tonumber, _G.table.sort, _G.math.ceil, _G.math.floor, _G.string.sub, _G.string.find, _G.string.gfind
local interface, interfaceName = object, object:GetName()

MarketplaceAnnounce = _G['MarketplaceAnnounce'] or {}

----------------------------------------------
--					Vars					--
----------------------------------------------
local COUNTDOWN_TICK_MS = 1000
local PRODUCT_ROTATE_MS = 15000
local CLIENT_LOAD_DELAY_MS = 3000
local PRODUCT_SWAP_EFFECT = '/ui/effects/marketplace_announce_swap.effect'
local PRODUCT_SWAP_EFFECT_SWAP_MS = 110
local PRODUCT_SWAP_EFFECT_CLEAR_MS = 420

local COUNTDOWN_IDS = { 'days', 'hours', 'mins', 'secs' }
local countdownValues, countdownUnits
local countdownToken = 0
local productRotationToken = 0
local productRotationSuspended = false
local priceRequestToken = 0
local registersSetup = false

local MODEL_REVEAL_DELAY_MS = 200

local MARKETPLACE_PRODUCTS = {
	{
		key = 'Hero.CorruptedDisciple.Loki',
		title = 'Loki',
		shopCategory = 'HeroSkin',
		productType = 'avatar',
		rarity = 'legendary',
		storeModel = '/heroes/corrupted_disciple/loki/store/store.mdf',
		storeEffect = '/heroes/corrupted_disciple/loki/effects/body_store_no_sfx.effect',
		modalStoreEffect = '/heroes/corrupted_disciple/loki/effects/body_store.effect',
		titleEffect = '/ui/effects/marketplace_loki_corrupted_disciple_title.effect',
		titleImage = '/ui/fe3/elements/feature_avatar_title_3.png',
		availabilityText = 'Этот облик нельзя продать.',
		featureTitle = 'INCLUDES NEW:',
		limited = false,
		marketable = false,
		mainModelPosition = '0 0 -20',
		mainModelScale = 1,
		modalModelPosition = '0 0 -20',
		modalModelScale = 1,
		featureFlags = {
			vfx = true,
			sfx = false,
			voice = true,
			anims = true,
			icons = true,
		},
	},
	{
		key = 'Announcer.ThaiEnglish',
		title = 'VRZO English Announcer',
		shopCategory = 'Announcer',
		productType = 'announcer',
		rarity = 'legendary',
		storeModel = '/core/null/invis.mdf',
		storeEffect = '',
		modalStoreEffect = '',
		showAvailability = false,
		limited = false,
		marketable = false,
		mainModelPosition = '0 0 0',
		mainModelScale = 1,
		modalModelPosition = '0 0 0',
		modalModelScale = 1,
		stage = {
			type = 'announcer',
			model = '/shared/models/invis.mdf',
			effect = '/content/stages/announcer/base/effects/thaienglish.effect',
			backgroundImage = '/content/stages/announcer/base/store_bg.tga',
		},
		featureFlags = {},
	},

}

local ANNOUNCE_FEATURE_BADGES = { 'vfx', 'sfx', 'voice', 'anims', 'icons' }

local FEATURE_BADGE_SPACING_H = 6.0

local stageCache = {}
local activeProductIndex = 1
local activeProduct = MARKETPLACE_PRODUCTS[activeProductIndex]
local announceWidgets = {}
local announceStageWidget = nil
local announceAnnouncerStageWidget = nil
local announceModelPanel = nil
local announceStageWidgetModal = nil
local announceAnnouncerStageWidgetModal = nil
local announceModelPanelModal = nil
local lastAnnouncerDemoKey = nil

-----------------------------------------------
--					 Code					 --
-----------------------------------------------

local function CacheMarketplaceWidgets()
	if not announceStageWidget then
		announceStageWidget = Main:GetWidget('marketplace_announce_stage')
	end
	if not announceAnnouncerStageWidget then
		announceAnnouncerStageWidget = Main:GetWidget('marketplace_announce_stage_announcer')
	end
	if not announceModelPanel then
		announceModelPanel = Main:GetWidget('marketplace_announce_modelpanel')
	end
	if not announceStageWidgetModal then
		announceStageWidgetModal = Main:GetWidget('marketplace_announce_stage_modal')
	end
	if not announceAnnouncerStageWidgetModal then
		announceAnnouncerStageWidgetModal = Main:GetWidget('marketplace_announce_stage_announcer_modal')
	end
	if not announceModelPanelModal then
		announceModelPanelModal = Main:GetWidget('marketplace_announce_modelpanel_modal')
	end

	if not announceWidgets.root then
		announceWidgets.root = Main:GetWidget('marketplace_announce_root')
		announceWidgets.modalRoot = Main:GetWidget('marketplace_announce_modal_root')
		announceWidgets.titleEffect = Main:GetWidget('marketplace_announce_title_effect')
		announceWidgets.titleEffectModal = Main:GetWidget('marketplace_announce_title_effect_modal')
		announceWidgets.titleImage = Main:GetWidget('marketplace_announce_title_image')
		announceWidgets.titleImageModal = Main:GetWidget('marketplace_announce_title_image_modal')
		announceWidgets.titleLabel = Main:GetWidget('marketplace_announce_title_label')
		announceWidgets.titleLabelModal = Main:GetWidget('marketplace_announce_title_label_modal')
		announceWidgets.stageBackground = Main:GetWidget('marketplace_announce_stage_background')
		announceWidgets.stageBackgroundModal = Main:GetWidget('marketplace_announce_stage_background_modal')
		announceWidgets.subtitle = Main:GetWidget('marketplace_announce_subtitle_label')
		announceWidgets.statusRoot = Main:GetWidget('marketplace_announce_status_root')
		announceWidgets.status = Main:GetWidget('marketplace_announce_status_label')
		announceWidgets.subtitleModal = Main:GetWidget('marketplace_announce_available_label_modal')
		announceWidgets.includesTitle = Main:GetWidget('marketplace_announce_includes_title')
		announceWidgets.countdownRoot = Main:GetWidget('marketplace_announce_countdown_root')
		announceWidgets.mainButton = Main:GetWidget('marketplace_announce_purchase_button')
		announceWidgets.mainLabel = Main:GetWidget('marketplace_announce_purchase_label')
		announceWidgets.modalButton = Main:GetWidget('marketplace_announce_purchase_button_modal')
		announceWidgets.modalLabel = Main:GetWidget('marketplace_announce_purchase_label_modal')
		announceWidgets.demoLabel = Main:GetWidget('marketplace_announce_demo_button_modal_label')
		announceWidgets.demoPlayIcon = Main:GetWidget('marketplace_announce_demo_button_modal_play_icon')
		announceWidgets.swapEffect = Main:GetWidget('marketplace_announce_swap_effect')
		announceWidgets.swapEffectModal = Main:GetWidget('marketplace_announce_swap_effect_modal')
	end
end

local function PlaySwapEffect(widget)
	if not widget then return end
	widget:SetVisible(1)
	widget:SetEffect('')
	widget:SetEffect(PRODUCT_SWAP_EFFECT)
end

local function ClearSwapEffect(widget)
	if not widget then return end
	widget:SetEffect('')
	widget:SetVisible(0)
end

local function CacheCountdownWidgets()
	if countdownValues then return true end
	countdownValues, countdownUnits = {}, {}
	for i = 1, #COUNTDOWN_IDS do
		local id = COUNTDOWN_IDS[i]
		countdownValues[i] = Main:GetWidget('marketplace_countdown_value_' .. id)
		countdownUnits[i]  = Main:GetWidget('marketplace_countdown_unit_' .. id)
		if not countdownValues[i] then countdownValues = nil; return false end
	end
	return true
end

local function SetWidgetVisible(widget, visible)
	if widget then widget:SetVisible(visible and 1 or 0) end
end

local function SetWidgetText(widget, text)
	if widget then widget:SetText(text or '') end
end

local function SetWidgetTexture(widget, texture)
	if widget and texture then widget:SetTexture(texture) end
end

local function GetActiveProduct()
	activeProduct = MARKETPLACE_PRODUCTS[activeProductIndex]
	return activeProduct
end

local function ProductIsLimited(product)
	return product and product.limited and product.countdownTargetUtc and product.countdownTargetUtc > 0
end

local function ProductIsMarketable(product)
	if not product then return false end
	if product.marketable ~= nil then return product.marketable end
	if IsMarketableProductKey then return IsMarketableProductKey(product.key) end
	return false
end

local function ProductShowsCountdown(product)
	return ProductIsLimited(product) and ProductIsMarketable(product)
end

local function ProductIsAvailable(product)
	if not ProductIsLimited(product) then return true end
	local now = GetHostUnixTime()
	if product.countdownStartUtc and product.countdownStartUtc > 0 and now < product.countdownStartUtc then return false end
	return now < product.countdownTargetUtc
end

local function FindAvailableProductIndex(startIndex, excludeIndex)
	local productCount = #MARKETPLACE_PRODUCTS
	if productCount == 0 then return nil end
	for offset = 0, productCount - 1 do
		local index = ((startIndex + offset - 1) % productCount) + 1
		if index ~= excludeIndex and ProductIsAvailable(MARKETPLACE_PRODUCTS[index]) then return index end
	end
	return nil
end

local function GetAvailabilityText(product)
	if product and product.availabilityText then return product.availabilityText end
	local marketable = ProductIsMarketable(product)
	if ProductIsLimited(product) then
		return marketable and 'Available for a Limited Time' or 'Limited Time - Not Marketable'
	end
	return marketable and 'Available Now - Marketplace Eligible' or 'Available Now - Not Marketable'
end

local function GetProductEntry(product)
	if not product then return nil end
	local category = product.shopCategory and Enum.ShopCategory[product.shopCategory]
	local products = category and GetCategoryProducts(category)
	if products then
		for i = 1, #products do
			local entry = products[i] and products[i][1]
			if entry and entry.key == product.key then return entry end
		end
	end
	local activations = category and GetCategoryActivations and GetCategoryActivations(category)
	if activations then
		for i = 1, #activations do
			local activation = activations[i]
			if activation and activation.key == product.key then return activation end
		end
	end
	if Store and Store.GetProductEntryByKey then return Store:GetProductEntryByKey(product.key) end
	return nil
end

local function GetProductActivation(product)
	if not product then return nil end
	-- Category activation records only contain the common store fields. Announcer
	-- event effects are populated by GetProductInfo's definition-specific table.
	local productInfo = GetProductInfo and GetProductInfo(product.key)
	if productInfo and productInfo[1] then return productInfo[1] end
	return GetProductEntry(product)
end

local function SetPurchaseState(enabled, label)
	CacheMarketplaceWidgets()
	if announceWidgets.mainButton then announceWidgets.mainButton:SetEnabled(enabled and 1 or 0) end
	if announceWidgets.modalButton then announceWidgets.modalButton:SetEnabled(enabled and 1 or 0) end
	SetWidgetText(announceWidgets.mainLabel, label or '---')
	SetWidgetText(announceWidgets.modalLabel, label or '---')
end

local function ApplyFeatureBadges()
	local activeBadgeIndexes = {}
	local product = GetActiveProduct()
	local featureFlags = product and product.featureFlags or {}
	CacheMarketplaceWidgets()

	SetWidgetText(announceWidgets.includesTitle, product and product.featureTitle or 'INCLUDES NEW:')

	for i = 1, #ANNOUNCE_FEATURE_BADGES do
		if featureFlags[ANNOUNCE_FEATURE_BADGES[i]] then
			tinsert(activeBadgeIndexes, i)
		end
	end

	local hasBadges = #activeBadgeIndexes > 0
	local includesPanel = Main:GetWidget('marketplace_announce_includes_panel')
	if includesPanel then includesPanel:SetVisible(hasBadges and 1 or 0) end

	for i = 1, #ANNOUNCE_FEATURE_BADGES do
		local root = Main:GetWidget('marketplace_announce_include_badge_' .. ANNOUNCE_FEATURE_BADGES[i])
		if root then root:SetVisible(0) end
	end

	if not hasBadges then return end

	local badgeCount = #activeBadgeIndexes
	for displayIndex = 1, badgeCount do
		local badgeKey = ANNOUNCE_FEATURE_BADGES[activeBadgeIndexes[displayIndex]]
		local root = Main:GetWidget('marketplace_announce_include_badge_' .. badgeKey)
		local offsetX = (displayIndex - ((badgeCount + 1) * 0.5)) * FEATURE_BADGE_SPACING_H

		if root then
			root:SetX(format('%.2fh', offsetX))
			root:SetVisible(1)
		end
	end
end

local function ApplyProductText(product)
	CacheMarketplaceWidgets()
	if not product then return end

	local availabilityText = GetAvailabilityText(product)
	local showCountdown = ProductShowsCountdown(product)
	local showAvailability = product.showAvailability ~= false

	SetWidgetText(announceWidgets.subtitle, availabilityText)
	SetWidgetText(announceWidgets.status, availabilityText)
	SetWidgetText(announceWidgets.subtitleModal, availabilityText)

	SetWidgetVisible(announceWidgets.countdownRoot, showCountdown)
	SetWidgetVisible(announceWidgets.subtitle, showAvailability and showCountdown)
	SetWidgetVisible(announceWidgets.statusRoot, showAvailability and not showCountdown)
	SetWidgetVisible(announceWidgets.subtitleModal, showAvailability)
end

local function ApplyProductTitleImage(product)
	CacheMarketplaceWidgets()
	if not product then return end

	local hasTitleImage = product.titleImage and product.titleImage ~= ''
	if hasTitleImage then
		SetWidgetTexture(announceWidgets.titleImage, product.titleImage)
		SetWidgetTexture(announceWidgets.titleImageModal, product.titleImage)
	end
	SetWidgetVisible(announceWidgets.titleImage, hasTitleImage)
	SetWidgetVisible(announceWidgets.titleImageModal, hasTitleImage)
	SetWidgetText(announceWidgets.titleLabel, product.title)
	SetWidgetText(announceWidgets.titleLabelModal, product.title)
	SetWidgetVisible(announceWidgets.titleLabel, not hasTitleImage)
	SetWidgetVisible(announceWidgets.titleLabelModal, not hasTitleImage)
end

local function ApplyProductDemoButton(product)
	CacheMarketplaceWidgets()
	local isAnnouncer = product and product.productType == 'announcer'
	SetWidgetText(announceWidgets.demoLabel, isAnnouncer and 'PLAY' or 'DEMO')
	SetWidgetVisible(announceWidgets.demoPlayIcon, isAnnouncer)
end

local function SetupMarketplaceStageWidget(stageWidget, modelPanel, stageCachePrefix, lightingCachePrefix, product, isModal)
	if not stageWidget or not modelPanel or not product then return end

	local stage = product.stage or product
	local activation = GetProductActivation(product)
	local modelAngles = activation and activation.store_angles
	if not modelAngles or modelAngles == '' then
		modelAngles = product.modelAngles or '0 0 0'
	end
	-- Cache entries describe what is currently applied to the selected stage widget,
	-- rather than each product's history.
	local stageCacheKey = stageCachePrefix
	local lightingCacheKey = lightingCachePrefix

	if stage.effect then
		ModelPanelShared:EnsureBgModelStage(
			stageWidget,
			stageCache,
			stageCacheKey,
			stage.effect,
			stage.model or '/shared/models/invis.mdf'
		)
		modelPanel:SetEffectWithIndex('', 1)
		stageCache[lightingCacheKey] = nil
	else
		local _, lightingEffect = ModelPanelShared:SetupAvatarStageWidget(
			stageWidget,
			stageCache,
			stageCacheKey,
			stage.storeModel or product.storeModel,
			stage.productKey or product.key
		)

		if lightingEffect then
			ModelPanelShared:EnsureStageSetup(modelPanel, stageCache, lightingCacheKey, lightingEffect, nil)
		end
	end

	modelPanel:SetModel(product.storeModel)
	modelPanel:SetAnim('idle')
	modelPanel:SetModelPosition(isModal and product.modalModelPosition or product.mainModelPosition)
	modelPanel:SetModelAngles(modelAngles)
	modelPanel:SetModelScale(isModal and product.modalModelScale or product.mainModelScale)
	ModelPanelShared:ApplyThemeSunOverrides(modelPanel, product.key)
	modelPanel:SetEffect((isModal and product.modalStoreEffect) or product.storeEffect)
end

local function SetupMarketplaceStage(revealModel)
	local product = GetActiveProduct()
	CacheMarketplaceWidgets()
	if not announceModelPanel or not product then return end

	local useAnnouncerStage = product.stage and product.stage.type == 'announcer'
	local stageWidget = useAnnouncerStage and announceAnnouncerStageWidget or announceStageWidget
	if not stageWidget then return end
	local stageBackground = product.stage and product.stage.backgroundImage
	if stageBackground then SetWidgetTexture(announceWidgets.stageBackground, stageBackground) end
	SetWidgetVisible(announceWidgets.stageBackground, stageBackground ~= nil)
	SetWidgetVisible(announceStageWidget, not useAnnouncerStage)
	SetWidgetVisible(announceAnnouncerStageWidget, useAnnouncerStage)

	if announceWidgets.titleEffect then
		announceWidgets.titleEffect:SetEffect(product.titleEffect or '')
	end
	ApplyProductTitleImage(product)
	ApplyProductDemoButton(product)

	if revealModel then announceModelPanel:SetColor('1 1 1 0') end
	SetupMarketplaceStageWidget(
		stageWidget,
		announceModelPanel,
		'marketplace_announce_stage',
		'marketplace_announce_lighting',
		product,
		false
	)

	if revealModel then
		announceModelPanel:Sleep(MODEL_REVEAL_DELAY_MS, function()
			announceModelPanel:SetColor('1 1 1 1')
		end)
	else
		announceModelPanel:SetColor('1 1 1 1')
	end
end

local function SetupMarketplaceModalStage()
	local product = GetActiveProduct()
	CacheMarketplaceWidgets()

	if announceModelPanelModal and product then
		local useAnnouncerStage = product.stage and product.stage.type == 'announcer'
		local stageWidget = useAnnouncerStage and announceAnnouncerStageWidgetModal or announceStageWidgetModal
		if not stageWidget then return end
		local stageBackground = product.stage and product.stage.backgroundImage
		if stageBackground then SetWidgetTexture(announceWidgets.stageBackgroundModal, stageBackground) end
		SetWidgetVisible(announceWidgets.stageBackgroundModal, stageBackground ~= nil)
		SetWidgetVisible(announceStageWidgetModal, not useAnnouncerStage)
		SetWidgetVisible(announceAnnouncerStageWidgetModal, useAnnouncerStage)

		if announceWidgets.titleEffectModal then
			announceWidgets.titleEffectModal:SetEffect(product.titleEffect or '')
		end
		ApplyProductTitleImage(product)
		ApplyProductDemoButton(product)

		SetupMarketplaceStageWidget(
			stageWidget,
			announceModelPanelModal,
			'marketplace_announce_stage_modal',
			'marketplace_announce_lighting_modal',
			product,
			true
		)
	end
end

local function ReplayModalModel()
	local product = GetActiveProduct()
	if not announceModelPanelModal then return end

	announceModelPanelModal:SetColor('1 1 1 0')
	announceModelPanelModal:SetAnim('')
	announceModelPanelModal:SetAnim('idle')
	announceModelPanelModal:SetAnimTime(0)
	if product then announceModelPanelModal:SetEffect(product.modalStoreEffect or product.storeEffect) end
end

local function HideMarketplaceAnnounce()
	Main.marketplaceAnnounceEnabled = false
	countdownToken = countdownToken + 1
	productRotationToken = productRotationToken + 1
	productRotationSuspended = false
	priceRequestToken = priceRequestToken + 1
	ModelPanelShared:ClearStageCache(stageCache)
	if Store and Store.HideAnnouncerFullscreenPreview then
		Store:HideAnnouncerFullscreenPreview()
	end

	local root = Main:GetWidget('marketplace_announce_root')
	if root then
		root:SetVisible(0)
	end
	ClearSwapEffect(announceWidgets.swapEffect)
	ClearSwapEffect(announceWidgets.swapEffectModal)

	local modalRoot = Main:GetWidget('marketplace_announce_modal_root')
	if modalRoot then
		modalRoot:SetVisible(0)
	end
end

local UpdateCountdown, UpdateAnnouncePrice, StartProductRotation

function MarketplaceAnnounce:ShowModal()
	if not productRotationSuspended then
		productRotationSuspended = true
		productRotationToken = productRotationToken + 1
	end

	ApplyProductText(GetActiveProduct())
	ApplyFeatureBadges()
	MarketplaceAnnounce:ApplyRarityTheme()
	SetupMarketplaceModalStage()
	ReplayModalModel()

	Main:GetWidget('marketplace_announce_modal_root'):SetVisible(1)

	if announceModelPanelModal then
		announceModelPanelModal:Sleep(MODEL_REVEAL_DELAY_MS, function()
			announceModelPanelModal:SetColor('1 1 1 1')
		end)
	end
end

function MarketplaceAnnounce:HideModal()
	local resumeProductRotation = productRotationSuspended
	productRotationSuspended = false

	if Store and Store.HideAnnouncerFullscreenPreview then
		Store:HideAnnouncerFullscreenPreview()
	end
	local modalRoot = Main:GetWidget('marketplace_announce_modal_root')
	if modalRoot then modalRoot:SetVisible(0) end

	if resumeProductRotation and Main.marketplaceAnnounceEnabled then
		StartProductRotation()
	end
end

function MarketplaceAnnounce:DemoAvatar()
	local product = GetActiveProduct()
	local slug = product and string.match(product.key, '^%w+%.([^%.]+)')
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
	SetSave('practice_avatar', product.key, 'string')

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
			if Testing.EntityIsHero(unit) then
				Testing.SetPlayerHero(owner, unit)
				Testing.Delete(entityId)
			else
				Testing.Delete(unit)
			end
		end)

		SelectAvatar(product.key, nil)
		Cmd('Action ToggleOverlayMenuGame')
	else
		PlayerHosted:CreatePracticeGame(gameVars)
	end
end

function MarketplaceAnnounce:DemoAnnouncer()
	local product = GetActiveProduct()
	local activation = GetProductActivation(product)
	local eventConfigs = StoreConfig and StoreConfig.ANNOUNCER_CFG
	if not (activation and activation.events and eventConfigs and Store and Store.ShowAnnouncerFullscreenPreview) then return end

	local availableKeys = {}
	for i = 1, #eventConfigs do
		local eventConfig = eventConfigs[i]
		if not eventConfig.audioOnly and activation.events[eventConfig.key] then
			tinsert(availableKeys, eventConfig.key)
		end
	end
	if #availableKeys == 0 then return end

	local eventIndex = _G.math.random(#availableKeys)
	if #availableKeys > 1 and availableKeys[eventIndex] == lastAnnouncerDemoKey then
		eventIndex = (eventIndex % #availableKeys) + 1
	end
	lastAnnouncerDemoKey = availableKeys[eventIndex]
	if Store:ShowAnnouncerFullscreenPreview(activation, lastAnnouncerDemoKey) then
		local previewRoot = Main:GetWidget('store_announcer_fullscreen_preview_root')
		if previewRoot then previewRoot:BringToFront() end
	end
end

function MarketplaceAnnounce:DemoProduct()
	local product = GetActiveProduct()
	if product and product.productType == 'announcer' then
		MarketplaceAnnounce:DemoAnnouncer()
	else
		MarketplaceAnnounce:DemoAvatar()
	end
end

function MarketplaceAnnounce:OpenProduct()
	local product = GetActiveProduct()
	local category = product and product.shopCategory and Enum.ShopCategory[product.shopCategory]
	if product then Store:OpenStoreToProduct(product.key, category) end
end

local function ActivateProduct(index, revealModel)
	activeProductIndex = index
	activeProduct = MARKETPLACE_PRODUCTS[activeProductIndex]
	if not activeProduct then
		HideMarketplaceAnnounce()
		return
	end

	ApplyProductText(activeProduct)
	ApplyFeatureBadges()
	SetupMarketplaceStage(revealModel)
	MarketplaceAnnounce:ApplyRarityTheme()
	UpdateAnnouncePrice()

	if announceWidgets.modalRoot and announceWidgets.modalRoot:IsVisible() ~= 0 then
		SetupMarketplaceModalStage()
		ReplayModalModel()
		if announceModelPanelModal then
			announceModelPanelModal:Sleep(MODEL_REVEAL_DELAY_MS, function()
				announceModelPanelModal:SetColor('1 1 1 1')
			end)
		end
	end

	countdownToken = countdownToken + 1
	if ProductShowsCountdown(activeProduct) then
		UpdateCountdown(countdownToken)
	end
end

local function ActivateNextProduct(revealModel, hideWhenMissing)
	local index = FindAvailableProductIndex(activeProductIndex + 1, activeProductIndex)
	if not index then
		if hideWhenMissing then HideMarketplaceAnnounce() end
		return false
	end

	ActivateProduct(index, revealModel)
	return true
end

local function ActivateNextProductWithEffect(revealModel, hideWhenMissing, token, onComplete)
	CacheMarketplaceWidgets()
	local effect = announceWidgets.swapEffect
	local modalEffect = announceWidgets.modalRoot and announceWidgets.modalRoot:IsVisible() ~= 0 and announceWidgets.swapEffectModal or nil
	local sleeper = effect or modalEffect
	if not sleeper then
		if onComplete then onComplete(ActivateNextProduct(revealModel, hideWhenMissing)) end
		return
	end

	PlaySwapEffect(effect)
	PlaySwapEffect(modalEffect)
	sleeper:Sleep(PRODUCT_SWAP_EFFECT_SWAP_MS, function()
		if token ~= productRotationToken or not Main.marketplaceAnnounceEnabled then
			ClearSwapEffect(effect)
			ClearSwapEffect(modalEffect)
			return
		end

		local changed = ActivateNextProduct(revealModel, hideWhenMissing)
		sleeper:Sleep(PRODUCT_SWAP_EFFECT_CLEAR_MS, function()
			ClearSwapEffect(effect)
			ClearSwapEffect(modalEffect)
		end)
		if onComplete then onComplete(changed) end
	end)
end

UpdateCountdown = function(token)
	if token ~= countdownToken then return end
	local product = GetActiveProduct()
	if not ProductShowsCountdown(product) then return end

	local now = GetHostUnixTime()
	if now >= product.countdownTargetUtc then
		ActivateNextProduct(true, true)
		return
	end
	if not CacheCountdownWidgets() then return end

	local remaining = product.countdownTargetUtc - now
	countdownValues[1]:SetText(format('%02d', floor(remaining / 86400)))
	countdownValues[2]:SetText(format('%02d', floor((remaining % 86400) / 3600)))
	countdownValues[3]:SetText(format('%02d', floor((remaining % 3600) / 60)))
	countdownValues[4]:SetText(format('%02d', remaining % 60))

	countdownValues[4]:Sleep(COUNTDOWN_TICK_MS, function() UpdateCountdown(token) end)
end

UpdateAnnouncePrice = function()
	local product = GetActiveProduct()
	if not product then return end

	priceRequestToken = priceRequestToken + 1
	local requestToken = priceRequestToken
	SetPurchaseState(false, '---')

	local entry = GetProductEntry(product)
	if not entry then return end

	local jadePrice = entry.purchaseOptions and entry.purchaseOptions.jades and entry.purchaseOptions.jades.price
	if jadePrice and jadePrice > 0 then
		SetPurchaseState(true, tostring(jadePrice))
	elseif ProductIsMarketable(product) and entry.productId and GetLowestListings then
		GetLowestListings({entry.productId}, function(result)
			if requestToken ~= priceRequestToken or GetActiveProduct() ~= product then return end
			local listing = result and result[1]
			local listingPrice = listing and tonumber(listing.amount)
			if listingPrice and listingPrice > 0 then
				SetPurchaseState(true, tostring(listingPrice))
			else
				SetPurchaseState(false, '---')
			end
		end)
	end
end

local function ScheduleProductRotation(token)
	if #MARKETPLACE_PRODUCTS < 2 or productRotationSuspended then return end
	CacheMarketplaceWidgets()
	if not announceWidgets.root then return end

	announceWidgets.root:Sleep(PRODUCT_ROTATE_MS, function()
		if token ~= productRotationToken or not Main.marketplaceAnnounceEnabled or productRotationSuspended then return end
		ActivateNextProductWithEffect(true, false, token, function(changed)
			if changed and token == productRotationToken and Main.marketplaceAnnounceEnabled and not productRotationSuspended then
				ScheduleProductRotation(token)
			end
		end)
	end)
end

StartProductRotation = function()
	if productRotationSuspended then return end
	productRotationToken = productRotationToken + 1
	ScheduleProductRotation(productRotationToken)
end

-----------------------------------------------
--					 Init					 --
-----------------------------------------------

local function SetupRegisters()
	if registersSetup then return end
	registersSetup = true
	interface:RegisterWatch('ShopProductsRefreshed', function()
		UpdateAnnouncePrice()
		MarketplaceAnnounce:ApplyRarityTheme()
	end)
end

local RARITY_GRADIENT_LABEL_NAMES = {
	'marketplace_announce_rarity_label', 'marketplace_announce_rarity_label_modal',
}

local RARITY_GRADIENT_START_COLOR = '#ffffff'
local RARITY_GRADIENT_END_COLOR   = '#5f2f0c'
local RARITY_GRADIENT_MID_POS     = 0.5

function MarketplaceAnnounce:ApplyRarityTheme()
	local product = GetActiveProduct()
	local entry = GetProductEntry(product)
	local rarity = entry and entry.rarity
	if not rarity or rarity == '' then rarity = product and product.rarity end
	if not rarity then return end
	rarity = string.lower(rarity)
	local theme = Store:GetRarityTheme(rarity)
	local hex = (theme and theme.border_color) or '#c87f15'
	if #hex == 9 then hex = hex:sub(1, 7) end

	for i = 1, #RARITY_GRADIENT_LABEL_NAMES do
		local w = Main:GetWidget(RARITY_GRADIENT_LABEL_NAMES[i])
		if w then
			w:SetGradientVertical(RARITY_GRADIENT_START_COLOR, RARITY_GRADIENT_END_COLOR)
			w:SetGradientMid(hex)
			w:SetGradientMidPos(RARITY_GRADIENT_MID_POS)
			w:SetText(rarity:upper())
		end
	end

end

function MarketplaceAnnounce:Init()
	WExt:ProcessInitWidgets(MarketplaceAnnounce, Main)

	ModelPanelShared:ClearStageCache(stageCache)
	announceStageWidget = nil
	announceAnnouncerStageWidget = nil
	announceModelPanel = nil
	announceStageWidgetModal = nil
	announceAnnouncerStageWidgetModal = nil
	announceModelPanelModal = nil
	announceWidgets = {}
	countdownValues = nil
	countdownUnits = nil
	countdownToken = countdownToken + 1
	productRotationToken = productRotationToken + 1
	productRotationSuspended = false
	priceRequestToken = priceRequestToken + 1
	lastAnnouncerDemoKey = nil
	activeProductIndex = FindAvailableProductIndex(1) or 1
	activeProduct = MARKETPLACE_PRODUCTS[activeProductIndex]

	Main.marketplaceAnnounceEnabled = false

	local root = Main:GetWidget('marketplace_announce_root')
	if not root then return end

	root:SetVisible(0)
	root:Sleep(CLIENT_LOAD_DELAY_MS, function()
		local firstAvailableIndex = FindAvailableProductIndex(activeProductIndex)
		if not firstAvailableIndex then
			HideMarketplaceAnnounce()
			return
		end

		Main.marketplaceAnnounceEnabled = true
		SetupRegisters()
		ActivateProduct(firstAvailableIndex, true)
		StartProductRotation()

		if (Main.IsPanelOpen and Main:IsPanelOpen('motd')) or not (Main.FSPanelActive and Main:FSPanelActive()) then
			root:SetVisible(1)
		end
	end)
end
