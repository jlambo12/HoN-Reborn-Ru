----------------------------------------------------------
--	Name:		Matchmaking FE3							--
--	(C) 2025 Juvio, LLC									--
----------------------------------------------------------
local _G = getfenv(0)
local interface = object
local interfaceName = object:GetName()

Matchmaking = _G['Matchmaking'] or {}

local ipairs, pairs, select, string, table, next, type, unpack, tinsert, tconcat, tremove, format, tostring, 
tonumber, tsort, ceil, floor, sub, find, gfind = _G.ipairs, _G.pairs, _G.select, _G.string, _G.table, _G.next, 
_G.type, _G.unpack, _G.table.insert, _G.table.concat, _G.table.remove, _G.string.format, _G.tostring, _G.tonumber, 
_G.table.sort, _G.math.ceil, _G.math.floor, _G.string.sub, _G.string.find, _G.string.gfind

----------------------------------------------------------
--						   Vars							--
----------------------------------------------------------

-- widgets
local rootPanel = WExt:InitWidget('matchmaking', Matchmaking)
local regionRoot = WExt:InitWidget('matchmaking_region_root', Matchmaking)
local modesCaldavarRoot = WExt:InitWidget('matchmaking_modes_caldavar_root', Matchmaking)
local modesMidwarsRoot = WExt:InitWidget('matchmaking_modes_midwars_root', Matchmaking)
local modesCaldavarEmptyLabel = WExt:InitWidget('matchmaking_modes_caldavar_empty', Matchmaking)
local modesMidwarsEmptyLabel = WExt:InitWidget('matchmaking_modes_midwars_empty', Matchmaking)
local playersRoot = WExt:InitWidget('matchmaking_players_root', Matchmaking)

local hostPlayerNameLabel = WExt:InitWidget('matchmaking_profile_section_playername', Matchmaking)
local hostPlayerCaldavarRatingLabel = WExt:InitWidget('matchmaking_profile_section_caldavar_rating', Matchmaking)
local hostPlayerMidwarsRatingLabel = WExt:InitWidget('matchmaking_profile_section_midwars_rating', Matchmaking)
local hostPlayerRoleIcon = WExt:InitWidget('matchmaking_profile_host_role', Matchmaking)
local hostPlayerLeaderIcon = WExt:InitWidget('matchmaking_profile_section_leader_icon', Matchmaking)
local hostPlayerAddFriendBtn = WExt:InitWidget('matchmaking_profile_section_add_friend', Matchmaking)
local hostPlayerLeaderCrownIcon = WExt:InitWidget('matchmaking_profile_section_leader', Matchmaking)
local hostPlayerKickBtn = WExt:InitWidget('matchmaking_player_kick_btn', Matchmaking)
local hostLeaveGroupBtn = WExt:InitWidget('matchmaking_player_leavegroup_btn', Matchmaking)
local confirmInvitePlayerBtn = WExt:InitWidget('matchmaking_confirm_invite_player', Matchmaking)
local invitePlayerInput = WExt:InitWidget('matchmaking_invite_player_input', Matchmaking)

local queueBtn = WExt:InitWidget('matchmaking_joinque_btn', Matchmaking)
local queueLabel = WExt:InitWidget('matchmaking_joinque_btn_label', Matchmaking)
local queueBtnInQueue = WExt:InitWidget('matchmaking_joinque_btn_inqueue', Matchmaking)
local queueLabelInQueue = WExt:InitWidget('matchmaking_joinque_btn_inqueue_label', Matchmaking)

local queueBtnPenalty = WExt:InitWidget('matchmaking_joinque_penalty_btn', Matchmaking)
local queuePenaltyLabel = WExt:InitWidget('matchmaking_joinque_penalty_btn_label', Matchmaking)
local queueBtnBlocked = WExt:InitWidget('matchmaking_joinque_blocked_btn', Matchmaking)
local queueBlockedLabel = WExt:InitWidget('matchmaking_joinque_blocked_btn_label', Matchmaking)

local rolesTooltip = WExt:InitWidget('matchmaking_player_role_tooltip', Matchmaking)

local noticeLabel = WExt:InitWidget('matchmaking_group_notice_label', Matchmaking)

local penaltyPointsNameLabel = WExt:InitWidget('matchmaking_penalty_points_name', Matchmaking)
local penaltyPointsLabel = WExt:InitWidget('matchmaking_penalty_points_value', Matchmaking)

local pp_queueDelayLabel = WExt:InitWidget('matchmaking_queue_delay_value', Matchmaking)
local pp_MatchedWithLabel = WExt:InitWidget('matchmaking_queue_with', Matchmaking)
local pp_rolePriorityLabel = WExt:InitWidget('matchmaking_role_priority', Matchmaking)
local pp_baseIcon = WExt:InitWidget('matchmaking_penalty_points_base', Matchmaking)

-- One table, not six top-level locals: this chunk is close to LuaJIT's 200-local main-chunk ceiling.
local npe = {
	root = WExt:InitWidget('matchmaking_npe_root', Matchmaking),
	ctaCol = WExt:InitWidget('matchmaking_npe_cta_col', Matchmaking),
	ctaDivider = WExt:InitWidget('matchmaking_npe_cta_divider', Matchmaking),
	ctaLabel = WExt:InitWidget('matchmaking_npe_cta_btn_label', Matchmaking),
	upgradeEntry = nil,
	-- notices can arrive at login, before this panel's widgets exist; touching a WExt proxy
	-- that early is a hard error, so nothing below writes to them until OnShow has run once
	panelReady = false,
}

local penaltyDialogConfirm = WExt:InitWidget('matchmaking_penalty_wait_confirm', Matchmaking)

local machineTagRoot = WExt:InitWidget('matchmaking_machine_tag_root', Matchmaking)
local machineTagIcon = WExt:InitWidget('matchmaking_machine_tag_icon', Matchmaking)
local machineTagLabel = WExt:InitWidget('matchmaking_machine_tag_label', Matchmaking)
local machineTagSubLabel = WExt:InitWidget('matchmaking_machine_tag_sub_label', Matchmaking)
local machineTagRetagRoot = WExt:InitWidget('matchmaking_machine_tag_retag_root', Matchmaking)

local retagDialog = WExt:InitWidget('matchmaking_retag_confirm', Matchmaking)
local retagDialogBodyLabel = WExt:InitWidget('matchmaking_retag_confirm_body_label', Matchmaking)
local retagDialogPromptLabel = WExt:InitWidget('matchmaking_retag_confirm_prompt_label', Matchmaking)
local retagDialogErrorLabel = WExt:InitWidget('matchmaking_retag_confirm_error_label', Matchmaking)
local retagDialogInput = WExt:InitWidget('matchmaking_retag_confirm_input', Matchmaking)
local retagDialogConfirmBtn = WExt:InitWidget('matchmaking_retag_confirm_ok', Matchmaking)

local machineTagDeniedDialog = WExt:InitWidget('matchmaking_machine_tag_denied_dialog', Matchmaking)
local machineTagDeniedLines = {}
for i = 1, 5 do
	machineTagDeniedLines[i] = WExt:InitWidget('matchmaking_machine_tag_denied_line' .. i, Matchmaking)
end

local playBanDeniedDialog = WExt:InitWidget('matchmaking_play_ban_denied_dialog', Matchmaking)
local playBanDeniedLines = {}
for i = 1, 5 do
	playBanDeniedLines[i] = WExt:InitWidget('matchmaking_play_ban_denied_line' .. i, Matchmaking)
end

local queueAgainstLabel = WExt:InitWidget('matchmaking_team_feedback_queue_against', Matchmaking)
local queueAgainstIcon = WExt:InitWidget('matchmaking_team_feedback_queue_against_icon', Matchmaking)

local balanceBestBtn = WExt:InitWidget('mm_fairness_balance_btn', Matchmaking)
local balanceFastBtn = WExt:InitWidget('mm_fairness_speed_btn', Matchmaking)

Matchmaking.invitePlayerPanel = WExt:InitWidget('matchmaking_invite_dialog', Matchmaking)

local function IsWebResourceTexture(iconPath)
	if type(iconPath) ~= 'string' or iconPath == '' then return false end
	-- Web textures arrive in any of these forms:
	--   'https://...'                raw URL (pre-resolution)
	--   '*https://...'               RES_TEXTURE resource key registered by WebResourceManager
	--   '!<sha256>'                  RES_REFERENCE reference name returned by g_ResourceManager.GetPath
	return find(iconPath, 'https://', 1, true) ~= nil or string.sub(iconPath, 1, 1) == '!'
end

-- strings
local modeTemplate = 'matchmaking_mode'
local flagTemplate = 'matchmaking_flag'
local playerTemplate = 'matchmaking_player'

-- ints
local maxModes = 4
local maxRegions = 4
local playersInQueue = 0
local rating_disparity_limit = '???'

-- vars
Matchmaking.CurrentState = Matchmaking.CurrentState or Enum.MatchmakingState.NotInGroup
Matchmaking.init = false

local matchmakingSaveDataName = "matchmaking_SaveData_v25"

Matchmaking.BalanceMode =
{
	BestBalance = 1, -- aka slider 1.0
	FastestQueue = 0, -- aka slider 0.0
}

-- tables
local regionList = {}
local modeList = {}
local modeBackgrounds = {
	caldavarphoenix = {
		texture = '/ui/fe3/elements/caldavar.tga',
		width = 2368,
		height = 907,
	},
	midwars = {
		texture = '/ui/fe3/elements/midwars.tga',
		width = 2368,
		height = 907,
	},
}

local MatchmakingMode = {
	RankedCaldavar = 1,
	UnrankedMidwars = 2,
	UnrankedCaldavar = 4,
	RankedMidwars = 8,
	-- MidWars Banning Pick variants; RankedMidwars/UnrankedMidwars are the Single Draft variants of the same map.
	RankedMidwarsBanning = 16,
	UnrankedMidwarsBanning = 32,
}

-- single account per machine for ranked play (MachineTagStatus param[0])
local MachineTagState = {
	Unknown = 0,
	Untagged = 1,
	TaggedToYou = 2,
	TaggedToOther = 3,
	AccountExempt = 4,
	MachineWhitelisted = 5,
}

local machineTag = {
	state = MachineTagState.Unknown,
	taggedAccountName = '',
	canRetag = false,
	nextRetagAt = 0,
	serverTime = 0,
	retagCooldownDays = 0,
	localUsername = '',
	clockOffset = 0, -- serverTime - local clock, so cooldown math never trusts the local clock
	retagPending = false,
}

-- Play ban on the local account (PlayBanStatus). Separate from the account disable, which never gets
-- this far because it rejects the login itself.
local playBan = {
	active = false,
	reason = '',
	endsAt = 0, -- unix seconds; 0 means permanent
	blocksPublicLobbies = false,
}

local function SizeModeBackground(backgroundWidget, clipWidget, backgroundData)
	if not (backgroundWidget and clipWidget and backgroundData) then
		return
	end

	local texturePath = backgroundData.texture or backgroundData
	if not texturePath then
		return
	end

	backgroundWidget:SetTexture(texturePath)
	backgroundWidget:SetVisible(1)

	local clipWidth = tonumber(clipWidget:GetWidth())
	local clipHeight = tonumber(clipWidget:GetHeight())
	local texWidth = tonumber(backgroundData.width)
	local texHeight = tonumber(backgroundData.height)

	if not (clipWidth and clipHeight and texWidth and texHeight) then
		return
	end
	if clipWidth <= 0 or clipHeight <= 0 or texWidth <= 0 or texHeight <= 0 then
		return
	end

	local clipRatio = clipWidth / clipHeight
	local textureRatio = backgroundData.aspect or (texWidth / texHeight)
	backgroundData.aspect = textureRatio
	local targetWidth, targetHeight

	if clipRatio > textureRatio then
		targetWidth = clipWidth
		targetHeight = clipWidth / textureRatio
	else
		targetHeight = clipHeight
		targetWidth = clipHeight * textureRatio
	end

	backgroundWidget:SetWidth(targetWidth)
	backgroundWidget:SetHeight(targetHeight)
	backgroundWidget:SetAlign('center')
	backgroundWidget:SetVAlign('center')
