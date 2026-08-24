----------------------------------------------------------
--	Name:		Game Shop HD Script						--
--	(C) 2025 Juvio, LLC									--
----------------------------------------------------------
local _G = getfenv(0)
local interface = object
local interfaceName = object:GetName()

ShopHD = _G['ShopHD'] or {}

local ipairs, pairs, select, string, table, next, type, unpack, tinsert, tconcat, tremove, format, tostring, 
tonumber, tsort, ceil, floor, sub, find, gfind = _G.ipairs, _G.pairs, _G.select, _G.string, _G.table, _G.next, 
_G.type, _G.unpack, _G.table.insert, _G.table.concat, _G.table.remove, _G.string.format, _G.tostring, _G.tonumber, 
_G.table.sort, _G.math.ceil, _G.math.floor, _G.string.sub, _G.string.find, _G.string.gfind

----------------------------------------------------------
--						INTERNAL						--
----------------------------------------------------------

local function GetWidgetShop(widget, fromInterface, hideErrors)

	if (widget) then
		local returnWidget
		if (fromInterface) then
			returnWidget = UIManager.GetInterface(fromInterface):GetWidget(widget)
		else
			returnWidget = interface:GetWidget(widget)
		end	
		if (returnWidget) then
			return returnWidget
		else
			if (not hideErrors) then println('GetWidget failed to find ' .. tostring(widget) .. ' in interface ' .. tostring(fromInterface)) end
			return nil		
		end	
	else
		println('GetWidget called without a target')
		return nil
	end
end

local GetWidget = GetWidgetShop
local GetWidgetMem = memoizeObject(GetWidgetShop)

function ShopHD:GetWidget(name)
	return GetWidgetShop(name)
end

function ShopHD:GetObjectName()
	return 'ShopHD'
end

----------------------------------------------------------
--						VARIABLES						--
----------------------------------------------------------

-- local widgets
ShopHD.rootPanel = GetWidgetMem('shop_root')
ShopHD.sleeper = GetWidgetMem('shop_dummy')
ShopHD.shopRightRoot = GetWidgetMem('shop_right_root')
ShopHD.leftCategoriesRootPanel = GetWidgetMem('shop_left_categories_root')
ShopHD.searchBox = GetWidgetMem('shop_search_entry')
ShopHD.searchHotkeyBox = GetWidgetMem('shop_search_entry_focus_key')
ShopHD.searchHotkey = GetWidgetMem('shop_search_entry_focus_key_label')
ShopHD.recipePanel = GetWidgetMem('shop_recipetree_panel')

ShopHD.tipContainer = GetWidgetMem('shop_tip_generic')
ShopHD.tipLabel = GetWidgetMem('shop_tip_generic_label')
ShopHD.shopHotkeyTip = GetWidgetMem('shop_controls_full')
ShopHD.shopSearchPlaceholder = GetWidgetMem('shop_search_placeholder')

ShopHD.body = GetWidgetMem('shop_body')
ShopHD.itemScrollBar = GetWidgetMem('shop_items_scrollbar')
ShopHD.categorySideListPanel = GetWidgetMem('shop_side_cat_panel')
ShopHD.itemCenterScrollPanel = GetWidgetMem('shop_center_item_scroll_panel')
ShopHD.shopQuickBuyRoot = GetWidgetMem('shop_quickbuy')
ShopHD.quickBuyToggleImg_On = GetWidgetMem('shop_hidequickbuy_toggle_img_on')
ShopHD.quickBuyToggleImg_Off = GetWidgetMem('shop_hidequickbuy_toggle_img_off')
ShopHD.subCategoriesRoot = GetWidgetMem('shop_right_subcategories_root')
ShopHD.rightItemsRootPanel = GetWidgetMem('shop_right_items_root')
ShopHD.recommendedRoot = GetWidgetMem('shop_right_recommended_root')
ShopHD.shopDropdownRoot = GetWidgetMem('shop_search_dropdown_root')
ShopHD.searchFocusKey = GetWidgetMem('shop_search_entry_focus_key')
ShopHD.guideMapFiltersRoot = GetWidgetMem('shop_guide_map_filters_root')
ShopHD.keybindsToggleImg_On = GetWidgetMem('shop_keybinds_toggle_img_on')
ShopHD.keybindsToggleImg_Off = GetWidgetMem('shop_keybinds_toggle_img_off')
ShopHD.shopLayoutToggleImg_On = GetWidgetMem('shop_shoplayout_toggle_img_on')
ShopHD.shopLayoutToggleImg_Off = GetWidgetMem('shop_shoplayout_toggle_img_off')
ShopHD.sortByPanel = GetWidgetMem('shop_sort_by_panel')
ShopHD.guideRoleFiltersRoot = GetWidgetMem('shop_guide_role_filters_root')
ShopHD.guideSortDropdown = GetWidgetMem('shop_section_guide_sortdropdown')
ShopHD.guideSearchEntry = GetWidgetMem('shop_guide_search_entry')
ShopHD.guideSearchPlaceholder = GetWidgetMem('shop_guide_search_placeholder')

ShopHD.recommendedCat1 = GetWidgetMem('shop_recommended_1')
ShopHD.recommendedCat2 = GetWidgetMem('shop_recommended_2')
ShopHD.recommendedCat3 = GetWidgetMem('shop_recommended_3')
ShopHD.recommendedCat4 = GetWidgetMem('shop_recommended_4')

ShopHD.recommendedEmpty1 = GetWidgetMem('shop_recommended_empties_1')
ShopHD.recommendedEmpty2 = GetWidgetMem('shop_recommended_empties_2')
ShopHD.recommendedEmpty3 = GetWidgetMem('shop_recommended_empties_3')
ShopHD.recommendedEmpty4 = GetWidgetMem('shop_recommended_empties_4')

ShopHD.pinnedItemsRoot = GetWidgetMem('shop_pinned_items_root')
ShopHD.outerRightSideRoot = GetWidgetMem('shop_section_rightside_root')
ShopHD.recommendedInstancesRoot = GetWidgetMem('shop_recommended_items_instances_root')
ShopHD.scrollableRoot = GetWidgetMem('shop_scrollable_root')

ShopHD.guideListbox = GetWidgetMem('shop_guide_listbox')
ShopHD.guideListboxScrollbar = GetWidget('shop_guide_listbox_vscroll')
ShopHD.guideAbilitiesPanel = GetWidgetMem('shop_guide_abilities_panel')
ShopHD.guideNameLabel = GetWidgetMem('shop_guide_name_label')
ShopHD.guideNameRoot = GetWidgetMem('shop_guide_name_root')
ShopHD.guideVoteButtonsRoot = GetWidgetMem('shop_guide_vote_buttons_root')
ShopHD.autoLevelCheckbox = GetWidgetMem('shop_auto_level_checkbox')
ShopHD.guideSelectorRoot = GetWidgetMem('shop_section_guide_selector')

ShopHD.guideEquippedHoverRoot = GetWidgetMem('shop_guide_equipped_hover_root')
ShopHD.guideEquippedRootPanel = GetWidgetMem('shop_guide_equipped_rootpanel')
ShopHD.guideEquippedName = GetWidgetMem('shop_guide_instance_name_equipped')
ShopHD.guideEquippedAuthor = GetWidgetMem('shop_guide_instance_author_equipped')
ShopHD.guideEquippedApproval = GetWidgetMem('shop_guide_instance_approval_equipped')
ShopHD.guideEquippedVersion = GetWidgetMem('shop_guide_instance_version_equipped')
ShopHD.guideEquippedUpdated = GetWidgetMem('shop_guide_instance_updated_equipped')
ShopHD.guideEquippedMapIcon = GetWidgetMem('shop_guide_instance_mapicon_equipped')
ShopHD.guideEquippedRoleIcon = GetWidgetMem('shop_guide_instance_roleicon_equipped')
ShopHD.guideHeaderUpvoteBtn = GetWidgetMem('shop_guide_instance_upvote_equiped')
ShopHD.guideHeaderDownvoteBtn = GetWidgetMem('shop_guide_instance_downvote_equiped')

