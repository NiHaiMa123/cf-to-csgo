# 🍑 T 阵营语音台本 · 桃桃（活泼少女·融合版）

> **角色卡**
> - 名字：**桃桃**，古灵精怪的元气少女——甜萌外表 + 傲娇内核 + 一颗中二魂。
> - 自称：桃桃（名字自称，三句不离本名，像晴雅那样）；偶尔傲娇撂"本小姐"。
> - 招牌：拟声词（`biubiubiu` / `砰` / `Biang` / `轰隆隆` / `咻`）、中二招式名（桃桃飞雷/桃桃甜烟/桃桃爆闪）、口头禅（啦/咯/嘛/呀/耶/嗷/哒/喽）。
>
> **用途**：用 TTS 制作「桃桃」声线，替换 CS:GO 全部基础 T 阵营（anarchist / balkan / leet / phoenix / pirate / professional / separatist）的角色语音。
>
> **怎么用**：按台本，**每个语义生成一句**（不需要为每个阵营、每个文件名重复生成）。生成后把音频命名为 `编号_语义.wav`（如 `001_t_smoke.wav`）放一个文件夹发我，我负责分发到 7 个阵营的对应文件名并部署到 MIGI。
>
> **格式硬性要求**（README）：`.wav` / **16-bit PCM** / **单声道** / **44.1kHz**；响度 **`-9~-11 LUFS`**（比常规高 5dB，补偿游戏语音混音衰减，实测合适），峰值 **`≤-0.5dBTP`**，句尾留 200~450ms 静音。
>
> **范围**：`tmap_*`（地图报点 128+ 变体）不在台本内；`radiobot*` 是 BOT 语音，professional 专属，已单列（可选）。

---

## 一、投掷物 🧨

| # | 语义 | 含义 | 桃桃的台词 | 阵营 | 变体 |
|---|------|------|-----------|------|------|
| 001 | `t_smoke` | 丢烟雾弹 | 「桃桃甜心烟雾～咻！」 | 7/7 | 5 |
| 002 | `t_flashbang` | 丢闪光弹 | 「桃桃爆闪！Biang～闪瞎你们！」 | 7/7 | 4 |
| 003 | `t_grenade` | 丢手雷 | 「桃桃飞雷，走你！」 | 7/7 | 6 |
| 004 | `t_molotov` | 丢燃烧瓶 | 「桃桃火球，轰隆隆～烧起来！」 | 7/7 | 9 |
| 005 | `t_decoy` | 丢诱饵弹 | 「小玩具上！迷惑他们去，嘿嘿～」 | 7/7 | 4 |

## 二、炸弹 💣

| # | 语义 | 含义 | 桃桃的台词 | 阵营 | 变体 |
|---|------|------|-----------|------|------|
| 006 | `plantingbomb` | 正在安包 | 「桃桃在放包啦，守好我哦！」 | 5/7 | 5 |
| 007 | `goingtoplantbomb` | 去安包 | 「桃桃去放包咯！」 | 5/7 | 3 |
| 008 | `goingtoplantbomba` | 去 A 安包 | 「A 点！桃桃带你们去放包！」 | 5/7 | 3 |
| 009 | `goingtoplantbombb` | 去 B 安包 | 「B 点走起，桃桃放包去！」 | 4/7 | 2 |
| 010 | `goingtoplantbombc` | 去 C 安包 | 「C 点！桃桃冲啦！」 | 1/7 | 3 |
| 011 | `bombtickingdown` | 包在倒计时 | 「包在倒数啦！桃桃好紧张！」 | 5/7 | 6 |
| 012 | `defendingbombsitea` | 防守 A 点 | 「A 点桃桃守着，谁也别想过来！」 | 5/7 | 5 |
| 013 | `defendingbombsiteb` | 防守 B 点 | 「B 点交给桃桃啦！」 | 4/7 | 5 |
| 014 | `goingtodefendbombsite` | 去守包点 | 「桃桃去守包点咯！」 | 5/7 | 5 |
| 015 | `spottedloosebomb` | 发现掉包 | 「发现掉包的啦！桃桃看到咯！」 | 5/7 | 8 |

## 三、人质 🧸

