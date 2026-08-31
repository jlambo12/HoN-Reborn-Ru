local _G = getfenv(0)
local interface = object

HoNPlusLive = _G['HoNPlusLive'] or {}
HoNPlusLive.stats = { kills=0, deaths=0, assists=0, cs=0, denies=0, level=1, gpm=0 }
HoNPlusLive.matchTimeMs = 0
HoNPlusLive.heroId = nil
HoNPlusLive.localSlot = nil
HoNPlusLive.role = nil
HoNPlusLive.manualRole = nil
HoNPlusLive.expanded = true
HoNPlusLive.initialized = false

local ROLE_IDS = { carry=1, mid=2, offlane=3, softsupport=4, hardsupport=5, soloofflane=6, jungle=7 }
local ROLE_NAMES = { [1]='КЕРРИ', [2]='МИД', [3]='ОФФЛЕЙН', [4]='САППОРТ 4', [5]='САППОРТ 5', [6]='СОЛО ОФФЛЕЙН', [7]='ЛЕС' }
local PERCENTILES = { 0, 10, 25, 50, 75, 90, 100 }

local function Widget(name)
    return Game:GetWidget('honplus_live_' .. name)
end

local function SetText(name, value)
    local widget = Widget(name)
    if widget then widget:SetText(value) end
end

local function Clamp(value, low, high)
    return math.max(low, math.min(high, value))
end

local function Lerp(a, b, amount)
    return a + (b - a) * amount
end

local function ResolveHeroId(displayName)
    if HoNPlusLive.heroId then return HoNPlusLive.heroId end
    if Testing and Testing.GetPlayerHeroIndex and Testing.GetEntityInfo then
        local okIndex, entityId = pcall(Testing.GetPlayerHeroIndex, GetLocalClientNumber())
        if okIndex and entityId then
            local okInfo, info = pcall(Testing.GetEntityInfo, entityId)
            if okInfo and info and info.typeName then
                HoNPlusLive.heroId = HoNPlusLiveData.heroes[string.lower(info.typeName)]
            end
        end
    end
    if not HoNPlusLive.heroId and displayName then
        HoNPlusLive.heroId = HoNPlusLiveData.heroes[string.lower(displayName)]
    end
    return HoNPlusLive.heroId
end

local function ResolveRole()
    if HoNPlusLive.manualRole then return HoNPlusLive.manualRole end
    local rawRole = GetLocalPlayerRole and GetLocalPlayerRole() or ''
    local numericRole = tonumber(rawRole)
    if numericRole and numericRole >= 1 and numericRole <= 7 then
        HoNPlusLive.role = numericRole
        return HoNPlusLive.role
    end
    local role = string.lower(tostring(rawRole))
    role = string.gsub(role, '_', '')
    HoNPlusLive.role = ROLE_IDS[role] or HoNPlusLive.role or 1
    return HoNPlusLive.role
end

local function InterpolatedGroup()
    local hero = HoNPlusLiveData.benchmarks[ResolveHeroId() or -1]
    local role = hero and hero[ResolveRole()]
    if not role then return nil, nil, nil end
    local minute = math.max(0, HoNPlusLive.matchTimeMs / 60000)
    local lowerMinute = math.floor(minute / 5) * 5
    local upperMinute = math.max(5, math.ceil(minute / 5) * 5)
    while upperMinute > 5 and not role[upperMinute] do upperMinute = upperMinute - 5 end
    if lowerMinute > upperMinute then lowerMinute = upperMinute end
    while lowerMinute > 0 and not role[lowerMinute] do lowerMinute = lowerMinute - 5 end
    local upper = role[upperMinute]
    local lower = lowerMinute > 0 and role[lowerMinute] or nil
    if not upper then return nil, nil, nil end
    local amount = lowerMinute == upperMinute and 0 or Clamp((minute - lowerMinute) / (upperMinute - lowerMinute), 0, 1)
    return lower, upper, amount
end

local function Metric(metric)
    local lower, upper, amount = InterpolatedGroup()
    if not upper or not upper[metric] then return nil end
    local values = {}
    for index=1,7 do
        local low = lower and lower[metric] and lower[metric][index] or 0
        values[index] = Lerp(low, upper[metric][index], amount)
    end
    return values, math.floor(Lerp(lower and lower.n or 0, upper.n or 0, amount) + .5)
end

local function Percentile(value, thresholds, lowerIsBetter)
    if not thresholds then return nil end
    if thresholds[1] == thresholds[7] and value == thresholds[1] then return 50 end
    local result = 50
    if value <= thresholds[1] then result = 0
    elseif value >= thresholds[7] then result = 100
    else
        for index=1,6 do
            if value <= thresholds[index + 1] then
                local span = thresholds[index + 1] - thresholds[index]
                local amount = span <= 0 and 0.5 or (value - thresholds[index]) / span
                result = Lerp(PERCENTILES[index], PERCENTILES[index + 1], amount)
                break
            end
        end
    end
    if lowerIsBetter then result = 100 - result end
    return Clamp(result, 0, 100)