ShopHD.guideSelectorToggleRoot = GetWidgetMem('shop_guide_selector_toggle_root')
ShopHD.guideSelectorToggleImg_On = GetWidgetMem('shop_guide_selector_toggle_img_on')
ShopHD.guideSelectorToggleImg_Off = GetWidgetMem('shop_guide_selector_toggle_img_off')

-----------

-- legacy shop widgets
if GetCvarBool('cg_useClassicShop') then

	ShopHD.sectionHeaderFrame = GetWidgetMem('shop_section_header_frame')
	ShopHD.bodyFrame = GetWidgetMem('shop_body_frame')
	ShopHD.shopItemsPanel = GetWidgetMem('shop_items')
	ShopHD.legacyGuideDropdown = GetWidgetMem('shop_legacy_guide_dropdown')
	ShopHD.legacyGuideDropdownListbox = GetWidgetMem('shop_legacy_guide_dropdown_listbox')
	ShopHD.legacyGuideDropdownScrollbar = GetWidgetMem('shop_legacy_guide_dropdown_listbox_vscroll')
	ShopHD.legacyGuideDescription = GetWidgetMem('shop_legacy_guide_description')
	ShopHD.guideApprovalBottom = GetWidgetMem('shop_guide_approval_bottom')

	ShopHD.recipeTreeLeftStick = GetWidgetMem('shop_recipe_tree_left_stick')
	ShopHD.recipeTreeRightStick = GetWidgetMem('shop_recipe_tree_right_stick')
	ShopHD.recipeTreeLeftStickRoot = GetWidgetMem('shop_recipe_tree_left_stick_root')
	ShopHD.recipeTreeRightStickRoot = GetWidgetMem('shop_recipe_tree_right_stick_root')
	ShopHD.recipeLeftHeader = GetWidgetMem('shop_recipe_left_header')
	ShopHD.recipeRightHeader = GetWidgetMem('shop_recipe_right_header')
	ShopHD.buyRemainingBtnLabel = GetWidgetMem('shop_buyremaining_btn_label')
	ShopHD.focusedItemNameLabel = GetWidgetMem('shop_focused_item_name')
	ShopHD.focusedItemCostLabel = GetWidgetMem('shop_focused_item_cost')

	ShopHD.recipePanelGeneral = GetWidgetMem('shop_recipe_panel_general')
	ShopHD.recipePanelWide = GetWidgetMem('shop_recipe_panel_wide')
	ShopHD.buildsIntoWidePanel = GetWidgetMem('shop_buildsinto_wide_panel')
	ShopHD.wideFocusedItemNameLabel = GetWidgetMem('shop_wide_focused_item_name')
	ShopHD.wideFocusedItemCostLabel = GetWidgetMem('shop_wide_focused_item_cost')

	ShopHD.recommendedBtmArea = GetWidgetMem('shop_recommended_bottom_area')

	ShopHD.requiredLvl2Panels = 
	{
		GetWidgetMem('shop_required_lvl2_panel_1'),
		GetWidgetMem('shop_required_lvl2_panel_2'),
		GetWidgetMem('shop_required_lvl2_panel_3'),
		GetWidgetMem('shop_required_lvl2_panel_4'),
	}

	ShopHD.buildsIntoLvl2Panels = 
	{
		GetWidgetMem('shop_builds_into_lvl2_panel_1'),
		GetWidgetMem('shop_builds_into_lvl2_panel_2'),
		GetWidgetMem('shop_builds_into_lvl2_panel_3'),
		GetWidgetMem('shop_builds_into_lvl2_panel_4'),
	}

	ShopHD.buildsIntoItemListPanels = 
	{
		GetWidgetMem('shop_builds_into_itemlist_panel_1'),
		GetWidgetMem('shop_builds_into_itemlist_panel_2'),
		GetWidgetMem('shop_builds_into_itemlist_panel_3'),
		GetWidgetMem('shop_builds_into_itemlist_panel_4'),
	}

	ShopHD.requiredItemListPanels = 
	{
		GetWidgetMem('shop_required_itemlist_panel_1'),
		GetWidgetMem('shop_required_itemlist_panel_2'),
		GetWidgetMem('shop_required_itemlist_panel_3'),
		GetWidgetMem('shop_required_itemlist_panel_4'),
	}
end

-- new shop widgets
if not GetCvarBool('cg_useClassicShop') then
	ShopHD.requiredItemListPanel = GetWidgetMem('shop_required_itemlist_panel')
	ShopHD.buildsIntoItemListPanel = GetWidgetMem('shop_builds_into_itemlist_panel')
end

-----------

ShopHD.chatInput = GameChat:GetWidgetMem('game_textbox_frame')

local courierLabelWidget = nil

local gameServerPhases = GetGameServerPhases() -- 0 -> IDLE, 1 -> WAITINGFORPLAYERS, 2 -> PREGAME, 3 -> INGAME, 4 -> POSTGAME, 5 -> FINISHED
local currGameServerPhase = 0

-- Arrays/Tables
ShopHD.ItemCur = {}
ShopHD.itemObjectTable = { focused = {} }
ShopHD.equippedGuide = nil
ShopHD.foundGuides = {}

ShopHD.searchLabels = {}

-- Shop skins for different contexts
ShopHD.courierStatusTipSkin = ShopHD.courierStatusTipSkin or 
{
	inventory_shop = { text = 'Этот купленный товар отправляется в рюкзак.', color = '0 1 0 1' },
	courier_shop = { text = 'Купленный предмет будет помещён в тайник курьера.', color = '0 1 1 1' },
	cant_shop = { text = 'Невозможно совершить покупку: курьер вне зоны действия', color = '1 0 0 1' },
}

local playerItems = {}

-- Strings
ShopHD.leftCurrentTab = ''
ShopHD.currentHeroName = ''
ShopHD.currentHeroNameForRecommended = ''
ShopHD.filterText = ''
ShopHD.searchText = ''
ShopHD.shopAccess = ''

-- Numbers
local playerGold = 0
ShopHD.courier_status = 0
ShopHD.recipePanelInner_W = 0
ShopHD.itemPanelBase_H = 0
--ShopHD.treeShopFrame_W = 0
ShopHD.recipeIndex = 1

-- Bools
local textboxSleeping = false
local canShop = false
local overrideDefaultTab = false

------------------------------
--			 Code			--
------------------------------

local function UpdateUIOpacity()
	local opacity = math.max(0.1, math.min(1, tonumber(ShopShared.shopSaveData.miscDefaults.opacity) or 1))
	Trigger('Shop_Opacity', tostring(opacity))
end

function ShopHD:SetOpacity(widget, updateColor, updateBorder)
	if not widget then return end

	local opacity = math.max(0.1, math.min(1, tonumber(ShopShared.shopSaveData.miscDefaults.opacity) or 1))

	if AtoB(updateColor) then
		local r, g, b = widget:GetBaseColor()
		if r ~= nil and g ~= nil and b ~= nil then
			widget:SetColor(r .. ' ' .. g .. ' ' .. b .. ' ' .. opacity)
		end
	end

	if AtoB(updateBorder) then
		local br, bg, bb = widget:GetBaseBorderColor()
		if br ~= nil and bg ~= nil and bb ~= nil then
			widget:SetBorderColor(br .. ' ' .. bg .. ' ' .. bb .. ' ' .. opacity)
		end
	end
end

local function ProcessItemCostWidgets(itemObj)
	
	local itemData = itemObj.itemData
	if not itemData or not itemData.itemDef then return end

	local costToCompare = GetRemainingCost(itemData.itemDef)

	-- Determine the color style based on affordability
	local colorKey
	if costToCompare > playerGold then
		colorKey = 'expensive'
	elseif itemData.IsRecipe or itemObj.isScroll then -- Treat scrolls visually like recipes (yellow border) when affordable
		colorKey = 'affordableRecipe'
	else
		colorKey = 'affordableBasic'
	end

	local colors = ShopShared.itemCostColors[colorKey]

	-- Apply colors to border and icon (applies to all item types)
	itemObj.border:SetColor(colors.borderColor)
	itemObj.itemIcon:SetColor(colors.iconColor)

	if itemObj.itemType ~= 'focused' then
		itemObj.costLabel:SetColor(colors.costLabelColor)
		itemObj.recipeIcon:SetColor(colors.recipeIconColor)
	end
end