| # | 语义 | 含义 | 桃桃的台词 | 阵营 | 变体 |
|---|------|------|-----------|------|------|
| 016 | `goingtoguardhostages` | 去守人质 | 「桃桃去看住人质！」 | 4/7 | 6 |
| 017 | `goingtoguardhostageescapezone` | 去守出口 | 「桃桃守住人质出口！」 | 5/7 | 3 |
| 018 | `guardinghostages` | 看守人质中 | 「人质在桃桃这，放一百个心！」 | 4/7 | 5 |
| 019 | `guardinghostageescapezone` | 守出口中 | 「出口桃桃盯着呢！」 | 4/7 | 5 |
| 020 | `hostagedown` | 人质倒地 | 「人质倒地啦！桃桃好慌！」 | 3/7 | 5 |
| 021 | `hostagesbeingtaken` | 人质被带走 | 「人质被带走啦！快追！」 | 3/7 | 4 |
| 022 | `hostagestaken` | 人质被抓 | 「人质被抓走啦！桃桃气死了！」 | 3/7 | 4 |

## 四、战术指令 📡

| # | 语义 | 含义 | 桃桃的台词 | 阵营 | 变体 |
|---|------|------|-----------|------|------|
| 023 | `affirmative` | 收到 | 「收到！桃桃明白啦！」 | 6/7 | 3 |
| 024 | `agree` | 赞成 | 「好呀好呀！桃桃同意！」 | 6/7 | 8 |
| 025 | `negative` | 否定 | 「不行不行，桃桃说不！」 | 6/7 | 4 |
| 026 | `disagree` | 反对 | 「才不要呢！桃桃反对！」 | 6/7 | 6 |
| 027 | `negativeno` | 坚决否定 | 「不行就是不行啦！桃桃说的！」 | 4/7 | 3 |
| 028 | `coverme` | 掩护我 | 「掩护桃桃一下下嘛！」 | 7/7 | 3 |
| 029 | `coveringfriend` | 掩护队友 | 「桃桃掩护你，上吧！」 | 6/7 | 4 |
| 030 | `followingfriend` | 跟随队友 | 「桃桃跟你走！」 | 6/7 | 7 |
| 031 | `help` | 求救 | 「救命呀！桃桃需要帮助！」 | 6/7 | 6 |
| 032 | `onmyway` | 在路上 | 「桃桃来啦桃桃来啦！」 | 6/7 | 4 |
| 033 | `inposition` | 就位 | 「桃桃到位咯！」 | 7/7 | 3 |
| 034 | `waitinghere` | 等待 | 「桃桃在这等着呢！」 | 7/7 | 5 |
| 035 | `reportingin` | 报到 | 「桃桃报到！我在这！」 | 7/7 | 4 |
| 036 | `requestreport` | 请报告 | 「报下情况嘛，桃桃想知道！」 | 6/7 | 4 |
| 037 | `clear` | 已清空 | 「这边干净啦，桃桃检查过！」 | 6/7 | 3 |
| 038 | `clearedarea` | 区域已清 | 「桃桃这边清理干净咯！」 | 6/7 | 5 |
| 039 | `lastmanstanding` | 最后一人 | 「只剩桃桃一个了…但我会赢的！」 | 6/7 | 8 |
| 040 | `thanks` | 感谢 | 「谢谢你啦！桃桃记住咯！」 | 6/7 | 5 |
| 041 | `lostenemy` | 跟丢敌人 | 「跟丢啦…他跑哪去了？」 | 6/7 | 4 |
| 042 | `enemydown` | 击倒敌人 | 「搞定！桃桃厉害吧！」 | 6/7 | 12 |
| 043 | `killedfriend` | 误杀队友 | 「啊对不起！桃桃不是故意的！」 | 6/7 | 6 |
| 044 | `friendlyfire` | 友军火力 | 「别打桃桃啦！自己人！」 | 6/7 | 17 |
| 045 | `niceshot` | 好枪法 | 「好枪法！桃桃给你鼓掌！」 | 6/7 | 14 |
| 046 | `peptalk` | 打气 | 「加油鸭！桃桃和你们一起赢！」 | 6/7 | 9 |
| 047 | `onarollbrag` | 连杀吹牛 | 「看桃桃的连杀！就问帅不帅！」 | 6/7 | 15 |
| 048 | `preventescapebrag` | 阻止逃跑炫耀 | 「想跑？桃桃可不答应！」 | 3/7 | 5 |
| 049 | `sniperkilled` | 干掉狙击手 | 「狙击手被桃桃干掉啦！」 | 6/7 | 4 |
| 050 | `sniperwarning` | 警告有狙击 | 「小心！有狙击手盯着呢！」 | 6/7 | 5 |
| 051 | `oneenemyleft` | 剩一敌 | 「就剩一个啦，桃桃加油！」 | 6/7 | 12 |
| 052 | `twoenemiesleft` | 剩二敌 | 「还剩两个哦！」 | 6/7 | 6 |
| 053 | `threeenemiesleft` | 剩三敌 | 「还有三个敌人呢！」 | 6/7 | 6 |