end

local queueRatingConfig = 
{
    [1] = { textKey = 'mm_team_size_solos_matched', color = '#5cec49' },
    [2] = { textKey = 'mm_team_size_duos_matched',  color = '#fcff41' },
    [3] = { textKey = 'mm_team_size_trios_matched', color = '#e9a62b' },
    [5] = { textKey = 'mm_team_size_squads_matched', color = '#c21e1e' },
}

local penaltyTiers = 
{
	{min = 0,  max = 0,   name = 'Chad',    color = '#5a9f60', queueDelay = 0,  matchedWith = 'Все игроки',     blockTopRoles = 0},
	{min = 1,  max = 9,   name = 'Bro',     color = '#b8a830', queueDelay = 0,  matchedWith = 'Все игроки',     blockTopRoles = 0},
	{min = 10, max = 14,  name = 'Sus',     color = '#8b4513', queueDelay = 5,  matchedWith = 'Mixed pool',      blockTopRoles = 0},
	{min = 15, max = 19,  name = 'Tool',    color = '#b82e2e', queueDelay = 10, matchedWith = 'High-PP pool',    blockTopRoles = 2},
	{min = 20, max = 999, name = 'Griefer', color = '#c5c5c5', queueDelay = 20, matchedWith = 'High-PP only',    blockTopRoles = 3},
}

local mm_condition = Enum.MatchmakingCondition.Normal
local mm_cooldown = ''
local mm_queueTime = 0
local mm_numplayers = 0
local mm_penaltyPoints = 0
local mm_allowRankedCaldavar = true
local mm_allowRankedMidwars = true

-- Per-mode reason (an Enum.MatchmakingCondition value) each ranked mode is disallowed for the group, so a
-- grayed-out mode button and the notice can name the real cause (high-MMR duo cap vs. disparity gap).
local mm_caldavarDisallowReason = Enum.MatchmakingCondition.Normal
local mm_midwarsDisallowReason = Enum.MatchmakingCondition.Normal

local function GetGroupDisallowReason()
	if mm_caldavarDisallowReason == Enum.MatchmakingCondition.DisparityTooHigh
		or mm_midwarsDisallowReason == Enum.MatchmakingCondition.DisparityTooHigh then
		return Enum.MatchmakingCondition.DisparityTooHigh
	end
	return Enum.MatchmakingCondition.Normal
end

-- Plain-sentence text for a disallow reason, shared by the grayed-out mode button tooltip and the notice line.
local function DisallowReasonText(reason)
	return Translate('mm_notice_high_disparity_tip', 'limit', rating_disparity_limit)
end
local flagObjects = {}
local modeObjects = {}
local hostObject = {}
local playerObjects = {}

Matchmaking.matchmakingOptions = HoN_Database:ReadDBEntry(matchmakingSaveDataName) or 
{
	region = 3,
	mode = 1,
	balanceMode = Matchmaking.BalanceMode.BestBalance,
}

----------------------------------------------------------
--						  Helpers						--
----------------------------------------------------------

function Matchmaking:MatchmakingVisibleState(widget, op, state)
	local operators = {
		["eq"]  = function(a, b) return a == b end,
		["gt"]  = function(a, b) return a > b end,
		["gte"] = function(a, b) return a >= b end,
		["lt"]  = function(a, b) return a < b end,
		["lte"] = function(a, b) return a <= b end,
	}

	op = op or "eq"
	local cmp = operators[op]
	if not cmp then
		println("^yWarning: MatchmakingVisibleState used invalid operator: " .. tostring(op))
	else
		widget:SetVisible(cmp(Matchmaking.CurrentState, state))
	end
end

----------------------------------------------------------
--						   Code							--
----------------------------------------------------------

function Matchmaking:OpenHonorSystem()
	ProfileV2:OpenWithPlayerName(Main.playerName, Enum.FSPanelDisplay.Sticky)
end

local function SetNoticeLabel(text, type)

	if type == 0 then
		noticeLabel:SetVisible(0)
		noticeLabel:SetText('')
		return
	end

	noticeLabel:SetVisible(1)
	noticeLabel:SetText(text)

	if type == Enum.ErrorType.Warning then
		noticeLabel:SetColor('yellow')
	elseif type == Enum.ErrorType.Error then
		noticeLabel:SetColor('red')
	end

end

local function BitTest(value, bit)
	return value % (bit * 2) >= bit
end

local function MachineTagServerNow()
	if os and os.time then
		return os.time() + machineTag.clockOffset
	end
	-- sandbox without os: freeze at the last server time we were told
	return machineTag.serverTime
end

local function FormatEpochDate(epochSeconds)
	if os and os.date then
		return os.date('%d %b %Y', epochSeconds)
	end
	-- sandbox without os: fall back to the shared UTC helper
	local _, _, _, day, month, year = UnixTimestampToNumeralTime(epochSeconds)
	return format('%04d-%02d-%02d', year, month, day)
end

local function FormatMachineTagRemaining(seconds)
	if seconds < 0 then seconds = 0 end
	local days = floor(seconds / 86400)
	local hours = floor((seconds % 86400) / 3600)
	if days > 0 then
		return days .. 'd ' .. hours .. 'h'
	end
	local minutes = floor((seconds % 3600) / 60)
	return hours .. 'h ' .. minutes .. 'm'
end

-- Only ever the largest unit, so a ban reads 6d, then 19h, then 58m, then 18s as it runs down. A
-- countdown beats an absolute date here: it needs no timezone to read and cannot be misread as local
-- time when it is not. Recomputed whenever the UI refreshes, matching the machine-tag cooldown above.
local function FormatRemainingShort(seconds)
	if seconds < 0 then seconds = 0 end
	if seconds >= 86400 then return floor(seconds / 86400) .. 'd' end
	if seconds >= 3600 then return floor(seconds / 3600) .. 'h' end
	if seconds >= 60 then return floor(seconds / 60) .. 'm' end
	return floor(seconds) .. 's'
end

local function PlayBanRemainingText(endsAt)
	return FormatRemainingShort(endsAt - MachineTagServerNow())
end

-- The ban's own reason is admin-authored free text, so it is shown verbatim; only the frame around it
-- is translated.
local function PlayBanReasonText(reason)
	return NotEmpty(reason) and reason or Translate('play_ban_reason_unspecified')
end

-- The server pushes a ban landing but never pushes one lapsing, so a timed ban has to be checked
-- against the clock on every UI pass. Without this a player sitting in the client when their ban
-- expires keeps a dead Play button until they relog, even though the server would let them queue.
local function PlayBanIsActive()
	if not playBan.active then
		return false
	end

	if playBan.endsAt > 0 and MachineTagServerNow() >= playBan.endsAt then
		playBan.active = false
		return false
	end

	return true
end

local partyRefusals = {}

local ROLE_SOFT_SUPPORT = 4
local ROLE_HARD_SUPPORT = 5
local REASON_INSUFFICIENT_ROLE_TOKENS = 4

local function LocallyCoversASupport()
	local enabled = RolePick_Shared and RolePick_Shared.enabledRoles
	if not enabled then
		return false
	end

	for _, id in ipairs(enabled) do
		if id == ROLE_SOFT_SUPPORT or id == ROLE_HARD_SUPPORT then
			return true
		end
	end

	return false
end

local function ModeRefusalText(modeBit)
	local info = partyRefusals[modeBit]
	if not info then
		return nil
	end

	if info.reason == REASON_INSUFFICIENT_ROLE_TOKENS and LocallyCoversASupport() then
		return nil
	end

	return TranslateOrNil(info.key) or info.text
end

local function RefusalTextFor(mode, wantRoleTokens)
	for modeBit, info in pairs(partyRefusals) do
		if BitTest(mode, modeBit) then
			local isRoleTokens = info.reason == REASON_INSUFFICIENT_ROLE_TOKENS
			if isRoleTokens == wantRoleTokens then
				local text = ModeRefusalText(modeBit)
				if text then
					return text
				end
			end
		end
	end
	return nil
end

local function PartyRefusalText()
	local mode = Matchmaking.matchmakingOptions and Matchmaking.matchmakingOptions.mode or 0
	return RefusalTextFor(mode, false)
end

local function RoleTokenRefusalText()
	local mode = Matchmaking.matchmakingOptions and Matchmaking.matchmakingOptions.mode or 0
	return RefusalTextFor(mode, true)
end

local function PlayBanNoticeText()
	local reason = PlayBanReasonText(playBan.reason)
	if playBan.endsAt > 0 then
		return Translate('play_ban_notice_temporary', 'reason', reason, 'remaining', PlayBanRemainingText(playBan.endsAt))
	end
	return Translate('play_ban_notice_permanent', 'reason', reason)
end

local function MachineTagBlocksRankedQueue()
	if machineTag.state ~= MachineTagState.TaggedToOther then
		return false
	end
	local mode = Matchmaking.matchmakingOptions.mode
	return BitTest(mode, MatchmakingMode.RankedCaldavar) or BitTest(mode, MatchmakingMode.RankedMidwars)
end

local function HasUnrankedBit(mode)
	return BitTest(mode, MatchmakingMode.UnrankedCaldavar)
		or BitTest(mode, MatchmakingMode.UnrankedMidwars)
		or BitTest(mode, MatchmakingMode.UnrankedMidwarsBanning)
end

local function HasRankedBit(mode)
	return BitTest(mode, MatchmakingMode.RankedCaldavar)
		or BitTest(mode, MatchmakingMode.RankedMidwars)
		or BitTest(mode, MatchmakingMode.RankedMidwarsBanning)
end

-- Region lock and any "unranked party restrictions don't apply" logic keys on this: picking unranked at all locks
-- regions, even when ranked is queued alongside it.
local function IsAnyUnrankedSelected()
	return HasUnrankedBit(Matchmaking.matchmakingOptions.mode)
end

local function IsUnrankedOnlySelected()
	local mode = Matchmaking.matchmakingOptions.mode
	return HasUnrankedBit(mode) and not HasRankedBit(mode)
end


-- The 3-stack, 4-stack, high-MMR and rating-disparity conditions are all ranked party restrictions, and the
-- backend applies none of them to unranked, so they must neither warn nor block the queue there. Cooldown and
-- penalty conditions are not party restrictions and still apply.
local function EffectiveMatchmakingCondition()
	if not IsUnrankedOnlySelected() then
		return mm_condition
	end

	if mm_condition == Enum.MatchmakingCondition.Warning_3Stack
	or mm_condition == Enum.MatchmakingCondition.Error_4Stack
	or mm_condition == Enum.MatchmakingCondition.DisparityTooHigh then
		return Enum.MatchmakingCondition.Normal
	end

	return mm_condition
end

-- Roles only matter for Ranked Caldavar; every other mode ignores role priority, so blanket the role notice
-- whenever Ranked Caldavar isn't in the selection. Regions are greyed separately (unranked region lock).
local function UpdateUnrankedOverlays()
	local show = not BitTest(Matchmaking.matchmakingOptions.mode, MatchmakingMode.RankedCaldavar)
	-- RolePick_Play is a separate script object but lives in the same Main interface tree
	local roleOverlay = Main:GetWidget('RolePick_Play_unranked_overlay')
	if roleOverlay then roleOverlay:SetVisible(show) end
end

local MACHINE_TAG_LOCK_ICON = '/ui/hd_ui/icons/lock.tga'
local MACHINE_TAG_UNLOCK_ICON = '/ui/hd_ui/icons/unlock.tga'