local function UpdateCurrentFocusPanel()
	ShopHD.sleeper:Sleep(1, function()
		
		ShopHD:UpdatePlayerItems()
		ShopHD:MarkItemCategoryOwnedItems('required')
		ShopHD:ItemCostUpdate(ShopHD)
		ShopShared:UpdateHotkeys(ShopHD)

		if next(ShopHD.itemObjectTable.focused[0].itemData) ~= nil and ShopShared:FindBestRecipe(ShopHD.itemObjectTable.focused[0].itemData) ~= ShopHD.recipeIndex then
			ShopHD:FillRecipePanel(ShopHD.itemObjectTable.focused[0].itemData, '', true)
		end

	end)
end

local function ToggleShopVisibility(visible)

	local function SetDefaultTab()
		for key, value in pairs(ShopShared.leftCategoryTypes) do
			if value.enabled and value.defaultIfAccessible and ShopHD.shopAccess:find(key) then
				return key
			end
		end
		return ShopShared:GetDefaultTab(ShopHD)
	end

	ShopHD.rootPanel:SetVisible(visible and 1 or 0)

	if visible then
		if overrideDefaultTab == false then
			ShopShared:SetLeftCategoryTab(SetDefaultTab(), true, ShopHD)
		end

		ShopShared:UpdateHotkeys(ShopHD)
		ShopHD.searchBox:SetFocus(ShopShared.shopSaveData.miscDefaults.alwaysSearch)

		ShopGuides:ProcessRecommendedCategory()

	else

		ShopHD.searchText = ''
		ShopShared:ClearSearch(ShopHD)
		ShopGuides:ClearPreviewState()
		ShopGuides:ClearSearch(false) -- Clear guide search on shop close (no refresh needed)

		-- hide focus panel on close if legacy shop
		if ShopHD.activeShopLayout == 'legacy' then
			ShopHD.recipePanel:SetVisible(0)
		end
	end

	overrideDefaultTab = false
end

function ShopHD:MarkItemCategoryOwnedItems(categoryName)

	-- gather item counts from player's inventory once, separate counts for scrolls.
	local itemCountsInInventory = {}
	local scrollCountsInInventory = {}

	for _, item in ipairs(playerItems) do

		local itemName = item.itemDef:GetName()

		if item.isRecipeScroll then -- the isRecipeScroll is exclusively from GetMyItems()
			scrollCountsInInventory[itemName] = (scrollCountsInInventory[itemName] or 0) + 1
		else
			itemCountsInInventory[itemName] = (itemCountsInInventory[itemName] or 0) + 1
		end

	end

	-- prepare sorted list with item objects (for consistent order)
	local itemsToMark = self.itemObjectTable[categoryName] or {}
	local sortedItemsToMark = {}

	for index, itemObj in pairs(itemsToMark) do
		if itemObj and itemObj.itemData then
			table.insert(sortedItemsToMark, {index = index, itemObj = itemObj})
		end
	end

	table.sort(sortedItemsToMark, function(a, b) return a.index < b.index end)

	-- mark/unmark items based on inventory count.
	for _, item in ipairs(sortedItemsToMark) do

		local itemObj = item.itemObj
		local itemName = itemObj.itemData.Name
		local isScrollComponent = itemObj.isScroll -- is dummy scroll thing
		local owned
		
		-- check if a scroll component 'n handle separately
		if isScrollComponent then

			owned = scrollCountsInInventory[itemName] and scrollCountsInInventory[itemName] > 0

			if owned then 
				-- decrease count specifically from scrolls count
				scrollCountsInInventory[itemName] = scrollCountsInInventory[itemName] - 1
			end

		else

			owned = itemCountsInInventory[itemName] and itemCountsInInventory[itemName] > 0

			if owned then 
				-- decrease count from general item count
				itemCountsInInventory[itemName] = itemCountsInInventory[itemName] - 1
			end

		end

		itemObj.ownedLabel:SetVisible(owned and 1 or 0)
		itemObj.ownedMark:SetVisible(owned and 1 or 0)
		itemObj.costLabel:SetVisible(not owned and 1 or 0)
	end
end

function ShopHD:UpdatePlayerItems()
	playerItems = {}  -- Reset the playerItems table
	for i, itemDetail in ipairs(GetMyItems()) do
		local item = {
			itemDef = itemDetail.itemDef,
			isRecipeScroll = itemDetail.isScroll
		}
		table.insert(playerItems, item)
	end
end

function ShopHD:ItemCostUpdate()

	if(self.rootPanel:IsVisible()) then
		
		ShopShared:RunActionOnItems(ShopHD, ProcessItemCostWidgets, 
			'all', 'consumable', 'ward', 'category', 'pinned', 'recommended1', 'recommended2', 'recommended3', 'recommended4'
		)

		if self.recipePanel:IsVisible() then
			ShopShared:RunActionOnItems(ShopHD, ProcessItemCostWidgets, 
				'required', 'buildsinto', 'focused', 'pinned', 'recommended1', 'recommended2', 'recommended3', 'recommended4',
				'requiredlvl2', 'buildsintolvl2'
			)
		end
		
	end

end

local function SetCourierTipPositions(tipWidget, courierTipWidget)

	local shopTipWidget = GetWidget('shop_global_item_tooltip', 'game')
	local courierTipWidget = GetWidget('courier_status_tooltip', 'game')

	local padding = 5
	local tipContentsWidget = shopTipWidget:GetChildren()[1]
	local calculatedCourierY = shopTipWidget:GetAbsoluteY() + tipContentsWidget:GetHeight() + padding

	courierTipWidget:SetAbsoluteX(shopTipWidget:GetAbsoluteX())
	courierTipWidget:SetAbsoluteY(calculatedCourierY)
end

function ShopHD:ShowShopTooltip(show, widget, name, icon, isScroll)

	local shopTipWidget = GetWidget('shop_global_item_tooltip', 'game')
	local courierTipWidget = GetWidget('courier_status_tooltip', 'game')

	local tipContentsWidget = shopTipWidget:GetChildren()[1]

	local offset_x = GetHeightFromString('3.5h')
	local offset_y = GetHeightFromString('0h')

	if show then

		TriggerItemTooltip('Shop_GlobalItemTrigger', name or '', isScroll and true or false)

		if icon then
			UITrigger.GetTrigger('Shop_GlobalItemIconTrigger'):Trigger(icon)
		end

		Tooltips:SetTipHoverPositions(widget, shopTipWidget, tipContentsWidget, offset_x, offset_y)
		
		SetCourierTipPositions(shopTipWidget, courierTipWidget)

		shopTipWidget:SetVisible(1)
		courierTipWidget:SetVisible(1)

	else
		shopTipWidget:SetVisible(0)
		courierTipWidget:SetVisible(0)
	end
end

local function SetCourierTooltipSkin(status)

	local function RunSkinLogic()
		if ShopHD.courierStatusTipSkin[status] then
			courierLabelWidget:SetText(ShopHD.courierStatusTipSkin[status].text)
			courierLabelWidget:SetColor(ShopHD.courierStatusTipSkin[status].color)
		end
	
		SetCourierTipPositions()
	end

	if courierLabelWidget == nil then
		ShopHD.sleeper:Sleep(1, function()
			courierLabelWidget = GetWidget('courier_status_tooltip_label', 'game')
			RunSkinLogic()
		end)
	else
		RunSkinLogic()
	end

end

local function CalculateCourierStatus()

	local skin = 'cant_shop' -- default skin

	if ShopHD.shopAccess ~= '' then
		skin = 'inventory_shop'
	elseif ShopHD.courier_status < 3 then
		skin = 'courier_shop'
	end

	SetCourierTooltipSkin(skin)
end

function ShopHD:UpdateShopGuideVisibility(recipePanelShowing)
	if recipePanelShowing == nil then
		recipePanelShowing = ShopHD.recipePanel:IsVisible()
	end
	
	local isRecommendedTab = ShopShared:IsRecommendedTab(ShopHD)
	local showGuideUI = isRecommendedTab and not recipePanelShowing
	
	if showGuideUI then
		ShopHD.outerRightSideRoot:FadeIn(200)
	else
		ShopHD.outerRightSideRoot:FadeOut(100)
	end
	
	if isRecommendedTab then
		ShopHD.guideSelectorToggleRoot:FadeIn(200)
	else
		ShopHD.guideSelectorToggleRoot:FadeOut(100)
	end
	
	-- when hiding guide view, update toggle to "Show guides" state and close selector
	if not showGuideUI then
		ShopHD.guideSelectorToggleImg_On:SetVisible(0)
		ShopHD.guideSelectorToggleImg_Off:SetVisible(1)
		ShopHD.guideSelectorRoot:SetVisible(0)
	end

	if ShopHD.recommendedBtmArea and isRecommendedTab then
		if recipePanelShowing then
			ShopHD.recommendedBtmArea:FadeOut(200)
		else
			ShopHD.recommendedBtmArea:FadeIn(200)
		end
	end