## 五、状态反应 🩹

| # | 语义 | 含义 | 桃桃的台词 | 阵营 | 变体 |
|---|------|------|-----------|------|------|
| 054 | `t_death` | 死亡 | 「啊…桃桃…居然…呜…」 | 7/7 | 7 |
| 055 | `blinded` | 被闪白 | 「好闪！桃桃眼睛都睁不开啦！」 | 6/7 | 7 |
| 056 | `heardnoise` | 听到动静 | 「有动静！桃桃听到啦！」 | 6/7 | 5 |
| 057 | `scaredemote` | 被吓到 | 「哇啊！吓死桃桃了！」 | 6/7 | 10 |
| 058 | `pinneddown` | 被压制 | 「桃桃被压住啦！快来帮忙！」 | 6/7 | 4 |
| 059 | `incombat` | 交火中 | 「桃桃这边打起来啦！」 | 6/7 | 10 |

## 六、无线电指令 📻

| # | 语义 | 含义 | 桃桃的台词 | 阵营 | 变体 |
|---|------|------|-----------|------|------|
| 060 | `radio_enemyspotted` | 发现敌人 | 「发现敌人！就在那边！」 | 5/7 | 7 |
| 061 | `radio_followme` | 跟我来 | 「跟桃桃来这边！」 | 5/7 | 6 |
| 062 | `radio_letsgo` | 出发 | 「走啦走啦！桃桃出发！」 | 5/7 | 13 |
| 063 | `radio_locknload` | 上膛 | 「上膛！桃桃要大显身手啦！」 | 5/7 | 14 |
| 064 | `radio_needbackup` | 需要支援 | 「桃桃需要支援！快来快来！」 | 5/7 | 6 |
| 065 | `radio_takingfire` | 挨打 | 「桃桃在挨打！救命呀！」 | 5/7 | 9 |

> 注：`separatist` 阵营用点分前缀版（`radio.enemyspotted` 等），语义同上，部署自动对应。

## 七、BOT 队友语音（professional 专属，可选）🤖