local function UpdateMachineTagUI()
	machineTagRoot:SetVisible(false)
	machineTagRetagRoot:SetVisible(false)
	machineTagSubLabel:SetVisible(false)
	machineTagSubLabel:SetText('')

	if machineTag.retagPending then
		machineTagRoot:SetVisible(true)
		machineTagIcon:SetTexture(MACHINE_TAG_LOCK_ICON)
		machineTagLabel:SetColor('#c5c5c5')
		machineTagLabel:SetText(Translate('mm_machine_tag_retag_pending'))
		return
	end

	if machineTag.state == MachineTagState.TaggedToYou then
		machineTagRoot:SetVisible(true)
		machineTagIcon:SetTexture(MACHINE_TAG_LOCK_ICON)
		machineTagLabel:SetColor('#c1ffd2')
		machineTagLabel:SetText(Translate('mm_machine_tag_locked_to_you'))
	elseif machineTag.state == MachineTagState.Untagged then
		machineTagRoot:SetVisible(true)
		machineTagIcon:SetTexture(MACHINE_TAG_UNLOCK_ICON)
		machineTagLabel:SetColor('#c5c5c5')
		machineTagLabel:SetText(Translate('mm_machine_tag_untagged', 'name', machineTag.localUsername))
	elseif machineTag.state == MachineTagState.TaggedToOther then
		machineTagRoot:SetVisible(true)
		machineTagIcon:SetTexture(MACHINE_TAG_LOCK_ICON)
		machineTagLabel:SetColor('#c5c5c5')
		if machineTag.canRetag then
			machineTagLabel:SetText(Translate('mm_machine_tag_locked_to_other', 'name', machineTag.taggedAccountName))
			machineTagRetagRoot:SetVisible(true)
		else
			local remaining = machineTag.nextRetagAt - MachineTagServerNow()
			machineTagLabel:SetText(Translate('mm_machine_tag_retag_cooldown', 'name', machineTag.taggedAccountName))
			machineTagSubLabel:SetColor('#c5c5c5')
			machineTagSubLabel:SetText(Translate('mm_machine_tag_retag_cooldown_sub',
				'date', FormatEpochDate(machineTag.nextRetagAt),
				'remaining', FormatMachineTagRemaining(remaining)))
			machineTagSubLabel:SetVisible(true)
		end
	elseif machineTag.state == MachineTagState.MachineWhitelisted then
		machineTagRoot:SetVisible(true)
		machineTagIcon:SetTexture(MACHINE_TAG_UNLOCK_ICON)
		machineTagLabel:SetColor('#c5c5c5')
		machineTagLabel:SetText(Translate('mm_machine_tag_whitelisted'))
		machineTagSubLabel:SetColor('#c5c5c5')
		machineTagSubLabel:SetText(Translate('mm_machine_tag_whitelisted_sub'))
		machineTagSubLabel:SetVisible(true)
	end
	-- Unknown and AccountExempt show nothing
end

local function UpdateQueueUI()
	local condition = EffectiveMatchmakingCondition()

	-- hide both by default
	queueBtn:SetVisible(false)
	queueBtnInQueue:SetVisible(false)
	queueBtnPenalty:SetVisible(false)
	queueBtnBlocked:SetVisible(false)

	-- OFFLINE state
	if Matchmaking.CurrentState == Enum.MatchmakingState.Offline then
		queueBtnBlocked:SetVisible(true)
		queueBtnBlocked:SetEnabled(false)
		queueBlockedLabel:SetText(Translate('mm_tmmdisabled'))

	-- IN-QUEUE state
	elseif Matchmaking.CurrentState == Enum.MatchmakingState.InQueue then
		-- penalty & postpenalty use red btn
		if condition == Enum.MatchmakingCondition.PenaltyQueue
		or condition == Enum.MatchmakingCondition.PostPenaltyQueue then

			queueBtnPenalty:SetVisible(true)
			queueBtnPenalty:SetEnabled(true)

			if condition == Enum.MatchmakingCondition.PenaltyQueue then
				-- still counting down
				queuePenaltyLabel:SetText(Translate('mm_wait_timer_prepend') .. ' ' .. tostring(mm_queueTime) .. ' ' .. Translate('mm_wait_timer_append'))
			else
				-- past cd counting up
				queuePenaltyLabel:SetText(mm_queueTime)
			end

		else
			-- any other queue state (normal queue timer)
			queueBtnInQueue:SetVisible(true)
			queueBtnInQueue:SetEnabled(true)
			queueLabelInQueue:SetText(mm_queueTime)
		end

	-- NOT IN-QUEUE (lobby) state
	else
		local label, enabled

		if PlayBanIsActive() then
			-- A play ban outranks every queue condition: no mode is reachable at all.
			label, enabled = Translate('mm_queue_cannot_queue_btn'), false
		elseif condition == Enum.MatchmakingCondition.Error_4Stack
			or condition == Enum.MatchmakingCondition.DisparityTooHigh then
			label, enabled = Translate('mm_queue_cannot_queue_btn'), false
		elseif condition == Enum.MatchmakingCondition.MMCooldown then
			label, enabled = Translate('mm_queue_cooldown_btn', 'time', mm_cooldown), false
		else
			local mode = Matchmaking.matchmakingOptions.mode
			local modeAllowed = (BitTest(mode, MatchmakingMode.RankedCaldavar) and mm_allowRankedCaldavar)
			                 or (BitTest(mode, MatchmakingMode.RankedMidwars)  and mm_allowRankedMidwars)
			                 or (BitTest(mode, MatchmakingMode.RankedMidwarsBanning) and mm_allowRankedMidwars)
			                 or (BitTest(mode, MatchmakingMode.UnrankedCaldavar)) -- always allowed
			                 or (BitTest(mode, MatchmakingMode.UnrankedMidwars)) -- always allowed
			                 or (BitTest(mode, MatchmakingMode.UnrankedMidwarsBanning)) -- always allowed
			local tokenRefusal = RoleTokenRefusalText()
			local blockedOtherwise = not modeAllowed or MachineTagBlocksRankedQueue() or PartyRefusalText() ~= nil

			if not blockedOtherwise and not tokenRefusal then
				label, enabled = RoleTokens:QueueButtonText() or Translate('mm_queue_enter_btn'), true
			elseif not blockedOtherwise then
				label, enabled = Translate('mm_queue_btn_required'), false
			else
				label, enabled = Translate('mm_queue_cannot_queue_btn'), false
			end
		end

		local currQueueBtn, currLabel

		if condition == Enum.MatchmakingCondition.PenaltyQueue then
			currQueueBtn, currLabel = queueBtnPenalty, queuePenaltyLabel
		elseif enabled then
			currQueueBtn, currLabel = queueBtn, queueLabel
		else
			currQueueBtn, currLabel = queueBtnBlocked, queueBlockedLabel
		end

		currQueueBtn:SetVisible(true)
		currQueueBtn:SetEnabled(enabled)
		currLabel:SetText(label)
	end

	-- notice state (the machine-tag lock is already shown by the yellow banner + Re-tag button, so it is not duplicated here)
	local groupDisallowReason = GetGroupDisallowReason()
	local partyRefusalText = PartyRefusalText()
	local partyDisparityText = RoleTokens:DisparityText()
	if PlayBanIsActive() then
		SetNoticeLabel(PlayBanNoticeText(), Enum.ErrorType.Error)
	elseif partyRefusalText then
		SetNoticeLabel(partyRefusalText, Enum.ErrorType.Error)
	elseif Matchmaking.CurrentState == Enum.MatchmakingState.Offline then
		SetNoticeLabel('', Enum.ErrorType.Normal)
	elseif condition == Enum.MatchmakingCondition.Error_4Stack then
		SetNoticeLabel(Translate('mm_notice_4stack'), Enum.ErrorType.Error)
	elseif condition == Enum.MatchmakingCondition.DisparityTooHigh then
		SetNoticeLabel(Translate('mm_notice_high_disparity', 'limit', rating_disparity_limit), Enum.ErrorType.Error)
	elseif groupDisallowReason ~= Enum.MatchmakingCondition.Normal and not IsUnrankedOnlySelected() then
		-- One ranked mode is disabled for the group but another stays queueable: explain why, without blocking.
		-- Suppressed under an unranked-only selection, mirroring EffectiveMatchmakingCondition.
		SetNoticeLabel(DisallowReasonText(groupDisallowReason), Enum.ErrorType.Warning)
	elseif partyDisparityText then
		SetNoticeLabel(partyDisparityText, Enum.ErrorType.Warning)
	elseif condition == Enum.MatchmakingCondition.Normal then
		SetNoticeLabel('', Enum.ErrorType.Normal)
	end


end

local function UpdateNumPlayersUI()
	local cfg = queueRatingConfig[mm_numplayers]
	if not cfg then
		-- No "queue against" pool for this group size (e.g. a 4-stack, which cannot queue —
		-- see Error_4Stack). Clear the label/icon instead of leaving the previous size's
		-- stale text and color on screen.
		queueAgainstLabel:SetText('')
		queueAgainstIcon:SetColor('#ffffff')
		return
	end

	queueAgainstLabel:SetText(Translate(cfg.textKey))
	queueAgainstIcon:SetColor(cfg.color)
end