end

function ShopHD:ToggleQuickBuyHide(setVisibilityFromDefault)
	if not setVisibilityFromDefault then
		ShopShared.shopSaveData.miscDefaults.quickBuyHidden = 
			(ShopShared.shopSaveData.miscDefaults.quickBuyHidden == 1) and 0 or 1
		
		ShopShared:FlushShopSaveData()
	end
	
	local isHidden = (ShopShared.shopSaveData.miscDefaults.quickBuyHidden == 1)
	
	ShopHD.quickBuyToggleImg_On:SetVisible(not isHidden and 1 or 0)
	ShopHD.quickBuyToggleImg_Off:SetVisible(isHidden and 1 or 0)
	ShopHD.shopQuickBuyRoot:SetVisible(not isHidden and 1 or 0)
end

function ShopHD:ToggleShopKeybinds(setVisibilityFromDefault)
	if not setVisibilityFromDefault then
		local current = GetCvarBool('cg_useShopKeybinds')
		Set('cg_useShopKeybinds', current and 'false' or 'true')
	end
	
	local isEnabled = GetCvarBool('cg_useShopKeybinds')
	
	ShopHD.keybindsToggleImg_On:SetVisible(isEnabled and 1 or 0)
	ShopHD.keybindsToggleImg_Off:SetVisible(not isEnabled and 1 or 0)
	ShopShared:UpdateHotkeys(ShopHD)
end

function ShopHD:ToggleShopLayout(setVisibilityFromDefault)
	if not setVisibilityFromDefault then
		local current = GetCvarBool('cg_useAdvancedShopCategories')
		Set('cg_useAdvancedShopCategories', current and 'false' or 'true')
		ShopShared:SetLeftCategoryTab('recommended', true, ShopHD)
		ShopShared:RebuildCategoryTabs(ShopHD)
	end

	local useNewShop = GetCvarBool('cg_useAdvancedShopCategories')
	ShopHD.activeShopLayout = useNewShop and 'basic' or 'legacy'

	ShopHD.shopLayoutToggleImg_On:SetVisible(not useNewShop and 1 or 0)
	ShopHD.shopLayoutToggleImg_Off:SetVisible(useNewShop and 1 or 0)

	-- sort toggle hidden for legacy mode
	ShopHD.sortByPanel:SetVisible(useNewShop and 1 or 0)
end

function ShopHD:SetFocusRecipeCoverHeight(widget)

	local totalHeight = 0
	local children = self.requiredItemListPanel:GetChildren()

	for _, child in ipairs(children) do
		totalHeight = totalHeight + child:GetHeight()
	end
	
	local requiredBaseFramePanel = widget:GetWidget('required_baseframe')
	if requiredBaseFramePanel then
		requiredBaseFramePanel:SetVisible(totalHeight > 0)
	end

	widget:SetHeight(totalHeight)
end

function ShopHD:SetupDraggableItem(object, widget, itemType, id)

	-- called when widget is made, handles draggable items
	local originPinnedSlot = nil
	local originPinnedData = nil

	local function ToggleHighlights(state)
		ShopShared:RunActionOnItems(object, function(itemObj)
			if itemObj.highlight then
				itemObj.highlight:SetVisible(state)
			end
		end, 'pinned')
	end

	-- updates pinned slot
	local function UpdatePinnedSlot(pinObj, itemData)
		pinObj.itemData = itemData
		local isBlank = (itemData.Name == '')
		pinObj.emptyPin:SetVisible(isBlank and 1 or 0)
		pinObj.filledPin:SetVisible(isBlank and 0 or 1)
		
		ShopShared:PopulateItem(pinObj, object)
		object:ItemCostUpdate()
	end

	-- saves pinned item state per hero
	local function SavePinnedState(pins)

		local heroName = GetViewHeroName() or ''
		local pinned = ShopShared.shopSaveData.pinnedItems or {}
		pinned[heroName] = pinned[heroName] or {}

		for i=0, ShopShared:GetNumPinnedItems(object)-1 do
			local pinObj = pins[i]
			pinned[heroName][i] = pinObj.itemData.Name or ''
		end

		ShopShared.shopSaveData.pinnedItems = pinned
		ShopShared:FlushShopSaveData()
	end

	-- gets hovered pin slot
	local function GetHoveredPinSlot(pins)
		for i=0, ShopShared:GetNumPinnedItems(object)-1 do

			local pinObj = pins[i]

			if pinObj.emptyPin and IsInputCursorInsideWidget(pinObj.emptyPin) then
				return i, pinObj
			end

			if pinObj.filledPin and IsInputCursorInsideWidget(pinObj.filledPin) then
				return i, pinObj
			end

		end
		return nil, nil
	end

	-- drops dragged item onto pin if available
	local function DropOnPin(data)
		local pins = object.itemObjectTable['pinned']

		if originPinnedSlot then

			local hoveredPinId, hoveredPinObj = GetHoveredPinSlot(pins)

			if hoveredPinId then
				-- swapping if needed
				if hoveredPinObj.emptyPin:IsVisible() == 1 then

					-- empty slot found, move dragged item there
					UpdatePinnedSlot(hoveredPinObj, originPinnedData)
					UpdatePinnedSlot(pins[originPinnedSlot], ShopShared:BuildBlankItemData())
					SavePinnedState(pins)

				else

					-- slot occupied, swap items
					local hoveredData = hoveredPinObj.itemData

					UpdatePinnedSlot(hoveredPinObj, originPinnedData)
					UpdatePinnedSlot(pins[originPinnedSlot], hoveredData)
					SavePinnedState(pins)

				end
			else
				-- user didn't drop on any pinned slot, clear the origin pinned item
				UpdatePinnedSlot(pins[originPinnedSlot], ShopShared:BuildBlankItemData())
				SavePinnedState(pins)
			end
		else
			-- dragging from a non-pin slot item, try to place it in an empty pin slot
			for i=0, ShopShared:GetNumPinnedItems(object)-1 do

				local pinObj = pins[i]

				if pinObj.emptyPin and IsInputCursorInsideWidget(pinObj.emptyPin) then
					UpdatePinnedSlot(pinObj, data)
					SavePinnedState(pins)
					break
				end

			end
		end
	end

	-- start dragging
	local function MouseStartDrag()

		ToggleHighlights(1)

		-- if dragging from a pinned slot, store its slot and data
		if itemType == 'pinned' then
			originPinnedSlot = tonumber(id)
			originPinnedData = object.itemObjectTable['pinned'][originPinnedSlot].itemData
		else
			originPinnedData = object.itemObjectTable[itemType][tonumber(id)].itemData
		end

	end

	-- end dragging and attempt to drop
	local function MouseEndDrag()
		ToggleHighlights(0)
		DropOnPin(originPinnedData)
		originPinnedSlot = nil
		originPinnedData = nil
	end

	widget:SetCallback('onstartdrag', MouseStartDrag)
	widget:SetCallback('onenddrag', MouseEndDrag)

end

function ShopHD:CheckForDragOverPin(widget)
	if IsInputCursorInsideWidget(widget) then
		widget:SetColor('#ffffff')
	else
		widget:SetColor('invisible')
	end
end