| # | 语义 | 含义 | 桃桃的台词 | 阵营 | 变体 |
|---|------|------|-----------|------|------|
| 066 | `radiobotendclean` | BOT：清场 | 「桃桃把他们都搞定啦！」 | 7/7 | 11 |
| 067 | `radiobotendsolid` | BOT：稳固 | 「桃桃稳住了！」 | 7/7 | 8 |
| 068 | `radiobotfallback` | BOT：撤退 | 「桃桃先撤！快跟上！」 | 7/7 | 5 |
| 069 | `radiobothold` | BOT：守住 | 「都给桃桃守住！」 | 7/7 | 4 |
| 070 | `radiobotregroup` | BOT：集结 | 「都来桃桃这集合！」 | 7/7 | 4 |
| 071 | `radiobotgo` | BOT：走 | 「走！桃桃开路！」 | 1/7 | 9 |
| 072 | `radiobotfollowme` | BOT：跟我 | 「跟着桃桃！」 | 1/7 | 5 |
| 073 | `radiobotfollowyou` | BOT：跟你 | 「桃桃跟你走！」 | 1/7 | 5 |
| 074 | `radiobotguarding` | BOT：看守 | 「桃桃看着呢！」 | 1/7 | 7 |
| 075 | `radiobotguardinga` | BOT：守 A | 「桃桃守着 A 点！」 | 1/7 | 3 |
| 076 | `radiobotguardingb` | BOT：守 B | 「桃桃守着 B 点！」 | 1/7 | 3 |
| 077 | `radiobotguardingc` | BOT：守 C | 「桃桃守着 C 点！」 | 1/7 | 3 |
| 078 | `radiobotkill` | BOT：击杀 | 「桃桃干掉一个！」 | 1/7 | 8 |
| 079 | `radiobotkillcount` | BOT：击杀数 | 「桃桃都杀了几个啦！」 | 1/7 | 18 |
| 080 | `radiobotkillsniper` | BOT：狙倒 | 「狙击手被桃桃解决啦！」 | 1/7 | 6 |
| 081 | `radiobotniceshot` | BOT：好枪 | 「漂亮！桃桃给你点赞！」 | 1/7 | 13 |
| 082 | `radiobotplanting` | BOT：安包中 | 「桃桃在放包！」 | 1/7 | 7 |
| 083 | `radiobotplantinggo` | BOT：去安包 | 「桃桃去放包！」 | 1/7 | 3 |
| 084 | `radiobotplantinggoa` | BOT：去 A 安 | 「桃桃去 A 点放包！」 | 1/7 | 2 |
| 085 | `radiobotplantinggob` | BOT：去 B 安 | 「桃桃去 B 点放包！」 | 1/7 | 2 |
| 086 | `radiobotplantinggoc` | BOT：去 C 安 | 「桃桃去 C 点放包！」 | 1/7 | 3 |
| 087 | `radiobotplantinggosafe` | BOT：安全安包 | 「安全啦！快放包！」 | 1/7 | 3 |
| 088 | `radiobotpostflash` | BOT：被闪后 | 「桃桃中闪了！看不清啦！」 | 1/7 | 4 |
| 089 | `radiobothear` | BOT：听到动静 | 「桃桃听到动静啦！」 | 1/7 | 6 |
| 090 | `radiobotquery` | BOT：询问 | 「情况怎么样呀？桃桃问问！」 | 2/7 | 5 |
| 091 | `radiobotreport` | BOT：报告 | 「桃桃报告完毕！」 | 1/7 | 8 |
| 092 | `radiobotstart` | BOT：开局 | 「开始行动！桃桃来啦！」 | 1/7 | 10 |
| 093 | `radiobottarget` | BOT：目标 | 「目标确认！桃桃锁定！」 | 1/7 | 4 |
| 094 | `radiobotunderfire` | BOT：被火 | 「桃桃被打了！」 | 1/7 | 11 |
| 095 | `radiobotunderfirefriendly` | BOT：被友军火 | 「自己人！别打桃桃！」 | 1/7 | 7 |
| 096 | `radiobotunderfiresniper` | BOT：被狙 | 「有狙击手盯上桃桃啦！」 | 1/7 | 3 |
| 097 | `radiobotcheer` | BOT：欢呼 | 「耶～桃桃赢啦！」 | 1/7 | 10 |
| 098 | `radiobotclear` | BOT：清空 | 「桃桃清理干净啦！」 | 1/7 | 7 |
| 099 | `radiobombsite` | BOT：包点 | 「包点在这！桃桃找到啦！」 | 1/7 | 3 |
| 100 | `radiobotbombatsafe` | BOT：包安全 | 「包安全着呢！桃桃放心啦！」 | 1/7 | 3 |
| 101 | `radiobotbombdefusing` | BOT：拆包 | 「桃桃在拆包！」 | 1/7 | 3 |
| 102 | `radiobotwait` | BOT：等待 | 「等一下哦！桃桃马上好！」 | 1/7 | 1 |
| 103 | `radiobotreponseattacking` | BOT：回应进攻 | 「桃桃在进攻！」 | 1/7 | 9 |
| 104 | `radiobotreponsecoverrequest` | BOT：回应掩护 | 「收到！桃桃掩护你！」 | 1/7 | 6 |
| 105 | `radiobotreponsenegative` | BOT：回应否定 | 「不行！桃桃说不！」 | 1/7 | 13 |
| 106 | `radiobotreponseomw` | BOT：回应在路上 | 「桃桃在路上！」 | 1/7 | 5 |
| 107 | `radiobotreponsepositive` | BOT：回应肯定 | 「好呀！桃桃来啦！」 | 1/7 | 10 |
| 108 | `radiobotcompliment` | BOT：夸奖 | 「你超棒的！桃桃很满意！」 | 1/7 | 1 |

## 八、其他 🐔

| # | 语义 | 含义 | 桃桃的台词 | 阵营 | 变体 |
|---|------|------|-----------|------|------|
| 109 | `chickenhate` | 讨厌鸡 | 「又是这只鸡！桃桃讨厌它！」 | 1/7 | 4 |

---

## 📌 汇总说明

- **7 阵营完全共有（15 个）**：投掷物 5 + `t_death` + `coverme` + `inposition` + `waitinghere` + `reportingin` + `radiobotendclean/endsolid/fallback/hold/regroup`。做这 15 个即可覆盖全部 7 阵营。
- **`professional` 最特殊**：普通战术语音基本没有，独占整套 `radiobot*` BOT 语音。
- **`separatist` 命名不一致**：无线电用点分 `radio.enemyspotted`；独有 `chickenhate`、`goingtoplantbombc`。
- **序号变体差异**：同语义各阵营文件名序号不同，部署时我按各阵营实际文件名逐个填满——**你每语义只需生成 1 句**。

> 建议至少完成 **#001~065**（投掷物/炸弹/人质/战术/状态/无线电）。`radiobot*`（#066~108）按需选做。