local function UpdatePenaltyUI()

	local function GetPenaltyTier(points)
		for i = 1, #penaltyTiers do
			local t = penaltyTiers[i]
			if points >= t.min and points <= t.max then return t end
		end
		return penaltyTiers[#penaltyTiers]
	end

	local function SetDelay(minutes)
		if minutes <= 0 then return 'Нет' end
		return tostring(minutes) .. ' min'
	end

	local function SetRolePriority(blockTopRoles)
		if blockTopRoles <= 0 then return 'Обычный' end
		return 'Top ' .. tostring(blockTopRoles) .. ' blocked'
	end
	local tier = GetPenaltyTier(mm_penaltyPoints)

	penaltyPointsNameLabel:SetText(tier.name)
	penaltyPointsLabel:SetText(tostring(mm_penaltyPoints))

	pp_queueDelayLabel:SetText(SetDelay(tier.queueDelay))
	pp_MatchedWithLabel:SetText(tier.matchedWith)
	pp_rolePriorityLabel:SetText(SetRolePriority(tier.blockTopRoles))

	pp_baseIcon:SetColor(tier.color)
end

local function SetMatchmakingState(state)
	Matchmaking.CurrentState = state
	UpdateQueueUI()
	Trigger('MatchmakingStateUpdated')
end

local function SaveOptions()
	HoN_Database:SetDBEntry(matchmakingSaveDataName, Matchmaking.matchmakingOptions)
end

local function UpdateMatchmakingSettings()
	local desiredBalanceStrictness = (Matchmaking.matchmakingOptions.balanceMode == Matchmaking.BalanceMode.FastestQueue) and Matchmaking.BalanceMode.FastestQueue or Matchmaking.BalanceMode.BestBalance
	MatchmakingClient.UpdateMatchmakingSettings(Matchmaking.matchmakingOptions.region, Matchmaking.matchmakingOptions.mode, desiredBalanceStrictness)
end

local function UpdateBalanceModeUI()
	local isBestBalance = (Matchmaking.matchmakingOptions.balanceMode == Matchmaking.BalanceMode.BestBalance)

	balanceBestBtn:SetButtonState(isBestBalance and 1 or 0)
	balanceFastBtn:SetButtonState(isBestBalance and 0 or 1)
end

function Matchmaking:SetBalanceMode(mode)
	Matchmaking.matchmakingOptions.balanceMode = mode
	UpdateBalanceModeUI()
	SaveOptions()
	UpdateMatchmakingSettings()
end

function Matchmaking:OnBalanceBestClicked()
	Matchmaking:SetBalanceMode(Matchmaking.BalanceMode.BestBalance)
end

function Matchmaking:OnBalanceFastClicked()
	Matchmaking:SetBalanceMode(Matchmaking.BalanceMode.FastestQueue)
end

-- Unranked may only be queued in regions the server flags AllowsUnranked, so the rest are greyed out while any
-- unranked mode is selected - even if ranked is queued alongside it, since the whole queue is region-locked then.
local function UpdateUnrankedRegionAvailability()
	local restrict = IsAnyUnrankedSelected()

	for _, r in ipairs(regionList) do
		local blocked = restrict and not r.allowsUnranked
		local flag = flagObjects[r.key]
		if flag and flag.button then
			flag.button:SetEnabled(not blocked)
		end

		-- Its own overlay, so it never fights the generic region_disabled_overlay that EnableRegions drives.
		local overlay = Main:GetWidget('region_unranked_overlay' .. r.key)
		if overlay then
			overlay:SetVisible(blocked)
		end
	end
end

-- The server locks an unranked queue (and any ranked queued with it) to AllowsUnranked regions, so never leave a
-- disallowed one selected once any unranked mode is on.
local function StripDisallowedUnrankedRegions()
	if not IsAnyUnrankedSelected() then
		return
	end

	local allowed, kept = 0, 0
	for _, r in ipairs(regionList) do
		if r.allowsUnranked then
			allowed = allowed + r.key
			if BitTest(Matchmaking.matchmakingOptions.region, r.key) then
				kept = kept + r.key
			end
		end
	end

	if allowed == 0 then
		return
	end

	Matchmaking.matchmakingOptions.region = (kept ~= 0) and kept or allowed
end

local function UpdateRegions()
	-- If Matchmaking.matchmakingOptions.region has a one or fewer bits set somewhere, set SetButtonNumStates to 1, otherwise 2, this is to prevent disabling all regions
	local numBits = 0
	for _, r in ipairs(regionList) do
		if Matchmaking.matchmakingOptions.region % (r.key * 2) >= r.key then
			numBits = numBits + 1
		end
	end	

	for _, r in ipairs(regionList) do
		local key = r.key
		local isEnabled = Matchmaking.matchmakingOptions.region % (key * 2) >= key

		if isEnabled then
			flagObjects[key].button:SetButtonNumStates(numBits > 1 and 2 or 1)
			flagObjects[key].button:SetButtonState(0) -- 0 = enabled
		else
			flagObjects[key].button:SetButtonNumStates(2)
			flagObjects[key].button:SetButtonState(1) -- 1 = disabled
		end
		
		-- Update percentage panel disabled state
		local percentageDisabled = Main:GetWidget('matchmaking_flag_percentage_disabled' .. key)

		if percentageDisabled then
			percentageDisabled:SetVisible(not isEnabled)
		end

	end

	UpdateUnrankedRegionAvailability()
end

local function ToggleRegion(region)
	local nRegion = tonumber(region)
	-- Matchmaking.matchmakingOptions.region is a bitmask of enabled regions
	if BitTest(Matchmaking.matchmakingOptions.region, nRegion) then
		-- If the region is currently enabled, disable it
		Matchmaking.matchmakingOptions.region = Matchmaking.matchmakingOptions.region - nRegion
	else
		-- If the region is currently disabled, enable it
		Matchmaking.matchmakingOptions.region = Matchmaking.matchmakingOptions.region + nRegion
	end
	UpdateRegions()
	UpdateMatchmakingSettings()
end

local function EnableRegions(regions)
	for _, region in ipairs(regions) do
		for _, r in ipairs(regionList) do
			if r.key == region then
				local button = Main:GetWidget('region_select_button' .. region)
				button:SetEnabled(true)
				if #regions == 1 then
					button:SetButtonNumStates(1)
				else
					button:SetButtonNumStates(2)
				end

				local overlay = Main:GetWidget('region_disabled_overlay' .. region)
				overlay:SetVisible(false)
				
				-- Enable percentage panel styling
				local percentageDisabled = Main:GetWidget('matchmaking_flag_percentage_disabled' .. region)
				
				if percentageDisabled then
					percentageDisabled:SetVisible(false)
				end
			end
		end
	end
end

local function SetLocalRegions(region)
	Matchmaking.matchmakingOptions.region = region
	UpdateRegions()
end

local function UpdateRatingVisibility(widgetData, rankedCaldavarEnabled, rankedMidwarsEnabled)
	-- Both MMRs always show now (icons label them); players queue multiple modes so both stay relevant.
	widgetData.filled.caldavarRating:SetVisible(true)
	widgetData.filled.midwarsRating:SetVisible(true)
end

local function UpdateModes()
	-- If Matchmaking.matchmakingOptions.mode has a one or fewer bits set somewhere, set SetButtonNumStates to 1, otherwise 2, this is to prevent disabling all modes
	local mode = Matchmaking.matchmakingOptions.mode
	local numModesSelected = 0
	for _, r in ipairs(modeList) do
		if BitTest(Matchmaking.matchmakingOptions.mode, r.key) then
			numModesSelected = numModesSelected + 1
		end
	end

	local modes = {}
	for _, r in ipairs(modeList) do
		local key = r.key
		local isEnabled = Matchmaking.matchmakingOptions.mode % (key * 2) >= key

		modeObjects[key].button:SetButtonState(isEnabled and 0 or 1)
		
		-- Update percentage panel disabled state
		local modeRoot = modeObjects[key] and modeObjects[key].root
		local percentageDisabled = modeRoot and modeRoot:GetChildWidget('matchmaking_mode_percentage_disabled' .. key)
		if percentageDisabled then
			percentageDisabled:SetVisible(not isEnabled)
		end

	end

	local rankedCaldavarEnabled = BitTest(Matchmaking.matchmakingOptions.mode, MatchmakingMode.RankedCaldavar)
	local rankedMidwarsEnabled = BitTest(Matchmaking.matchmakingOptions.mode, MatchmakingMode.RankedMidwars)
		or BitTest(Matchmaking.matchmakingOptions.mode, MatchmakingMode.RankedMidwarsBanning)

	-- our rating
	UpdateRatingVisibility(hostObject, rankedCaldavarEnabled, rankedMidwarsEnabled)

	-- our friends' ratings
	for i = 0, 3 do
	    UpdateRatingVisibility(playerObjects[i], rankedCaldavarEnabled, rankedMidwarsEnabled)
	end

	-- if modes have changed, the queue button may need to be enabled/disabled
	UpdateQueueUI()

	-- switching between ranked and unranked changes which regions may be selected
	UpdateRegions()

	UpdateUnrankedOverlays()
end

-- A single-bit mode the player isn't currently permitted to queue. Both MidWars ranked drafts share the MidWars
-- ranked permission; Caldavar has its own; unranked is always permitted.
local function IsRankedModeAllowed(mode)
	if BitTest(mode, MatchmakingMode.RankedCaldavar) then
		return mm_allowRankedCaldavar
	end
	if BitTest(mode, MatchmakingMode.RankedMidwars) or BitTest(mode, MatchmakingMode.RankedMidwarsBanning) then
		return mm_allowRankedMidwars
	end
	return true
end

-- Normalize an authoritative mask (server echo / saved settings). Any combination of modes is queueable now, so
-- keep every selected bit, only dropping ranked modes the player isn't currently allowed to play.
local function SetLocalModes(modes)
	modes = tonumber(modes) or 0

	if not mm_allowRankedCaldavar and BitTest(modes, MatchmakingMode.RankedCaldavar) then
		modes = modes - MatchmakingMode.RankedCaldavar
	end
	if not mm_allowRankedMidwars and BitTest(modes, MatchmakingMode.RankedMidwars) then
		modes = modes - MatchmakingMode.RankedMidwars
	end
	if not mm_allowRankedMidwars and BitTest(modes, MatchmakingMode.RankedMidwarsBanning) then
		modes = modes - MatchmakingMode.RankedMidwarsBanning
	end

	-- Never leave the player with nothing queueable.
	if modes ~= 0 then
		Matchmaking.matchmakingOptions.mode = modes
	end

	UpdateModes()
end

local function ToggleMode(mode)
	mode = tonumber(mode)

	local current = Matchmaking.matchmakingOptions.mode
	local selecting = not BitTest(current, mode)

	-- Don't let a player select a ranked mode they aren't currently allowed to play.
	if selecting and not IsRankedModeAllowed(mode) then
		return
	end

	if selecting then
		current = current + mode
	else
		current = current - mode
	end

	-- Deselecting the last remaining mode would leave nothing queueable, so keep it selected.
	if current == 0 then
		current = mode
	end

	Matchmaking.matchmakingOptions.mode = current
	StripDisallowedUnrankedRegions()
	UpdateModes()
	UpdateMatchmakingSettings()
end

local function EnableModes(modes)
	for _, mode in ipairs(modes) do
		for _, r in ipairs(modeList) do
			if r.key == mode then
				local button = Main:GetWidget('mode_select_button' .. mode)
				button:SetEnabled(true)
				button:SetVisible(true)
				if #modes == 1 then
					button:SetButtonNumStates(1)
				else
					button:SetButtonNumStates(2)
				end

				local modeRoot = modeObjects[mode] and modeObjects[mode].root
				local overlay = modeRoot and modeRoot:GetChildWidget('mode_disabled_overlay' .. mode)
				if overlay then
					overlay:SetVisible(false)
				end
				
				-- Enable percentage panel styling
				local percentageDisabled = modeRoot and modeRoot:GetChildWidget('matchmaking_mode_percentage_disabled' .. mode)
				
				if percentageDisabled then
					percentageDisabled:SetVisible(false)
				end

			end
		end
	end
end

local function SpawnRegions()

	for i, regionData in ipairs(regionList) do
		regionRoot:AddTemplateListItem(flagTemplate, regionData.key, 'flag', regionData.key, 'region', regionData.label or 'Region')
		-- Initially hide all items until populated
		regionRoot:HideItemByValue(regionData.key)
		
		local iconWidget = Main:GetWidget(flagTemplate .. '_icon'..regionData.key)
		local rootWidget = Main:GetWidget(flagTemplate .. '_root'..regionData.key)
		local buttonWidget = Main:GetWidget('region_select_button' ..regionData.key)
		local codeWidget = Main:GetWidget(flagTemplate .. '_code'..regionData.key)

		-- store widgets in table
		if iconWidget then -- Removed frameWidget check
			flagObjects[regionData.key] = 
			{
				root = rootWidget,
				icon = iconWidget,
				button = buttonWidget,
				code = codeWidget
			}
		end
	end

end

local function SpawnModes()

	-- How many modes each Ranked/Unranked group has, so a 2-mode group lays them out side by side.
	local groupCounts = {}
	for _, m in ipairs(modeList) do
		local gk = m.mapName .. (m.isRanked and '_ranked' or '_unranked')
		groupCounts[gk] = (groupCounts[gk] or 0) + 1
	end

	local headerEmitted = {}
	local groupSlots = {}   -- groupKey -> { leftSlot, rightSlot } for 2-mode groups
	local groupIndex = {}

	for i, modeData in ipairs(modeList) do
		-- Determine which root to use based on mapName
		local targetRoot = (modeData.mapName == 'midwars') and modesMidwarsRoot or modesCaldavarRoot
		local groupKey = modeData.mapName .. (modeData.isRanked and '_ranked' or '_unranked')
		local count = groupCounts[groupKey]

		-- On the first mode of a group, emit its Ranked/Unranked divider and (for a 2-mode group) a two-slot row.
		if not headerEmitted[groupKey] then
			headerEmitted[groupKey] = true
			targetRoot:Instantiate('matchmaking_mode_group_header', 'key', groupKey, 'label', '')
			local headerLabel = Main:GetWidget('matchmaking_mode_group_header_label' .. groupKey)
			if headerLabel then
				headerLabel:SetText(modeData.isRanked and Translate('general_mode_ranked') or Translate('general_mode_unranked'))
			end
			if count >= 2 then
				targetRoot:Instantiate('matchmaking_mode_row', 'key', groupKey)
				groupSlots[groupKey] = {
					Main:GetWidget('matchmaking_mode_slotL' .. groupKey),
					Main:GetWidget('matchmaking_mode_slotR' .. groupKey),
				}
			end
			groupIndex[groupKey] = 0
		end

		-- A 2-mode group fills the left slot then the right; a lone mode fills the column.
		local idx = groupIndex[groupKey]
		groupIndex[groupKey] = idx + 1
		local container = (count >= 2) and groupSlots[groupKey][idx + 1] or targetRoot

		if count >= 2 then
			-- Narrow side-by-side cards use a smaller title so it clears the toggle badge.
			container:Instantiate(modeTemplate, 'mode', modeData.key, 'map', 'map_' .. modeData.mapName, 'titlestyle', 'h5')
		else
			container:Instantiate(modeTemplate, 'mode', modeData.key, 'map', 'map_' .. modeData.mapName)
		end

		local modeRoot = Main:GetWidget(modeTemplate .. '_root'..modeData.key)
		local mapNameLabel = Main:GetWidget(modeTemplate .. '_mapname'..modeData.key)
		local modeNameLabel = Main:GetWidget(modeTemplate .. '_modename'..modeData.key)
		local playersLabel = Main:GetWidget(modeTemplate .. '_players'..modeData.key)
		local rankedLabel = Main:GetWidget(modeTemplate .. '_ranked_label'..modeData.key)

		local iconWidget = Main:GetWidget(modeTemplate .. '_modeicon'..modeData.key)
		local modeButtonWidget = Main:GetWidget('mode_select_button' .. modeData.key)

		if mapNameLabel and iconWidget then
			-- store widgets in table
			modeObjects[modeData.key] = 
			{
				root = modeRoot,
				mapName = mapNameLabel,
				modeName = modeNameLabel,
				players = playersLabel,
				rankedLabel = rankedLabel,
				icon = iconWidget,
				button = modeButtonWidget,
			}
		end
		
	end

end

local function SpawnPlayers()
	
	for i = 0, 3 do
	
		playersRoot:Instantiate(playerTemplate, 'id', i)
		
		local filledWidget = Main:GetWidget(playerTemplate .. '_filled_root' .. i)
		local emptyWidget = Main:GetWidget(playerTemplate .. '_empty_root' .. i)
		local playerIcon = Main:GetWidget(playerTemplate .. '_icon' .. i)
		local playerCrown = Main:GetWidget(playerTemplate .. '_crown' .. i)
		local playerName = Main:GetWidget(playerTemplate .. '_name' .. i)
		local caldavarRating = Main:GetWidget(playerTemplate .. '_caldavar_rating' .. i)
		local midwarsRating = Main:GetWidget(playerTemplate .. '_midwars_rating' .. i)
		local kickBtn = Main:GetWidget(playerTemplate .. '_kick_btn' .. i)
		local leaveBtn = Main:GetWidget(playerTemplate .. '_leave_btn' .. i)
		local roleIcon = Main:GetWidget(playerTemplate .. '_top_role' .. i)
		local addBtn = Main:GetWidget(playerTemplate .. '_add_btn' .. i)

		playerObjects[i] = 
		{
			filled = 
			{
				root = filledWidget,
				icon = playerIcon,
				name = playerName,
				caldavarRating = caldavarRating,
				midwarsRating = midwarsRating,
				kick = kickBtn,
				leave = leaveBtn,
				add = addBtn,
				role = roleIcon,
			},
			empty = 
			{
				root = emptyWidget
			},
		}
	end

	hostObject =
	{
		filled = 
		{
			root = nil,
			icon = hostPlayerLeaderIcon,
			name = hostPlayerNameLabel,
			caldavarRating = hostPlayerCaldavarRatingLabel,
			midwarsRating = hostPlayerMidwarsRatingLabel,
			leave = hostLeaveGroupBtn,
			kick = hostPlayerKickBtn,
			add = hostPlayerAddFriendBtn,
			role = hostPlayerRoleIcon,
		},
		empty = 
		{
			root = nil,
		}
	}
	
end

-- Helper function to resize the region listbox based on the number of visible items
local function UpdateRegionListboxHeight()
	local numRegions = #regionList
	if numRegions <= 0 then return end
	
	-- Get listbox dimensions
	local listboxWidth = tonumber(regionRoot:GetWidth()) or 0
	local itemWidth = regionRoot:GetHeightFromString('11.5h') -- matches itemwidth in template
	local itemHeight = regionRoot:GetHeightFromString('3.1h') -- matches itemheight in template
	
	if listboxWidth <= 0 or itemWidth <= 0 then return end
	
	-- Calculate how many items fit per row
	local itemsPerRow = floor(listboxWidth / itemWidth)
	if itemsPerRow <= 0 then itemsPerRow = 1 end
	
	-- Calculate number of rows needed
	local numRows = ceil(numRegions / itemsPerRow)
	
	-- Set the listbox height to fit all rows
	local newHeight = numRows * itemHeight
	regionRoot:SetHeight(newHeight)
end

local function PopulateRegions()
	
	for i, regionData in ipairs(regionList) do
		-- Show the listbox item by its value (regionData.key)
		regionRoot:ShowItemByValue(regionData.key)
		flagObjects[regionData.key].icon:SetTexture('/ui/icons/flags/' .. regionData.texture)
		flagObjects[regionData.key].code:SetText(regionData.code)
	end

	local enabledRegionIds = {}
	for _, regionData in ipairs(regionList) do
		table.insert(enabledRegionIds, regionData.key)
	end
	EnableRegions(enabledRegionIds)
	UpdateRegions()

	-- Resize the listbox to fit all regions
	UpdateRegionListboxHeight()

	-- UpdateRegionListboxHeight bails out when the listbox has no resolved width yet, so it cannot be relied on to
	-- re-lay-out the panel. Recalculate explicitly: a changed region count re-wraps the rows, and the cascade up the
	-- grow chain keeps the section below it from being drawn over the flags.
	regionRoot:RecalculateSize()
end

local function ApplyRankedAllowOverlays()
	local rankedCaldavarRoot = modeObjects[MatchmakingMode.RankedCaldavar] and modeObjects[MatchmakingMode.RankedCaldavar].root
	local rankedCaldavarOverlay = rankedCaldavarRoot and rankedCaldavarRoot:GetChildWidget('mode_disabled_overlay' .. tostring(MatchmakingMode.RankedCaldavar))
	if rankedCaldavarOverlay then
		rankedCaldavarOverlay:SetVisible(not mm_allowRankedCaldavar)
	end

	local rankedMidwarsRoot = modeObjects[MatchmakingMode.RankedMidwars] and modeObjects[MatchmakingMode.RankedMidwars].root
	local rankedMidwarsOverlay = rankedMidwarsRoot and rankedMidwarsRoot:GetChildWidget('mode_disabled_overlay' .. tostring(MatchmakingMode.RankedMidwars))
	if rankedMidwarsOverlay then
		rankedMidwarsOverlay:SetVisible(not mm_allowRankedMidwars)
	end

	-- Banning Pick MidWars shares the MidWars ranked permission.
	local rankedMidwarsBanningRoot = modeObjects[MatchmakingMode.RankedMidwarsBanning] and modeObjects[MatchmakingMode.RankedMidwarsBanning].root
	local rankedMidwarsBanningOverlay = rankedMidwarsBanningRoot and rankedMidwarsBanningRoot:GetChildWidget('mode_disabled_overlay' .. tostring(MatchmakingMode.RankedMidwarsBanning))
	if rankedMidwarsBanningOverlay then
		rankedMidwarsBanningOverlay:SetVisible(not mm_allowRankedMidwars)
	end
end

-- show a placeholder in each map column when the catalog returns no modes for it (e.g. server maintenance)
local function UpdateEmptyModeLabels()
	local caldavarCount, midwarsCount = 0, 0
	for _, modeData in ipairs(modeList) do
		if modeData.mapName == 'midwars' then
			midwarsCount = midwarsCount + 1
		else
			caldavarCount = caldavarCount + 1
		end
	end
	if modesCaldavarEmptyLabel then modesCaldavarEmptyLabel:SetVisible(caldavarCount == 0) end
	if modesMidwarsEmptyLabel then modesMidwarsEmptyLabel:SetVisible(midwarsCount == 0) end
end

local function PopulateModes()

	for i, modeData in ipairs(modeList) do
		modeObjects[modeData.key].root:SetVisible(1)
		modeObjects[modeData.key].mapName:SetText(Translate('mode_'..modeData.serverKey))
		modeObjects[modeData.key].modeName:SetText(({['Role Pick']='Выбор ролей', ['Single Draft']='Одиночный выбор', ['Banning Pick']='Выбор с запретами'})[modeData.modeName] or modeData.modeName)
		modeObjects[modeData.key].players:SetText(modeData.playerCount)
		modeObjects[modeData.key].icon:SetTexture(modeData.icon)

		-- The card title is the draft mode; the Ranked/Unranked group header above the card conveys rankedness.
		if modeObjects[modeData.key].rankedLabel then
			modeObjects[modeData.key].rankedLabel:SetText(({['Role Pick']='Выбор ролей', ['Single Draft']='Одиночный выбор', ['Banning Pick']='Выбор с запретами'})[modeData.modeName] or modeData.modeName)
		end

		-- The draft is now the title, so hide the redundant "Mode: ..." subtitle.
		local modenamePanel = Main:GetWidget('matchmaking_mode_modename_panel' .. modeData.key)
		if modenamePanel then modenamePanel:SetVisible(false) end
	end

	local enabledModeIds = {}
	for _, modeData in ipairs(modeList) do
		table.insert(enabledModeIds, modeData.key)
	end
	EnableModes(enabledModeIds)
	UpdateModes()

	-- EnableModes just cleared the disabled overlays; reapply the last known ranked-allow state
	ApplyRankedAllowOverlays()

	UpdateEmptyModeLabels()

	-- The mode columns are grow_noinvis: they keep their old height until asked to resize, so a catalog that
	-- returns a different number of modes (unranked arriving alongside ranked) overflows the column and ends up
	-- underneath the statistics panel and queue button. RecalculateSize cascades up the grow chain.
	if modesCaldavarRoot then modesCaldavarRoot:RecalculateSize() end
	if modesMidwarsRoot then modesMidwarsRoot:RecalculateSize() end

	-- The teamsize label can change per catalog now; its panel keeps a construction-time percent-x/width
	-- (K2 only re-lays children whose parent's size changed), stranding "5v5" outside the narrow
	-- side-by-side cards. Re-derive it against the settled card geometry, parent row first.
	for _, modeData in ipairs(modeList) do
		local card = modeObjects[modeData.key] and modeObjects[modeData.key].root
		if card then card:RecalculateSize() end
		local detailsRow = Main:GetWidget('matchmaking_mode_details_row' .. modeData.key)
		if detailsRow then detailsRow:RecalculateSize() end
		local teamsizePanel = Main:GetWidget('matchmaking_mode_teamsize_panel' .. modeData.key)
		if teamsizePanel then teamsizePanel:RecalculateSize() end
	end
end

local function PopulateStatistics(stats)
	-- Online/in-queue counts now live on the system bar; keep only the queue value for mode/region percentages.
	playersInQueue = tonumber(stats[3]) or playersInQueue
end

function Matchmaking:OnRegionClicked(selectedFlag)
	ToggleRegion(selectedFlag)
	SaveOptions()
end

function Matchmaking:OnModeClicked(selectedMode)
	ToggleMode(tonumber(selectedMode))
	SaveOptions()
end

-- Reads the engine binding, not Store:GetProductData('AccountUpgrade') -- that table is
-- only filled when the store panel opens, so it is empty for a player who goes straight here.
-- Returns the purchasable upgrade, and whether one is already owned.
local function FindNewPlayerUpgrade()
	if not GetAccountUpgradeProducts then return nil, false end

	local products = GetAccountUpgradeProducts()
	if not products then return nil, false end

	local purchasable, owned = nil, false

	for i = 1, #products do
		local entry = products[i] and products[i][1]
		if entry and entry.liftsNewPlayerStatus then
			if entry.owned then
				owned = true
			elseif not purchasable then
				-- the store's purchase guards key off this; RefreshStoreData sets it the same way
				entry.productCategory = 'AccountUpgrade'
				purchasable = entry
			end
		end
	end

	return purchasable, owned
end

function Matchmaking:UpdateNewPlayerUpsell()
	if not npe.panelReady then return end

	local isNewPlayer = IsAccountNewPlayer ~= nil and IsAccountNewPlayer() or false
	local entry, upgradeOwned = nil, false
	if isNewPlayer then entry, upgradeOwned = FindNewPlayerUpgrade() end

	-- IsAccountNewPlayer is fetched once at login (c_clientaccount.cpp:570) and never
	-- refreshed, so it still reports true after buying the upgrade. Ownership is the live
	-- signal, and PurchaseItem only calls back once the inventory cache has refreshed.
	-- The restriction itself applies whether or not there is anything to sell, so only the
	-- CTA below depends on a purchasable product existing.
	npe.root:SetVisible(isNewPlayer and not upgradeOwned)
	npe.upgradeEntry = entry

	-- the divider only separates the copy from the button, so it goes with it
	npe.ctaCol:SetVisible(entry ~= nil)
	npe.ctaDivider:SetVisible(entry ~= nil)
	if not entry then return end

	-- reuse the store's resolution so the price cannot drift between surfaces
	local jadePrice = Store and Store.ResolveJadePrice and Store:ResolveJadePrice(entry) or nil

	-- ':jade:' is an inline emoji token from /shared/icons/icons.emojis
	if npe.ctaLabel then
		local label = Translate('mm_npe_cta')
		if jadePrice then
			label = label .. '  ' .. tostring(jadePrice) .. ' :jade:'
		end
		npe.ctaLabel:SetText(label)
	end
end

function Matchmaking:BuyAccountUpgrade()
	-- the banner shows with nothing to sell; clicking must then do nothing
	if not npe.upgradeEntry then return end
	if not Store or not Store.ShowPurchaseConfirmationWindow then return end

	-- dataOverride path: our entry comes from the engine binding, not the store's grid
	Store:ShowPurchaseConfirmationWindow('buy', nil, npe.upgradeEntry)
end

function Matchmaking:OnShow()
	-- older engine builds don't expose machine tag support
	if MatchmakingClient.RequestMachineTagStatus then
		MatchmakingClient.RequestMachineTagStatus()
	end

	-- PlayBanStatus fires once at login, which can be before this panel exists
	if MatchmakingClient.RefreshPlayBanStatus then
		MatchmakingClient.RefreshPlayBanStatus()
	end

	npe.panelReady = true
	Matchmaking:UpdateNewPlayerUpsell()
end

function Matchmaking:OnHide()
	--nothing
end

function Matchmaking:InvitePlayerButton(widget)
	Matchmaking.invitePlayerPanel:SetVisible(1)
	invitePlayerInput:SetFocus(true)
	invitePlayerInput:SetInputLine('')

	Matchmaking.invitePlayerPanel:SetAbsoluteY(widget:GetAbsoluteY() - widget:GetHeight())
	Matchmaking.invitePlayerPanel:SetAbsoluteX(widget:GetAbsoluteX() * 1.1)
end

function Matchmaking:ConfirmInvitePlayerBtn()
	PlaySound('/shared/sounds/ui/button_click_03.wav')

	Matchmaking.invitePlayerPanel:SetVisible(0)
	MatchmakingClient.InvitePlayerToMatchmakingGroup(invitePlayerInput:GetInputLine())
end

function Matchmaking:OnInviteInputChanged(widget)
	confirmInvitePlayerBtn:SetEnabled(NotEmpty(widget:GetInputLine()))
end

function Matchmaking:JoinOrLeaveQueueBtn()
	if Matchmaking.CurrentState == Enum.MatchmakingState.InQueue then
		if mm_condition == Enum.MatchmakingCondition.PenaltyQueue or mm_condition == Enum.MatchmakingCondition.PostPenaltyQueue then
			Matchmaking:ShowPenaltyWarningDialog()
		else
			MatchmakingClient.LeaveMatchmakingQueue()
		end
	else
		MatchmakingClient.EnterMatchmakingQueue(Matchmaking.matchmakingOptions.region, Matchmaking.matchmakingOptions.mode)
	end
end

function Matchmaking:ShowPenaltyWarningDialog()
	penaltyDialogConfirm:FadeIn(250)
end

local function RetagInputMatches(typed)
	return NotEmpty(machineTag.localUsername) and string.lower(typed) == string.lower(machineTag.localUsername)
end

function Matchmaking:ShowRetagDialog()
	retagDialogBodyLabel:SetText(Translate('mm_machine_tag_retag_confirm_body', 'days', tostring(machineTag.retagCooldownDays)))
	retagDialogPromptLabel:SetText(Translate('mm_machine_tag_retag_confirm_prompt', 'name', machineTag.localUsername))
	retagDialogErrorLabel:SetText('')
	retagDialogConfirmBtn:SetEnabled(false)
	retagDialogInput:SetInputLine('')
	retagDialog:FadeIn(250)
	retagDialogInput:SetFocus(true)
end

function Matchmaking:OnRetagInputChanged(widget)
	retagDialogConfirmBtn:SetEnabled(RetagInputMatches(widget:GetInputLine() or ''))
end

function Matchmaking:ConfirmRetagBtn()
	local typed = retagDialogInput:GetInputLine() or ''
	if not RetagInputMatches(typed) then
		return -- onenterlua fires regardless of the typed text
	end
	if MatchmakingClient.RetagMachine then
		MatchmakingClient.RetagMachine(typed)
		retagDialog:FadeOut(250)
		-- show a pending note until the refreshed MachineTagStatus arrives
		machineTag.retagPending = true
		UpdateMachineTagUI()
	end
end

----------------------------------------------------------
--						  Registers						--
----------------------------------------------------------

local function MatchmakingPlayerStatus(widgetData, index, data)
	if #data.displayName == 0 then
		if widgetData.empty.root then widgetData.empty.root:SetVisible(true) end -- show empty
		if widgetData.filled.root then widgetData.filled.root:SetVisible(false) end -- hide filled

		-- the following should not be necessary...
		widgetData.filled.leave:SetVisible(false)
		widgetData.filled.kick:SetVisible(false)
		widgetData.filled.add:SetVisible(false)
	else
		if widgetData.empty.root then widgetData.empty.root:SetVisible(false) end -- hide empty
		if widgetData.filled.root then widgetData.filled.root:SetVisible(true) end -- show filled

		widgetData.filled.name:SetText((data.isNewPlayer and ':newplayersprout: ' or '') .. data.displayName)

		widgetData.filled.caldavarRating:SetText(tostring(data.rankedCaldavarRating))
		widgetData.filled.midwarsRating:SetText(tostring(data.rankedMidwarsRating))

		widgetData.filled.icon:SetTexture(data.icon)
		widgetData.filled.icon:UICmd("SetRenderMode('normal')")
		widgetData.filled.leave:SetVisible(data.canLeave)
		widgetData.filled.kick:SetVisible(data.canBeKicked)
		widgetData.filled.add:SetVisible(data.canAddFriend)

		local rankedCaldavarEnabled = BitTest(Matchmaking.matchmakingOptions.mode, MatchmakingMode.RankedCaldavar)
		local rankedMidwarsEnabled = BitTest(Matchmaking.matchmakingOptions.mode, MatchmakingMode.RankedMidwars)

		UpdateRatingVisibility(widgetData, rankedCaldavarEnabled, rankedMidwarsEnabled)
	end

	local topRoleId = data.roles % 16
	local role = RolePick_Shared:GetRoleById(topRoleId)

	widgetData.filled.role:SetTexture('/ui/hd_ui/icons/' .. role.image)
	--widgetData.filled.role:SetColor(role.color)

	--accountId
	--username
	--slot
	--isLeader
	--chatNameColorf
	--chatNameTexturePath
	--chatNameGlow
	--isInGame
end

local function MatchmakingJoinGroup(groupId)
	SetMatchmakingState(Enum.MatchmakingState.InGroup)
end

local function MatchmakingLeaveGroup(groupName)
	SetMatchmakingState(Enum.MatchmakingState.NotInGroup)
end

local function MatchmakingJoinQueue()
	SetMatchmakingState(Enum.MatchmakingState.InQueue)

	-- entering a ranked queue tags the machine server-side, so refresh the status
	-- banner right away instead of waiting for the panel to be reopened
	if (machineTag.state == MachineTagState.Unknown or machineTag.state == MachineTagState.Untagged)
	and MatchmakingClient.RequestMachineTagStatus then
		MatchmakingClient.RequestMachineTagStatus()
	end
end

local function MatchmakingLeaveQueue()
	SetMatchmakingState(Enum.MatchmakingState.InGroup)
end

local function MatchmakingFoundMatch(matchID)
	PlaySound('/shared/sounds/ui/lobby/match_found.wav', 3.6)
	SetMatchmakingState(Enum.MatchmakingState.InGroup)
end

local function MatchmakingConnected()
	SetMatchmakingState(Enum.MatchmakingState.NotInGroup)
end

local function MatchmakingDisconnected()
	SetMatchmakingState(Enum.MatchmakingState.Offline)
end

local function MatchmakingPlayerJoinedGroup()
	PlaySound('/shared/sounds/ui/lobby/player_joined.wav')
end

local function MatchmakingRegions(...)
	-- Accept updated regions as packed parameters (region names)
	local regionNames = {...}
	
	local newRegions = 0

	-- Convert region names to region keys and collect enabled regions
	for _, regionName in ipairs(regionNames) do
		-- Find the region data by matching the label
		local foundRegion = false
		for _, regionData in ipairs(regionList) do
			if regionData.serverKey == regionName then
				foundRegion = true
				newRegions = newRegions + regionData.key
				break
			end
		end
		if not foundRegion then
			println("^yWarning: MatchmakingRegions received invalid region name: " .. tostring(regionName))
		end
	end
	
	SetLocalRegions(newRegions)
end

local function MatchmakingModes(...)
	-- Accept updated modes as packed parameters (mode names)
	local modeNames = {...}
	local newModes = 0

	-- Convert mode names to mode keys and collect enabled modes
	for _, modeName in ipairs(modeNames) do
		-- Find the mode data by matching the mapName (e.g., "caldavarphoenix", "midwars", "showdown")
		local foundMode = false
		for _, modeData in ipairs(modeList) do
			if modeData.serverKey == modeName then
				foundMode = true
				newModes = newModes + modeData.key
				break
			end
		end
		if not foundMode then
			println("^yWarning: MatchmakingModes received invalid mode name: " .. tostring(modeName))
		end
	end

	SetLocalModes(newModes)
end

local function MatchmakingBalanceStrictness(desiredBalanceStrictness)
	Matchmaking.matchmakingOptions.balanceMode = tonumber(desiredBalanceStrictness) < 0.5 and Matchmaking.BalanceMode.FastestQueue or Matchmaking.BalanceMode.BestBalance
	UpdateBalanceModeUI()
end

local function MatchmakingPenaltyPoints(penaltyPoints)
	mm_penaltyPoints = tonumber(penaltyPoints)
	UpdatePenaltyUI()
end

local function MatchmakingGroupNumPlayers(numPlayers)
	mm_numplayers = tonumber(numPlayers)
	UpdateNumPlayersUI()
end

local function MatchmakingRatingDisparityLimit(ratingDisparityLimit)
	rating_disparity_limit = ratingDisparityLimit
end

local function MatchmakingCaldavarDisallowReason(reason)
	mm_caldavarDisallowReason = tonumber(reason)
end

local function MatchmakingMidwarsDisallowReason(reason)
	mm_midwarsDisallowReason = tonumber(reason)
end

local function MatchmakingPlayerLeftGroup(kicked)
	if (AtoB(kicked)) then
		PlaySound('/shared/sounds/ui/lobby/player_kicked.wav')
	else
		PlaySound('/shared/sounds/ui/lobby/player_left.wav')
	end
end

local function MatchmakingRegionsData(regionsDataString)
	-- Parse regions data: "id,enabled,name,flag,players,allowsUnranked|..."
	if not regionsDataString or regionsDataString == "" then
		return
	end
	
	local newRegionList = {}
	
	-- collect data and calculate total players
	local regionDataList = {}
	for regionData in string.gmatch(regionsDataString, "[^|]+") do
		local parts = {}
		for part in string.gmatch(regionData, "[^,]+") do
			table.insert(parts, part)
		end
		
		if #parts >= 5 then
			local id = tonumber(parts[1])
			local enabled = parts[2] == "1"
			local name = parts[3]
			local flag = parts[4]
			local players = tonumber(parts[5]) or 0
			-- Absent on an older server: treat as not unranked-capable rather than silently allowing every region.
			local allowsUnranked = parts[6] == "1"

			if enabled then
				table.insert(regionDataList, {
					id = id,
					name = name,
					flag = flag,
					players = players,
					allowsUnranked = allowsUnranked
				})
			end
		end
	end
	
	-- create region list with normalized percentages
	for _, data in ipairs(regionDataList) do
		local denom = playersInQueue or 0
		local percentage = 0
		if denom > 0 then
			percentage = floor(((data.players or 0) / denom) * 100 + 0.5)
			if percentage > 100 then percentage = 100 end
			if percentage < 0 then percentage = 0 end
		end

		-- println(string.format("^y[MM] Region '%s': %d / %d = %d%% (playersInQueue=%d)", tostring(data.name), data.players or 0, denom, percentage, playersInQueue or 0))

		local texture = data.flag .. '.tga'
		local key = data.id
		local serverKey = data.name:gsub(' ', '')
		
		local stringKey = 'mm_region_code_' .. serverKey:lower()
		local code = Translate(stringKey)
		if code == stringKey then code = '' end
		
		table.insert(newRegionList, {
			key = key,
			label = data.name,
			serverKey = serverKey,
			texture = texture,
			players = data.players,
			percentage = percentage,
			allowsUnranked = data.allowsUnranked,
			code = code  -- Add region abbreviation code
		})
	end
	
	-- Check if we need to rebuild the UI (structure changed) or just update percentages
	local needsRebuild = false
	
	-- Compare with existing regionList to see if structure changed
	if #regionList ~= #newRegionList then
		needsRebuild = true
	else
		-- Check if any region's key or enabled state changed
		local oldRegionsByKey = {}
		for _, region in ipairs(regionList) do
			oldRegionsByKey[region.key] = region
		end
		
		for _, newRegion in ipairs(newRegionList) do
			local oldRegion = oldRegionsByKey[newRegion.key]
			if not oldRegion or oldRegion.label ~= newRegion.label or oldRegion.texture ~= newRegion.texture then
				needsRebuild = true
				break
			end
		end
	end
	
	-- Update the global regionList
	regionList = newRegionList
	
	if needsRebuild or not next(flagObjects) then
		-- Structure changed or first time - (re)build UI.
		-- Hidden leftovers would collide by name with the items SpawnRegions re-adds, breaking GetWidget lookups
		-- and row wrapping (the mode columns already carry the same fix).
		regionRoot:ClearItems()
		flagObjects = {}

		SpawnRegions()
		PopulateRegions()
	end
	
	-- Always update percentages
	for _, regionData in ipairs(regionList) do
		local percentageWidget = Main:GetWidget('matchmaking_flag_percentage' .. regionData.key)
		if percentageWidget then
			percentageWidget:SetText(regionData.percentage .. '%')
		end
	end
end

local function MatchmakingModesData(modesDataString)
	-- Parse modes data: "id,enabled,name,mode,teamsize,icon,players|id,enabled,name,mode,teamsize,icon,players|..."
	if not modesDataString or modesDataString == "" then
		return
	end
	
	local newModeList = {}
	
	-- collect data and calculate total players
	local modeDataList = {}
	for modeData in string.gmatch(modesDataString, "[^|]+") do
		local parts = {}
		for part in string.gmatch(modeData, "[^,]+") do
			table.insert(parts, part)
		end
		
		if #parts >= 7 then
			local id = tonumber(parts[1])
			local enabled = parts[2] == "1"
			local name = parts[3]
			local mode = parts[4]
			local teamsize = parts[5]
			local icon = parts[6]
			local players = tonumber(parts[7]) or 0
			
			if enabled then
				table.insert(modeDataList, {
					id = id,
					name = name,
					mode = mode,
					teamsize = teamsize,
					icon = icon,
					players = players
				})
			end
		end
	end
	
	-- create mode list with normalized percentages
	for _, data in ipairs(modeDataList) do
		local denom = playersInQueue or 0
		local percentage = 0
		if denom > 0 then
			percentage = floor(((data.players or 0) / denom) * 100 + 0.5)
			if percentage > 100 then percentage = 100 end
			if percentage < 0 then percentage = 0 end
		end

		-- Map mode names to map names for backwards compatibility
		local mapName = 'unknown'
		if string.find(data.name:lower(), 'caldavar') then
			mapName = 'caldavarphoenix'
		elseif string.find(data.name:lower(), 'midwars') then
			mapName = 'midwars'
		end
		
		-- Format icon path from server data (server sends "caldavarphoenix", we need "/maps/caldavarphoenix/icon.tga")
		local iconPath = '/maps/' .. data.icon .. '/icon.tga'
		
		local nameLower = data.name:lower()
		local isRanked = string.find(nameLower, 'unranked') == nil and string.find(nameLower, 'ranked') ~= nil

		local key = data.id
		table.insert(newModeList, {
			key = key,
			name = data.name,  -- Add original name for ranked/unranked detection
			isRanked = isRanked,
			mapName = mapName,
			serverKey = data.name:gsub(' ', ''),  -- Remove spaces for serverKey
			modeName = data.mode,
			playerCount = data.teamsize,
			icon = iconPath,
			players = data.players,
			percentage = percentage
		})
	end

	-- Group ranked modes before unranked ones within each map column; keep the server order as a stable tiebreak.
	for i, m in ipairs(newModeList) do m._order = i end
	table.sort(newModeList, function(a, b)
		if a.isRanked ~= b.isRanked then
			return a.isRanked
		end
		return a._order < b._order
	end)
	
	-- Check if we need to rebuild the UI (structure changed) or just update percentages
	local needsRebuild = false
	
	-- Compare with existing modeList to see if structure changed
	if #modeList ~= #newModeList then
		needsRebuild = true
	else
		-- Check if any mode's key or properties changed
		local oldModesByKey = {}
		for _, mode in ipairs(modeList) do
			oldModesByKey[mode.key] = mode
		end
		
		for _, newMode in ipairs(newModeList) do
			local oldMode = oldModesByKey[newMode.key]
			if not oldMode or oldMode.mapName ~= newMode.mapName or oldMode.modeName ~= newMode.modeName or oldMode.icon ~= newMode.icon then
				needsRebuild = true
				break
			end
		end
	end
	
	-- Update the global modeList
	modeList = newModeList
	
	if needsRebuild or not next(modeObjects) then
		-- Structure changed or first time - (re)build UI
		-- Destroy any previously instantiated mode widgets before respawning; hiding them
		-- leaves stale duplicates with identical names, breaking GetWidget lookups and grow sizing
		modesCaldavarRoot:ClearChildren()
		modesMidwarsRoot:ClearChildren()
		modeObjects = {}

		SpawnModes()
		PopulateModes()
	end
	
	-- Always update percentages (whether rebuilt or not)
	for _, modeData in ipairs(modeList) do
		local percentageWidget = Main:GetWidget('matchmaking_mode_percentage' .. modeData.key)
		if percentageWidget then
			percentageWidget:SetText(modeData.percentage .. '%')
		end
	end
end

local function MachineTagStatus(state, taggedAccountName, canRetag, nextRetagAt, serverTime, retagCooldownDays, localUsername)
	machineTag.state = tonumber(state) or MachineTagState.Unknown
	machineTag.taggedAccountName = taggedAccountName or ''
	machineTag.canRetag = tostring(canRetag) == '1'
	machineTag.nextRetagAt = tonumber(nextRetagAt) or 0
	machineTag.serverTime = tonumber(serverTime) or 0
	machineTag.retagCooldownDays = tonumber(retagCooldownDays) or 0
	machineTag.localUsername = localUsername or ''
	machineTag.retagPending = false

	-- pin cooldown math to server time; the local clock only advances it
	if os and os.time and machineTag.serverTime > 0 then
		machineTag.clockOffset = machineTag.serverTime - os.time()
	end

	UpdateMachineTagUI()
	UpdateQueueUI()
end

local function MachineTagQueueDenied(...)
	-- one param per blocked group member: "displayName|verdict|taggedAccountDisplayName"
	local blockedNames = {}
	local reasons = {}

	for _, entry in ipairs({...}) do
		local parts = {}
		for part in string.gmatch(tostring(entry), '[^|]+') do
			tinsert(parts, part)
		end

		local displayName = parts[1] or ''
		local verdict = tonumber(parts[2]) or 0
		local taggedAccountName = parts[3] or ''

		if NotEmpty(displayName) then
			tinsert(blockedNames, displayName)
			if verdict == 2 then
				tinsert(reasons, Translate('mm_machine_tag_denied_reason_other', 'name', displayName, 'tagged', taggedAccountName))
			elseif verdict == 4 then
				tinsert(reasons, Translate('mm_machine_tag_denied_reason_shared', 'name', displayName))
			else
				tinsert(reasons, Translate('mm_machine_tag_denied_reason_unknown', 'name', displayName))
			end
		end
	end

	if #blockedNames == 0 then return end

	SetNoticeLabel(Translate('mm_machine_tag_denied_notice', 'names', tconcat(blockedNames, ', ')), Enum.ErrorType.Error)

	for i = 1, 5 do
		machineTagDeniedLines[i]:SetText(reasons[i] or '')
		machineTagDeniedLines[i]:SetVisible(reasons[i] ~= nil)
	end
	machineTagDeniedDialog:FadeIn(250)
end

function Matchmaking:RolesChangedLocally()
	UpdateQueueUI()
end





local function PartyQueueEligibility(...)
	partyRefusals = {}

	for _, entry in ipairs({...}) do
		local modeBit, available, reason, reasonKey, reasonText = string.match(tostring(entry), '^([^|]*)|([^|]*)|([^|]*)|([^|]*)|(.*)$')
		modeBit = tonumber(modeBit) or 0

		if modeBit ~= 0 and not AtoB(available or 'false') then
			partyRefusals[modeBit] = { reason = tonumber(reason) or 0, key = reasonKey or '', text = reasonText or '' }
		end
	end

	UpdateQueueUI()
end

local function PlayBanStatus(active, reason, endsAt, blocksPublicLobbies)
	playBan.active = AtoB(active or 'false')
	playBan.reason = reason or ''
	playBan.endsAt = tonumber(endsAt) or 0
	playBan.blocksPublicLobbies = AtoB(blocksPublicLobbies or 'false')

	UpdateQueueUI()
end

local function PlayBanQueueDenied(...)
	-- one param per blocked group member: "displayName|endsAt|blocksPublicLobbies|reason"
	local blockedNames = {}
	local reasons = {}

	for _, entry in ipairs({...}) do
		-- Matched as a whole rather than split on '|', because the reason is free text that may
		-- contain the separator and any field before it may be empty.
		local displayName, endsAt, _, reason = string.match(tostring(entry), '^([^|]*)|([^|]*)|([^|]*)|(.*)$')

		if displayName and NotEmpty(displayName) then
			tinsert(blockedNames, displayName)

			local reasonText = PlayBanReasonText(reason)
			endsAt = tonumber(endsAt) or 0
			if endsAt > 0 then
				tinsert(reasons, Translate('mm_play_ban_denied_reason_temporary', 'name', displayName, 'reason', reasonText, 'remaining', PlayBanRemainingText(endsAt)))
			else
				tinsert(reasons, Translate('mm_play_ban_denied_reason_permanent', 'name', displayName, 'reason', reasonText))
			end
		end
	end

	if #blockedNames == 0 then return end

	SetNoticeLabel(Translate('mm_play_ban_denied_notice', 'names', tconcat(blockedNames, ', ')), Enum.ErrorType.Error)

	for i = 1, 5 do
		playBanDeniedLines[i]:SetText(reasons[i] or '')
		playBanDeniedLines[i]:SetVisible(reasons[i] ~= nil)
	end
	playBanDeniedDialog:FadeIn(250)
end

local function MachineTagRetagError(message)
	machineTag.retagPending = false
	local errorText = (message and NotEmpty(message)) and message or Translate('mm_machine_tag_retag_error_generic')
	if retagDialog:IsVisible() then
		retagDialogErrorLabel:SetText(errorText)
	else
		SetNoticeLabel(errorText, Enum.ErrorType.Error)
	end
	UpdateMachineTagUI()
end

local function MatchmakingCondition(condition, cooldown, allowRankedCaldavar, allowRankedMidwars)

	-- normalize condition (accepts number or string enum key)
	local newCondition = tonumber(condition)
	if not newCondition and type(condition) == 'string' and Enum and Enum.MatchmakingCondition then
		newCondition = Enum.MatchmakingCondition[condition]
	end

	-- default to normal if invalid
	if type(newCondition) ~= 'number' then
		newCondition = Enum.MatchmakingCondition.Normal
	end

	mm_condition = newCondition
	mm_cooldown = (cooldown ~= nil and cooldown ~= '') and cooldown or ''
	mm_allowRankedCaldavar = AtoB(allowRankedCaldavar)
	mm_allowRankedMidwars = AtoB(allowRankedMidwars)

	ApplyRankedAllowOverlays()

	UpdateQueueUI()
end

----------------------------------------------------------
--						   Init							--
----------------------------------------------------------

function Matchmaking:Init()
	WExt:ProcessInitWidgets(Matchmaking, Main)

	-- balance checkbox default
	if Matchmaking.matchmakingOptions.balanceMode == nil then
		Matchmaking.matchmakingOptions.balanceMode = Matchmaking.BalanceMode.BestBalance
	end

	-- start disconnected
	if Matchmaking.init == false then
		Matchmaking.init = true
	else
		MatchmakingDisconnected()
	end

	if Matchmaking.matchmakingOptions.region == 0 then
		Matchmaking.matchmakingOptions.region = 3 -- default to EU + NA
	end

	if Matchmaking.matchmakingOptions.mode == 0 then
		Matchmaking.matchmakingOptions.mode = MatchmakingMode.RankedCaldavar -- default to Caldavar Phoenix
	end

	-- synchronize C++ state with LUA state
	UpdateMatchmakingSettings()

	-- apply saved balance mode to UI
	UpdateBalanceModeUI()

	SpawnPlayers()

	interface:RegisterWatchLua('matchmakingplayerstatus0', function(_, data)
		MatchmakingPlayerStatus(hostObject, 0, data)
		-- you can't registerwatchlua in a different file from the same watch.
		-- that's messed up, so, here's a hack
		SystemBar:SetPlayerMMR("FoC: " .. tostring(data.rankedCaldavarRating) .. " MW: " .. tostring(data.rankedMidwarsRating))
		SystemBar:SetPlayerIcon(data.icon)
	end)

	interface:RegisterWatchLua('matchmakingplayerstatus1', function(_, data)
		MatchmakingPlayerStatus(playerObjects[0], 1, data)
	end)

	interface:RegisterWatchLua('matchmakingplayerstatus2', function(_, data)
		MatchmakingPlayerStatus(playerObjects[1], 2, data)
	end)

	interface:RegisterWatchLua('matchmakingplayerstatus3', function(_, data)
		MatchmakingPlayerStatus(playerObjects[2], 3, data)
	end)

	interface:RegisterWatchLua('matchmakingplayerstatus4', function(_, data)
		MatchmakingPlayerStatus(playerObjects[3], 4, data)
	end)

	interface:RegisterWatch("MatchmakingCondition", function(_, ...) MatchmakingCondition(...) end)
	interface:RegisterWatch("MatchmakingJoinGroup", function(_, ...) MatchmakingJoinGroup(...) end)
	interface:RegisterWatch("MatchmakingLeaveGroup", function(_, ...) MatchmakingLeaveGroup(...) end)
	interface:RegisterWatch("MatchmakingJoinQueue", function(_, ...) MatchmakingJoinQueue(...) end)
	interface:RegisterWatch("MatchmakingLeaveQueue", function(_, ...) MatchmakingLeaveQueue(...) end)
	interface:RegisterWatch("MatchmakingFoundMatch", function(_, ...) MatchmakingFoundMatch(...) end)
	interface:RegisterWatch("MatchmakingConnected", function(_, ...) MatchmakingConnected(...) end)
	interface:RegisterWatch("MatchmakingDisconnected", function(_, ...) MatchmakingDisconnected(...) end)
	interface:RegisterWatch("MatchmakingPlayerLeftGroup", function(_, ...) MatchmakingPlayerLeftGroup(...) end)
	interface:RegisterWatch("MatchmakingPlayerJoinedGroup", function(_, ...) MatchmakingPlayerJoinedGroup(...) end)
	interface:RegisterWatch("MatchmakingRegions", function(_, ...) MatchmakingRegions(...) end)
	interface:RegisterWatch("MatchmakingModes", function(_, ...) MatchmakingModes(...) end)
	interface:RegisterWatch("MatchmakingBalanceStrictness", function(_, ...) MatchmakingBalanceStrictness(...) end)
	interface:RegisterWatch("MatchmakingPenaltyPoints", function(_, ...) MatchmakingPenaltyPoints(...) end)
	interface:RegisterWatch("MatchmakingGroupNumPlayers", function(_, ...) MatchmakingGroupNumPlayers(...) end)
	interface:RegisterWatch("MatchmakingRatingDisparityLimit", function(_, ...) MatchmakingRatingDisparityLimit(...) end)
	interface:RegisterWatch("MatchmakingCaldavarDisallowReason", function(_, ...) MatchmakingCaldavarDisallowReason(...) end)
	interface:RegisterWatch("MatchmakingMidwarsDisallowReason", function(_, ...) MatchmakingMidwarsDisallowReason(...) end)
	interface:RegisterWatch("MachineTagStatus", function(_, ...) MachineTagStatus(...) end)
	interface:RegisterWatch("MachineTagQueueDenied", function(_, ...) MachineTagQueueDenied(...) end)
	interface:RegisterWatch("MachineTagRetagError", function(_, ...) MachineTagRetagError(...) end)
	interface:RegisterWatch("PlayBanStatus", function(_, ...) PlayBanStatus(...) end)
	interface:RegisterWatch("PlayBanQueueDenied", function(_, ...) PlayBanQueueDenied(...) end)
	interface:RegisterWatch("PartyQueueEligibility", function(_, ...) PartyQueueEligibility(...) end)
	interface:RegisterWatch("MatchmakingRoleTokens", function(_, ...) RoleTokens:OnBalance(...) UpdateQueueUI() end)
	interface:RegisterWatch("MatchmakingPartyDisparity", function(_, ...) RoleTokens:OnDisparity(...) UpdateQueueUI() end)

	-- ShopProductStore populates asynchronously after login; a new player who reaches
	-- matchmaking before it arrives would otherwise see the upsell banner stay hidden
	-- for the rest of the session, since OnShow only re-evaluates it once per visit
	interface:RegisterWatch('ShopProductsRefreshed', function() Matchmaking:UpdateNewPlayerUpsell() end)
	-- catches the buy itself: FinishPurchaseAttempt broadcasts nothing, so without this the
	-- banner keeps advertising an upgrade the player already owns until they leave the screen
	interface:RegisterWatch('PlayerCurrency', function() Matchmaking:UpdateNewPlayerUpsell() end)

	-- later populated from infra
	PopulateRegions()
	PopulateModes()

	local function setPlayersInQueue(stat)
		-- Value drives mode/region percentages; the visible count is shown on the system bar.
		playersInQueue = tonumber(stat)
	end
	interface:RegisterWatch("MatchmakingUsersInQueue", function(_, stat) setPlayersInQueue(stat) end)
	interface:RegisterWatch("MatchmakingQueueTime", function(_, ...) Matchmaking:SetMatchmakingQueueTime(...) end)
	interface:RegisterWatch("MatchmakingRegionsData", function(_, dataString) MatchmakingRegionsData(dataString) end)
	interface:RegisterWatch("MatchmakingModesData", function(_, dataString) MatchmakingModesData(dataString) end)
	
	--
	--interface:RegisterWatch("MatchmakingLeaveGroup", function(...) Matchmaking:MatchmakingLeaveGroup(...) end)
	--
	--interface:RegisterWatch("MatchmakingLeaveQueue", function(...) Matchmaking:MatchmakingLeaveQueue(...) end)
	--interface:RegisterWatch("MatchmakingFoundMatch", function(...) Matchmaking:MatchmakingFoundMatch(...) end)
	--interface:RegisterWatch("LoginStatus", function(...) Matchmaking:Reset(...) end)
	--Matchmaking:Reset()

	SetMatchmakingState(Matchmaking.CurrentState)

	-- color handled by button_hd_deepblue template

end

function Matchmaking:LeaveGroup()
	MatchmakingClient.LeaveMatchmakingGroup()
end

function Matchmaking:KickPlayer(index)
	MatchmakingClient.KickPlayerFromMatchmakingGroup(index)
end

function Matchmaking:AddFriend(index)
	MatchmakingClient.AddFriend(index)
end

function Matchmaking:SetMatchmakingQueueTime(time)
	mm_queueTime = time
	UpdateQueueUI()
end

function Matchmaking:PopulateRoles(index)
	local roles = MatchmakingClient.GetPlayerRoles(index)

	for id = 1, 7 do
		local roleId = roles % 16
    	roles = math.floor(roles / 16)

		local role = RolePick_Shared:GetRoleById(roleId)
		local roleIcon = Main:GetWidget('matchmaking_player_role_pref_image_' .. id)

		roleIcon:SetTexture('/ui/hd_ui/icons/' .. role.image)
		--roleIcon:SetColor(role.color)

		local roleLabel = Main:GetWidget('matchmaking_player_role_pref_name_' .. id)
		roleLabel:SetText(Translate('player_role_' .. role.name))
	end
	rolesTooltip:SetVisible(true)
end

function Matchmaking:ShowModeDisabledTooltip(widget, mode)
	local tooltipText
	local maxWidth
	if mode == MatchmakingMode.RankedCaldavar and not mm_allowRankedCaldavar then
		tooltipText = ModeRefusalText(mode) or DisallowReasonText(mm_caldavarDisallowReason)
		maxWidth = '36h'
	elseif (mode == MatchmakingMode.RankedMidwars or mode == MatchmakingMode.RankedMidwarsBanning) and not mm_allowRankedMidwars then
		tooltipText = ModeRefusalText(mode) or DisallowReasonText(mm_midwarsDisallowReason)
		maxWidth = '36h'
	else
		tooltipText = Translate('options_disabled')
		maxWidth = nil
	end
	Tooltips:TooltipHover_Main(widget, tooltipText, 'top', maxWidth)
end