function ShopHD:PopulatePinnedItems(shopActive)

	-- abort if shop isn't open
	if not shopActive then return false end

	local heroName = GetViewHeroName() or ''

	-- clear pinned items
	local function ResetPinnedSlots()
		for i=0, ShopShared:GetNumPinnedItems(self)-1 do

			local pinObj = self.itemObjectTable['pinned'][i]

			pinObj.itemData = ShopShared:BuildBlankItemData()
			pinObj.emptyPin:SetVisible(1)
			pinObj.filledPin:SetVisible(0)
			ShopShared:PopulateItem(pinObj, self)

		end
	end

	-- load pinned items assigned to a specific hero
	local function LoadPinnedItemsForHero(heroName)
		ResetPinnedSlots()

		local pinned = ShopShared.shopSaveData.pinnedItems or {}
		pinned[heroName] = pinned[heroName] or {}

		-- check if hero was never initialized
		if not pinned[heroName]._initialized then
			pinned[heroName]._initialized = true

			for slotIndex, defaultItem in ipairs(ShopShared.defaultPinnedItems) do

				if slotIndex-1 < ShopShared:GetNumPinnedItems(self) then
					pinned[heroName][slotIndex-1] = defaultItem
				end

			end

			ShopShared.shopSaveData.pinnedItems = pinned
			ShopShared:FlushShopSaveData()
		end

		for i=0, ShopShared:GetNumPinnedItems(self)-1 do

			local pinObj = self.itemObjectTable['pinned'][i]
			local savedItemName = pinned[heroName][i] or ''

			if savedItemName ~= '' then

				-- load the saved item
				local itemDef = HoN.GetItemDefinition(savedItemName)

				if itemDef then
					pinObj.itemData = ShopShared:BuildItemDataFromComponent(itemDef)
					pinObj.emptyPin:SetVisible(0)
					pinObj.filledPin:SetVisible(1)
					ShopShared:PopulateItem(pinObj, self)
				end
			end
		end
	end

	self.currentHeroName = heroName
	LoadPinnedItemsForHero(heroName)

	-- update item costs based on current gold
	self:ItemCostUpdate()

end

function ShopHD:ToggleSetting(widget, init, dataKey, executeExtraAction)
	if init then
		widget:SetButtonState(ShopShared.shopSaveData.miscDefaults[dataKey] or 0)
	else
		ShopShared.shopSaveData.miscDefaults[dataKey] = ShopShared.shopSaveData.miscDefaults[dataKey] == 0 and 1 or 0
		ShopShared:FlushShopSaveData()
		if executeExtraAction then executeExtraAction() end
	end
end

function ShopHD:SetRecipeIndex(index)
	self.recipeIndex = index
end

local function SelectRecipePanelVariant(panelsArray, count)
	-- show correct panel variant (1-4) for item count & hides rest
	local index = math.min(math.max(count, 1), 4)
	for i = 1, 4 do
		panelsArray[i]:SetVisible(0)
	end
	panelsArray[index]:SetVisible(1)
	return panelsArray[index]
end

local function ClearAllPanelVariants(panelsArray, object, itemType)
	if not panelsArray then return end
	for i = 1, 4 do
		if panelsArray[i] then
			for _, child in pairs(panelsArray[i]:GetChildren()) do
				child:Destroy()
			end
			panelsArray[i]:SetVisible(0)
		end
	end
	object.itemObjectTable[itemType] = {}
end