end

local function Average(parts)
    local total, weight = 0, 0
    for _, part in ipairs(parts) do
        if part[1] then total = total + part[1] * part[2]; weight = weight + part[2] end
    end
    return weight > 0 and total / weight or nil
end

local function FormatTarget(metric)
    local values = Metric(metric)
    if not values then return '—' end
    return string.format('%.1f', values[4])
end

local function SetScore(name, score)
    local label, bar = Widget(name), Widget(name .. '_bar')
    if not label or not bar then return end
    if not score then label:SetText('—'); bar:SetWidth('0%'); return end
    local rounded = math.floor(score + .5)
    label:SetText(tostring(rounded))
    bar:SetWidth(tostring(rounded) .. '%')
    local color = rounded >= 65 and '#63d99b' or (rounded >= 40 and '#f1c75b' or '#ef786f')
    label:SetColor(color); bar:SetColor(color)
end

function HoNPlusLive:Refresh()
    local heroId, roleId = ResolveHeroId(), ResolveRole()
    local csQ, n = Metric('cs')
    local levelQ = Metric('level')
    local killsQ = Metric('kills')
    local deathsQ = Metric('deaths')
    local assistsQ = Metric('assists')
    local economy = Average({{Percentile(self.stats.cs, csQ, false), .5},{Percentile(self.stats.level, levelQ, false), .5}})
    local combat = Average({{Percentile(self.stats.kills, killsQ, false), .4},{Percentile(self.stats.deaths, deathsQ, true), .3}})
    local team = Average({{Percentile(self.stats.assists, assistsQ, false), 1}})
    SetScore('economy', economy); SetScore('combat', combat); SetScore('team', team)
    SetText('role', ROLE_NAMES[roleId] or 'РОЛЬ ?')
    SetText('status', heroId and ('LIVE · n=' .. tostring(n or 0)) or 'ОЖИДАНИЕ ГЕРОЯ')
    SetText('kda_now', string.format('%d / %d / %d', self.stats.kills, self.stats.deaths, self.stats.assists))
    SetText('kda_target', FormatTarget('kills') .. ' / ' .. FormatTarget('deaths') .. ' / ' .. FormatTarget('assists'))
    SetText('cs_now', string.format('%d / %d', self.stats.cs, self.stats.denies))
    SetText('cs_target', FormatTarget('cs') .. ' / ' .. FormatTarget('creepDenies'))
    SetText('level_now', tostring(self.stats.level))
    SetText('level_target', FormatTarget('level'))
end

function HoNPlusLive:Toggle()
    self.expanded = not self.expanded
    local body, root = Widget('body'), Widget('root')
    if body then body:SetVisible(self.expanded) end
    if root then root:SetHeight(self.expanded and '11.5h' or '2.2h') end
    SetText('toggle', self.expanded and '−' or '+')
end

function HoNPlusLive:CycleRole()
    self.manualRole = ((self.manualRole or ResolveRole()) % 7) + 1
    self.role = self.manualRole
    self:Refresh()
end

function HoNPlusLive:Init()
    if self.initialized then return end
    self.initialized = true
    interface:RegisterWatch('PlayerScore', function(_, kills, deaths, assists, creepKills, neutralKills, denies)
        self.stats.kills=tonumber(kills) or 0; self.stats.deaths=tonumber(deaths) or 0; self.stats.assists=tonumber(assists) or 0
        self.stats.cs=(tonumber(creepKills) or 0)+(tonumber(neutralKills) or 0); self.stats.denies=tonumber(denies) or 0
        self:Refresh()
    end)
    interface:RegisterWatch('MatchTime', function(_, matchTime)
        self.matchTimeMs=math.max(0,tonumber(matchTime) or 0); ResolveHeroId(); self:Refresh()
    end)
    for index=0,9 do
        local slot = index
        interface:RegisterWatch('AlliesAndEnemiesPlayerInfo'..slot, function(_, _, _, playerClient)
            if tonumber(playerClient)==tonumber(GetLocalClientNumber()) then self.localSlot=slot end
        end)
        interface:RegisterWatch('AlliesAndEnemiesHeroInfo'..slot, function(_, displayName, _, level)
            if self.localSlot==slot then self.stats.level=tonumber(level) or self.stats.level; ResolveHeroId(displayName); self:Refresh() end
        end)
        interface:RegisterWatch('AlliesAndEnemiesGold'..slot, function(_, _, gpm)
            if self.localSlot==slot then self.stats.gpm=tonumber(gpm) or 0 end
        end)
    end
    self:Refresh()
end