function ShopHD:SpawnLvl2(lvl1Type, lvl2Type, getSubItemsFn)
	ShopShared:ClearItemPanel(self, lvl2Type)

	local cfg = ShopShared.itemObjectCfg[lvl2Type]
	if not cfg then return end

	local lvl2Panel = cfg.hostPanel(self)
	if not lvl2Panel then return end

	local globalId = 0
	local lvl1Items = self.itemObjectTable[lvl1Type] or {}
	local i = 0

	while lvl1Items[i] do
		local subItems, scrollIndex = getSubItemsFn(lvl1Items[i])

		-- Spawn list container (even if empty, for alignment with LVL1)
		local listWidget = lvl2Panel:Instantiate('shop_recipe_lvl2_list',
			'name', 'shop_' .. lvl2Type .. '_list_' .. i
		)

		ShopShared:SpawnPanels(self, cfg, subItems, false, nil, listWidget, globalId)

		-- show connector frame only on item nearest to parent
		for j = 1, #subItems do
			local itemId = globalId + j - 1
			local rootName = cfg.instance .. itemId

			local connectorWidget = self:GetWidget(rootName .. 'frameconnector')
			local singleWidget = self:GetWidget(rootName .. 'framesingle')

			local isConnector
			if lvl2Type == 'requiredlvl2' then isConnector = (j == #subItems) else isConnector = (j == 1) end
				
			connectorWidget:SetVisible(isConnector and 1 or 0)
			singleWidget:SetVisible(isConnector and 0 or 1)
		end

		-- mark scroll item
		if scrollIndex then
			local scrollGlobalId = globalId + scrollIndex - 1

			if self.itemObjectTable[lvl2Type][scrollGlobalId] then
				self.itemObjectTable[lvl2Type][scrollGlobalId].isScroll = true
			end
		end

		globalId = globalId + #subItems
		i = i + 1
	end

	ShopShared:RunActionOnItems(self, function(itemObj) ShopShared:PopulateItem(itemObj, ShopHD) end, lvl2Type)
end

function ShopHD:FillRecipePanel(itemData, itemType, force)

	if GetCvarBool('cg_useClassicShop') then
		ClearAllPanelVariants(self.requiredItemListPanels, self, 'required')
		ClearAllPanelVariants(self.buildsIntoItemListPanels, self, 'buildsinto')
		ClearAllPanelVariants(self.requiredLvl2Panels, self, 'requiredlvl2')
		ClearAllPanelVariants(self.buildsIntoLvl2Panels, self, 'buildsintolvl2')
		for _, child in pairs(self.buildsIntoWidePanel:GetChildren()) do
			child:Destroy()
		end
		self.buildsIntoWidePanel:Sleep(1, function() self.buildsIntoWidePanel:RecalculateSize() end)
	else
		ShopShared:ClearItemPanel(self, 'required', 'buildsinto')
	end

	-- if the focus item was selected and you select it again, it closes the panel, unless force is true
	local recipePanelItemType = (itemType == 'focused' or itemType == 'buildsinto' or itemType == 'required' or itemType == 'requiredlvl2' or itemType == 'buildsintolvl2')

	if(not force and itemData.Name == self.itemObjectTable.focused[0].itemData.Name and not recipePanelItemType and self.recipePanel:IsVisible()) then
		self.recipePanel:SetVisible(0)
		self:UpdateShopGuideVisibility(false)
		ShopShared:UpdateHotkeys(self)
		return
	end

	-- show recipe panel and run fade effect (unless force showing which is used when reopening shop or updating)
	local skipFade = recipePanelItemType and self.recipePanel:IsVisible()
	self.recipePanel:SetVisible(0)
	if skipFade then
		self.recipePanel:SetVisible(1)
	else
		self.recipePanel:FadeIn(300)
	end
	self:UpdateShopGuideVisibility(true)

	local focusedItem = self.itemObjectTable.focused[0]

	-- fetch and store current items in backpack/stash/wards
	self:UpdatePlayerItems()

	-- transfers selected item to focus item and populates it
	focusedItem.itemData = itemData
	ShopShared:PopulateItem(focusedItem, self)

	-- store remaining cost
	local remainingCost = GetRemainingCost(focusedItem.itemData.itemDef)

	-- notify the object that a focused item was selected (label/buy button updates)
	self:OnFocusedItemSelected(focusedItem, remainingCost)

	local bestRecipeIndex = ShopShared:FindBestRecipe(itemData)
	self:SetRecipeIndex(bestRecipeIndex)
	local requiredComponents = ShopShared:BuildItemTable(itemData.itemDef:GetComponentsList()[bestRecipeIndex] or {}, true, self)
	local buildsIntoList = ShopShared:BuildItemTable(itemData.itemDef:BuildsIntoDeep(), true, self)

	-- Update recipe items in the requiredList to get recipe scroll cost/set scroll icon
	local hasScroll = false
	for i = #requiredComponents, 1, -1 do
		local item = requiredComponents[i]
		if item.itemDef and item.itemDef:GetTypeID() == itemData.itemDef:GetTypeID() then
			-- Move the recipe item to the end of the list when found
			hasScroll = true
			table.insert(requiredComponents, table.remove(requiredComponents, i))
			break
		end
	end

	local hasComponents = #requiredComponents > 0
	local hasBuildsInto = #buildsIntoList > 0

	-- use wide panel when 5+ buildsinto items & 0 components
	local useWidePanel = GetCvarBool('cg_useClassicShop') and not hasComponents and #buildsIntoList >= 5

	if GetCvarBool('cg_useClassicShop') then
		self.recipePanelGeneral:SetVisible(useWidePanel and 0 or 1)
		self.recipePanelWide:SetVisible(useWidePanel and 1 or 0)

		if useWidePanel then
			local wideFocused = self.itemObjectTable.focused[1]
			wideFocused.itemData = itemData
			ShopShared:PopulateItem(wideFocused, self)

			local displayName = itemData.itemDef and itemData.itemDef:GetDisplayName() or '--'
			self.wideFocusedItemNameLabel:SetText(displayName)
			local cost = itemData.itemDef and tostring(itemData.itemDef:GetTotalCost()) or '---'
			self.wideFocusedItemCostLabel:SetText('Стоимость: ' .. cost)

			self.buildsIntoItemListPanel = self.buildsIntoWidePanel
		else
			local requiredCount = math.min(math.max(#requiredComponents, 1), 4)
			local buildsIntoCount = math.min(math.max(#buildsIntoList, 1), 4)

			self.requiredItemListPanel = SelectRecipePanelVariant(self.requiredItemListPanels, requiredCount)
			self.buildsIntoItemListPanel = SelectRecipePanelVariant(self.buildsIntoItemListPanels, buildsIntoCount)

			self.recipeTreeLeftStickRoot:SetVisible(hasComponents and 1 or 0)
			self.recipeLeftHeader:SetVisible(hasComponents and 1 or 0)

			if hasComponents then
				self.recipeTreeLeftStick:SetTexture('/ui/common/new_shop_interface/tree_left_' .. requiredCount .. '.tga')
			end

			self.recipeTreeRightStickRoot:SetVisible(hasBuildsInto and 1 or 0)
			self.recipeRightHeader:SetVisible(hasBuildsInto and 1 or 0)

			if hasBuildsInto then
				self.recipeTreeRightStick:SetTexture('/ui/common/new_shop_interface/tree_right_' .. buildsIntoCount .. '.tga')
			end
		end
	end

	self.recipePanelUpdateIndex = (self.recipePanelUpdateIndex or 0) + 1
	local recipePanelUpdateIndex = self.recipePanelUpdateIndex

	local function PopulateRecipePanelItems()
		if recipePanelUpdateIndex and self.recipePanelUpdateIndex ~= recipePanelUpdateIndex then return end

		ShopShared:SpawnPanels(self, ShopShared.itemObjectCfg['required'], requiredComponents, false)
		ShopShared:SpawnPanels(self, ShopShared.itemObjectCfg['buildsinto'], buildsIntoList, false, useWidePanel and 'shop_item_buildsinto_wide_shop' or nil)

		if hasScroll then
			self.itemObjectTable['required'][#(self.itemObjectTable['required'])].isScroll = true
		end

		ShopShared:RunActionOnItems(self, function(itemObj) ShopShared:PopulateItem(itemObj, ShopHD) end, 'required', 'buildsinto')

		if GetCvarBool('cg_useClassicShop') and not useWidePanel then

			-- Select lvl2 panel variants (aligned with lvl1 item counts)
			self.requiredLvl2Panel = SelectRecipePanelVariant(self.requiredLvl2Panels, #requiredComponents)
			self.buildsIntoLvl2Panel = SelectRecipePanelVariant(self.buildsIntoLvl2Panels, #buildsIntoList)

			-- spawn required LVL2
			self:SpawnLvl2('required', 'requiredlvl2', function(itemObj)
				if itemObj.isScroll or not itemObj.itemData or not itemObj.itemData.itemDef then return {} end
				local compList = itemObj.itemData.itemDef:GetComponentsList()
				local bestRecipe = ShopShared:FindBestRecipe(itemObj.itemData)
				local subComps = ShopShared:BuildItemTable(bestRecipe ~= -1 and compList[bestRecipe] or {}, true, self)

				-- Detect recipe scroll (component with same TypeID as parent)
				local scrollIndex = nil
				for i = #subComps, 1, -1 do
					if subComps[i].itemDef and subComps[i].itemDef:GetTypeID() == itemObj.itemData.itemDef:GetTypeID() then
						table.insert(subComps, table.remove(subComps, i))
						scrollIndex = #subComps
						break
					end
				end

				-- Reverse order so items fan outward to the left (rightmost = closest to parent)
				local reversed = {}
				for i = #subComps, 1, -1 do
					tinsert(reversed, subComps[i])
				end
				if scrollIndex then
					scrollIndex = #subComps - scrollIndex + 1
				end

				return reversed, scrollIndex
			end)

			-- spawn builds-into LVL2
			self:SpawnLvl2('buildsinto', 'buildsintolvl2', function(itemObj)
				if not itemObj.itemData or not itemObj.itemData.itemDef then return {} end
				return ShopShared:BuildItemTable(itemObj.itemData.itemDef:BuildsIntoDeep(), true, self)
			end)

		end

		self:MarkItemCategoryOwnedItems('required')
		self:ItemCostUpdate()

		ShopShared:UpdateHotkeys(self, true)
	end

	-- Defer the spawn one frame. FillRecipePanel can be triggered from a click on a
	-- required/builds-into item, which runs while the engine is still iterating that
	-- panel's children to dispatch the input.
	self.recipePanel:Sleep(1, function() PopulateRecipePanelItems() end)
end

------------------------------
--		  Registers			--
------------------------------

local function PlayerGold(gold)
	playerGold = tonumber(gold)
	ShopHD:ItemCostUpdate()
end

local function ShopActive(active)
	active = AtoB(active)
	ToggleShopVisibility(active)
	ShopHD:PopulatePinnedItems(active)
	if active then
		-- search
		if GetCvarBool('cg_useShopKeybinds') then
			ShopHD.searchHotkeyBox:SetVisible(1)
			ShopHD.searchHotkey:SetText(GetKeybindButton("shop", "ShopSearch", ""))
		else
			ShopHD.searchHotkeyBox:SetVisible(0)
		end
	end

end

local function ShopAccess(shopList)

	ShopHD.shopAccess = shopList

	local shops = {}
	-- Parse the shop list string and mark each shop as present.
	for shop in string.gmatch(ShopHD.shopAccess, "Shop_([%w_]+)") do
		shops[shop] = true
	end

	ShopShared:RunActionOnItems(ShopHD, function(item)
		item.button:SetMouseOverCursor(ShopShared:GetCursor(ShopHD, item))
	end)

	CalculateCourierStatus()
end

local function PlayerCanShop(playerCanShop)
	canShop = AtoB(playerCanShop)
end

local function ItemPurchased()
	interface:UICmd("PlaySound('/shared/sounds/ui/sell.wav')")
end

local function ItemSold()
	interface:UICmd("PlaySound('/shared/sounds/ui/sell.wav')")
end

local function OnHeroChange(heroName)
	ShopGuides:UpdateGuide(heroName)
end

local function CourierStatus(newStatus)
	ShopHD.courier_status = tonumber(newStatus)
	CalculateCourierStatus()
	ShopShared:RunActionOnItems(ShopHD, function(item)
		item.button:SetMouseOverCursor(ShopShared:GetCursor(ShopHD, item))
	end)
end

local function ShopActiveRequest(shop)

	-- TODO: This works, but the sleep makes it flash the all tab quickly when clicking outpost
	-- good enough for now

	if not NotEmpty(shop) then return end

	shop = shop:gsub('Shop_', '')

	if not ShopHD.rootPanel:IsVisible() then
		overrideDefaultTab = true
	end
	
	ShopShared:SetLeftCategoryTab(shop, nil, ShopHD)
end

local function RecipeItemRequest(itemName)
	local typeid = HoN.GetItemTypeID(itemName)
	if ShopShared.itemTableCache[typeid] then
		ShopHD:FillRecipePanel(ShopShared.itemTableCache[typeid], 'focused', true)
	end
end

function ShopHD:BuyPinnedItem(itemIndex)

	-- get pin item from table from keybind index (starts at 0)
	local pinObj = self.itemObjectTable['pinned'][itemIndex]

	if pinObj and pinObj.itemData and pinObj.itemData.Name ~= '' then
		ShopShared:BuyItems(pinObj.itemData.Name, pinObj.isScroll)
	end
end

local function NotifyShopButtonPressed(isPressed)
	-- legacy pinned item keybind thing, need to remove this at some point
end

local function OnShopHotkey(slot)
	slot = tonumber(slot)
	if slot == nil then return end
	if not ShopHD.rootPanel:IsVisible() then return end
	ShopShared:HandleShopHotkey(ShopHD, slot)
end

local function UpdateGameServerPhase(phase)
	currGameServerPhase = tonumber(phase)
	ShopGuides:UpdateGameServerPhase(phase)

	-- Auto level first ability when pre game ends
	if ShopHD.equippedGuide then
		ShopGuides:ProcessAutoLevel(ShopHD.equippedGuide)
	end
end

------------------------------
--			 Init			--
------------------------------

function ShopHD:SetupPinnedItems()

	-- create fake list of empty items for pinned slots
	local pinnedItemsList = {}
	for i = 1, ShopShared:GetNumPinnedItems(self) do
		table.insert(pinnedItemsList, ShopShared:BuildBlankItemData())
	end

	-- spawn pinned item panels
	ShopShared:SpawnPanels(self, ShopShared.itemObjectCfg['pinned'], pinnedItemsList, true)

	-- populate them (with blank data for now)
	ShopShared:RunActionOnItems(self, function(itemObj)
		ShopShared:PopulateItem(itemObj, self)
	end, 'pinned')

	-- load saved pinned items per hero
	local heroName = GetViewHeroName() or ''
	local pinned = ShopShared.shopSaveData.pinnedItems
	pinned = type(pinned) == 'table' and pinned or {}
	pinned[heroName] = pinned[heroName] or {}

	for i=0, ShopShared:GetNumPinnedItems(self)-1 do
		pinned[heroName][i] = pinned[heroName][i] or ''
	end

	ShopShared.shopSaveData.pinnedItems = pinned
	ShopShared:FlushShopSaveData()

end

function ShopHD:SpawnRecommendedEmptySlots()

	local recommendedCfgNames = { 'recommended1', 'recommended2', 'recommended3', 'recommended4' }
	
	for _, cfgName in ipairs(recommendedCfgNames) do
		
		local cfg = ShopShared.itemObjectCfg[cfgName]
		local panel = cfg.emptySlotPanel(self)

		panel:ClearChildren()

		-- spawns the empty recommended panel slots
		local blankSlots = {}
		for i = 1, (cfg.maxItems or 0) do
			table.insert(blankSlots, { rootPanel = panel:Instantiate('shop_item_recommended_blank') })
		end

		-- align them to grid
		ShopShared:ArrangeWidgetsInGrid(
			panel,
			blankSlots,
			{
				xMargin = cfg.gridSettings and cfg.gridSettings.x_margin,
				yMargin = cfg.gridSettings and cfg.gridSettings.y_margin,
				topSpacing = cfg.gridSettings and cfg.gridSettings.topSpacing,
				maxPerRow = cfg.gridSettings and cfg.gridSettings.maxPerRow,
				arrangeFromLeft = cfg.gridSettings and cfg.gridSettings.arrangeFromLeft
			}
		)

	end

end

function ShopHD:SetupCvars()
	--none lol
end

function ShopHD:SetupRegisters()
	interface:RegisterWatch('ShopActive', function(_, ...) ShopActive(...) end)
	interface:RegisterWatch('ShopAccess', function(_, ...) ShopAccess(...) end)
	interface:RegisterWatch('ShopActiveRequest', function(_, ...) ShopActiveRequest(...) end)
	interface:RegisterWatch('RecipeItemRequest', function(_, ...) RecipeItemRequest(...) end)
	interface:RegisterWatch('PlayerCanShop', function(_, ...) PlayerCanShop(...) end)
	interface:RegisterWatch('ItemPurchased', ItemPurchased)
	interface:RegisterWatch('ItemSold', ItemSold)
	interface:RegisterWatch('HeroInventoryChanged', function(_) UpdateCurrentFocusPanel() end)
	interface:RegisterWatch('AutoCourierModernStatus', function(_, ...) CourierStatus(...) end)
	interface:RegisterWatch('PlayerGold', function(_, ...) PlayerGold(...) end)
	interface:RegisterWatch('BuyPinnedItem', function(_, itemIndex) self:BuyPinnedItem(tonumber(itemIndex)) end)
	interface:RegisterWatch('NotifyShopButtonPressed', function(_, isPressed) NotifyShopButtonPressed(tonumber(isPressed) ~= 0) end)
	interface:RegisterWatch('ShopHotkey', function(_, ...) OnShopHotkey(...) end)
	interface:RegisterWatch('HeroRealName', function(_, ...) OnHeroChange(...) end)
	interface:RegisterWatch('GameServerPhase', function(_, ...) UpdateGameServerPhase(...) end)
	interface:RegisterWatch('GuidesLoaded', function(_, ...) ShopGuides:OnGuidesLoaded(...) end)
	interface:RegisterWatch('OnGuideFetched', function(_, ...) ShopGuides:OnGuideFetched(...) end)
	interface:RegisterWatch('OnDefaultGuideFetched', function(_, ...) ShopGuides:OnDefaultGuideFetched(...) end)
	interface:RegisterWatch('OnGuideVoted', function(_, ...) ShopGuides:OnGuideVoted(...) end)
	interface:RegisterWatch('ShopSearch', function(_, ...) ShopHD.searchBox:SetFocus(true) end)

end

function ShopHD:SetupValues()
	--self.recipePanelInner_W = self.recipePanelInner:GetWidth()
	self.itemPanelBase_H = self.rightItemsRootPanel:GetHeight()
	--self.treeShopFrame_W = self.treeShopFrame:GetWidth()
	self.shopRightRoot:SetWidth(self.shopRightRoot:GetWidth() - self.leftCategoriesRootPanel:GetWidth())
	ShopHD.currentHeroName = ''
	ShopHD.currentHeroNameForRecommended = ''
	SetAutoLevelup('')
end

function ShopHD:Init()
	ShopShared:RegisterShopObject(ShopHD, 'shop', {'shophd'})
	ShopHD.defaultTabField = 'defaultTabGame'
	ShopHD.activeShopLayout = GetCvarBool('cg_useAdvancedShopCategories') and 'basic' or 'legacy'

	ShopHD:SetupValues()
	ShopHD:SetupRegisters()
	ShopShared:SetupLeftCategoryTabs(ShopHD)
	ShopShared:SetupSubCategoryTabs(ShopHD)

	-- focus widgets
	ShopShared:SetupFocusPanelWidgets(ShopHD)
	if GetCvarBool('cg_useClassicShop') then
		ShopShared:SetupFocusPanelWidgets(ShopHD, 1)
	end

	ShopHD:SetupPinnedItems()
	ShopHD:SpawnRecommendedEmptySlots()
	ShopShared:InitSearchInstances(ShopHD)
	ShopHD:ToggleQuickBuyHide(true)
	ShopHD:ToggleShopKeybinds(true)
	ShopHD:ToggleShopLayout(true)
	ShopGuides:ToggleGuideSelector(true)
	ShopGuides:InitMapFilters(ShopHD.guideMapFiltersRoot)
	ShopGuides:InitRoleFilters(ShopHD.guideRoleFiltersRoot)
	ShopGuides:InitSortDropdown()
	ShopGuides:InitLegacyGuideDropdown()
	ShopGuides:UpdateGuide(GetViewHeroName())
end

------------------------------
--		 Shared Hooks		--
------------------------------

function ShopHD:OnFocusedItemSelected(focusedItem, remainingCost)
	--local label = (focusedItem.itemData.IsRecipe and Translate('shop_buyremaining') or Translate('shop_buyitem'))
	--self.buyRemainingBtnLabel:SetText(label .. ' - ' .. remainingCost)

	if GetCvarBool('cg_useClassicShop') then
		local displayName = focusedItem.itemData.itemDef and focusedItem.itemData.itemDef:GetDisplayName() or '--'
		self.focusedItemNameLabel:SetText(displayName)

		local cost = focusedItem.itemData.itemDef and tostring(focusedItem.itemData.itemDef:GetTotalCost()) or '---'
		self.focusedItemCostLabel:SetText(cost)
	end

end

function ShopHD:OnRecommendedVisibilityUpdate(isRecommendedShop)
	self.recommendedRoot:SetVisible(isRecommendedShop and 1 or 0)
	
	if GetCvarBool('cg_useClassicShop') then
		self.sectionHeaderFrame:SetWidth(isRecommendedShop and '77.2h' or '100.6h')
		self.bodyFrame:SetWidth(isRecommendedShop and '78.5h' or '101.8h')
		self.shopItemsPanel:SetWidth(isRecommendedShop and '98h' or '120h')
	end

	if isRecommendedShop then
		self.recommendedRoot:SetVisible(0)
		self.recommendedRoot:FadeIn(200)
	end
end

function ShopHD:OnRequiredItemSpawned(parentWidget, itemType, i, total)
	if GetCvarBool('cg_useClassicShop') then return  end

	if itemType == 'required' and i < total then
		parentWidget:Instantiate('shop_item_required_operator')
	end
end

function ShopHD:OnPopulateItemExtended(itemObj, itemData, shopShared)
	itemObj.countLabel:UnregisterWatch('MatchTime')

	if(itemData.RestockDelay > 0) then
		itemObj.timerContainer:SetVisible(1)
		itemObj.countLabel:RegisterWatch('MatchTime', function(_, time)
			local restockTime, currentStock = GetItemStockInfo(itemData.itemDef)

			-- Set the count ( amount of items ready to buy )
			itemObj.countLabel:SetText(currentStock)

			if (restockTime > 0) then
				-- if timer is greater than zero, then stock is replenishing so show the time on the label
				itemObj.timerLabel:SetText(shopShared:ConvertTimeRange(restockTime))
				itemObj.timerContainer:SetVisible(1)
			else
				-- if timer is zero, then stock is at max
				itemObj.timerLabel:SetText('')
				itemObj.timerContainer:SetVisible(0)
			end
		end)
	else
		itemObj.timerContainer:SetVisible(0)
		itemObj.timerLabel:SetText('')
	end

	itemObj.button:SetMouseOverCursor(shopShared:GetCursor(self, itemData))
end

function ShopHD:OnSearchShiftClick(itemData)
	if Input.IsShiftDown() then
		ShopQBuy:InstantiateQbItem_External(itemData.Name, false, ShopQBuy:GetQbWidgetID_External())
		return true
	end
	return false
end

function ShopHD:GetDisplayButtonType(itemObjCfg)

	local baseSuffix = ''

	if ShopShared.shopSaveData.miscDefaults.gridList ~= 0 then
		if ShopShared:IsCenterGridItem(itemObjCfg.itemType) then
			baseSuffix = '_list'
		end
	elseif GetCvarBool('cg_useClassicShop') then
		if ShopShared:IsCenterGridItem(itemObjCfg.itemType) then
			baseSuffix = '_large'
		end
	end

	if itemObjCfg.customObjectInstance then
		local objNameLower = ShopShared:GetShopNameByObject(self)
		baseSuffix = '_' .. objNameLower .. baseSuffix
	end

	return baseSuffix
end

function ShopHD:OnSearchInstanceSetup(searchInstance, i, shopShared)
	searchInstance:SetCallback('onrightclick', function()
		local itemDef = self.searchResults[i].itemDef
		local itemData = shopShared:BuildItemDataFromComponent(itemDef)
		shopShared:BuyItems(itemData.Name, false)
		shopShared:ClearSearch(self)
	end)
end

------------------------------
--		   External			--
------------------------------

function ShopHD:OnItemRClick(object, widget, itemType, id)

	-- holding shift and right clicking a pinned item clears it
	if Input.IsShiftDown() and itemType == 'pinned' then

		local pinObj = object.itemObjectTable['pinned'][tonumber(id)]

		pinObj.itemData = ShopShared:BuildBlankItemData()
		pinObj.emptyPin:SetVisible(1)
		pinObj.filledPin:SetVisible(0)
		ShopShared:PopulateItem(pinObj, object)
		object:ItemCostUpdate()

		-- remove it from saved data for the current hero
		local heroName = GetViewHeroName() or ''
		local pinned = ShopShared.shopSaveData.pinnedItems or {}
		pinned[heroName] = pinned[heroName] or {}
		pinned[heroName][tonumber(id)] = ''

		ShopShared.shopSaveData.pinnedItems = pinned
		ShopShared:FlushShopSaveData()

	else

		-- normal right click -> buy the item
		local itemObject = ShopHD.itemObjectTable[itemType][tonumber(id)]
		ShopShared:BuyItems(itemObject.itemData.Name, itemObject.isScroll)

	end
end

function ShopHD:OnItemLClick(widget, itemType, id)
	local index = tonumber(id)
	local itemObject = ShopHD.itemObjectTable[itemType][index]
	if not itemObject then return end

	if Input.IsShiftDown() then
		ShopQBuy:InstantiateQbItem_External(itemObject.itemData.Name, itemObject.isScroll, ShopQBuy:GetQbWidgetID_External())
		return
	end

	if Input.IsAltDown() then
		if itemType == 'required' then
			for _, qbObject in ipairs(ShopQBuy.qbObjects) do
				if qbObject.itemData == ShopHD.itemObjectTable.focused[0].itemData then
					itemObject = ShopHD.itemObjectTable.focused[0]
					break
				end
			end
		end
		SendGamePing('alt_shop_item', HoN.GetItemTypeID(itemObject.itemData.Name))
		return
	end

	-- Normal click: show recipe panel
	if itemType ~= 'focused' then
		ShopHD:ShowShopTooltip(false)
		ShopHD:FillRecipePanel(itemObject.itemData, itemType, nil)
	end
end

function ShopHD:RegisterBuyButton(widget)

	local function BuyButton()
		local focusedItemData = ShopHD.itemObjectTable.focused[0].itemData
		ShopShared:BuyItems(focusedItemData.Name, focusedItemData.IsScroll)
	end

	widget:SetCallback('onclick', function() BuyButton() end)
	widget:SetCallback('onrightclick', function() BuyButton() end)
end

function ShopHD:RegisterSellerCatcher(widget)

	local function ItemCatcherCursor(cursorVisible)
		widget:SetColor(canShop and cursorVisible and '1 1 1 .6' or '1 1 1 0')
		widget:SetVisible(canShop and cursorVisible and 1 or 0)
	end

	local function CheckIfHoveringAndSell()
		if IsInputCursorInsideWidget(widget) then
			widget:UICmd("Sell()")
		end
	end

	widget:RegisterWatch('ItemCursorVisible', function(_, _, cursorVisible) ItemCatcherCursor(AtoB(cursorVisible)) end)
	widget:SetCallback('onmouselup', function() CheckIfHoveringAndSell() end)
end

function ShopHD:CloseRecipePanel()
	self.recipePanel:SetVisible(0)
	self:UpdateShopGuideVisibility(false)
	ShopShared:UpdateHotkeys(self)
end

function ShopHD:CloseShop()
	interface:UICmd('ToggleShop()')
end

function ShopHD:ToggleOpacity(widget, init)
	if init then
		local opacity = math.max(0.1, math.min(1, tonumber(ShopShared.shopSaveData.miscDefaults.opacity) or 1))
		widget:SetValue((opacity - 0.1) / 0.9)
	else
		ShopShared.shopSaveData.miscDefaults.opacity = 0.1 + (widget:GetValue() * 0.9)
		ShopShared:FlushShopSaveData()
	end
	UpdateUIOpacity()
end

function ShopHD:ToggleShopHotkeyTipVisibility(show)
	ShopHD.shopHotkeyTip:SetVisible(show)
end

function ShopHD:OnGuideAbilityMouseOver(mouseover, index)
	Tooltips:ShowAbilityTooltip('active', index, mouseover, mouseover)
end

function ShopHD:OnGuideTipMouseOver(widget, state, id)
	if state and ShopHD.equippedGuide and ShopHD.equippedGuide.itemCategories then
		local category = ShopHD.equippedGuide.itemCategories[tonumber(id)]
		if category then
			Tooltips:TooltipHover_Game(widget, category.description, 'top', '38h')
		end
	else
		Tooltips:TooltipHover_Game(false)
	end
end

ShopHD:Init()
