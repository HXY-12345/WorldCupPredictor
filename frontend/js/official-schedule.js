/* 核心功能：维护基于 FIFA 官方整理的 2026 世界杯静态赛程和球队展示元数据。 */
const TEAM_FLAGS = {
  Algeria: "🇩🇿",
  Argentina: "🇦🇷",
  Australia: "🇦🇺",
  Austria: "🇦🇹",
  Belgium: "🇧🇪",
  "Bosnia and Herzegovina": "🇧🇦",
  Brazil: "🇧🇷",
  Canada: "🇨🇦",
  "Cabo Verde": "🇨🇻",
  Colombia: "🇨🇴",
  "Congo DR": "🇨🇩",
  Croatia: "🇭🇷",
  Curaçao: "🇨🇼",
  Czechia: "🇨🇿",
  Ecuador: "🇪🇨",
  Egypt: "🇪🇬",
  England: "🏴",
  France: "🇫🇷",
  Germany: "🇩🇪",
  Ghana: "🇬🇭",
  Haiti: "🇭🇹",
  "IR Iran": "🇮🇷",
  Iraq: "🇮🇶",
  Japan: "🇯🇵",
  Jordan: "🇯🇴",
  "Korea Republic": "🇰🇷",
  Mexico: "🇲🇽",
  Morocco: "🇲🇦",
  Netherlands: "🇳🇱",
  "New Zealand": "🇳🇿",
  Norway: "🇳🇴",
  Panama: "🇵🇦",
  Paraguay: "🇵🇾",
  Portugal: "🇵🇹",
  Qatar: "🇶🇦",
  "Saudi Arabia": "🇸🇦",
  Scotland: "🏴",
  Senegal: "🇸🇳",
  "South Africa": "🇿🇦",
  Spain: "🇪🇸",
  Sweden: "🇸🇪",
  Switzerland: "🇨🇭",
  Tunisia: "🇹🇳",
  Türkiye: "🇹🇷",
  USA: "🇺🇸",
  Uruguay: "🇺🇾",
  Uzbekistan: "🇺🇿"
};

const SOURCE_REASONING =
  "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。";

const OFFICIAL_FIFA_SCHEDULE = [
  {
    date: "2026-06-11",
    fixtures: [
      { matchNo: 1, stage: "小组赛", group: "A", home: "Mexico", away: "South Africa", venue: "Mexico City Stadium" },
      { matchNo: 2, stage: "小组赛", group: "A", home: "Korea Republic", away: "Czechia", venue: "Estadio Guadalajara" }
    ]
  },
  {
    date: "2026-06-12",
    fixtures: [
      { matchNo: 3, stage: "小组赛", group: "B", home: "Canada", away: "Bosnia and Herzegovina", venue: "Toronto Stadium" },
      { matchNo: 4, stage: "小组赛", group: "D", home: "USA", away: "Paraguay", venue: "Los Angeles Stadium" }
    ]
  },
  {
    date: "2026-06-13",
    fixtures: [
      { matchNo: 5, stage: "小组赛", group: "C", home: "Haiti", away: "Scotland", venue: "Boston Stadium" },
      { matchNo: 6, stage: "小组赛", group: "D", home: "Australia", away: "Türkiye", venue: "BC Place Vancouver" },
      { matchNo: 7, stage: "小组赛", group: "C", home: "Brazil", away: "Morocco", venue: "New York New Jersey Stadium" },
      { matchNo: 8, stage: "小组赛", group: "B", home: "Qatar", away: "Switzerland", venue: "San Francisco Bay Area Stadium" }
    ]
  },
  {
    date: "2026-06-14",
    fixtures: [
      { matchNo: 9, stage: "小组赛", group: "E", home: "Côte d'Ivoire", away: "Ecuador", venue: "Philadelphia Stadium" },
      { matchNo: 10, stage: "小组赛", group: "E", home: "Germany", away: "Curaçao", venue: "Houston Stadium" },
      { matchNo: 11, stage: "小组赛", group: "F", home: "Netherlands", away: "Japan", venue: "Dallas Stadium" },
      { matchNo: 12, stage: "小组赛", group: "F", home: "Sweden", away: "Tunisia", venue: "Estadio Monterrey" }
    ]
  },
  {
    date: "2026-06-15",
    fixtures: [
      { matchNo: 13, stage: "小组赛", group: "H", home: "Saudi Arabia", away: "Uruguay", venue: "Miami Stadium" },
      { matchNo: 14, stage: "小组赛", group: "H", home: "Spain", away: "Cabo Verde", venue: "Atlanta Stadium" },
      { matchNo: 15, stage: "小组赛", group: "G", home: "IR Iran", away: "New Zealand", venue: "Los Angeles Stadium" },
      { matchNo: 16, stage: "小组赛", group: "G", home: "Belgium", away: "Egypt", venue: "Seattle Stadium" }
    ]
  },
  {
    date: "2026-06-16",
    fixtures: [
      { matchNo: 17, stage: "小组赛", group: "I", home: "France", away: "Senegal", venue: "New York New Jersey Stadium" },
      { matchNo: 18, stage: "小组赛", group: "I", home: "Iraq", away: "Norway", venue: "Boston Stadium" },
      { matchNo: 19, stage: "小组赛", group: "J", home: "Argentina", away: "Algeria", venue: "Kansas City Stadium" },
      { matchNo: 20, stage: "小组赛", group: "J", home: "Austria", away: "Jordan", venue: "San Francisco Bay Area Stadium" }
    ]
  },
  {
    date: "2026-06-17",
    fixtures: [
      { matchNo: 21, stage: "小组赛", group: "L", home: "Ghana", away: "Panama", venue: "Toronto Stadium" },
      { matchNo: 22, stage: "小组赛", group: "L", home: "England", away: "Croatia", venue: "Dallas Stadium" },
      { matchNo: 23, stage: "小组赛", group: "K", home: "Portugal", away: "Congo DR", venue: "Houston Stadium" },
      { matchNo: 24, stage: "小组赛", group: "K", home: "Uzbekistan", away: "Colombia", venue: "Mexico City Stadium" }
    ]
  },
  {
    date: "2026-06-18",
    fixtures: [
      { matchNo: 25, stage: "小组赛", group: "A", home: "Czechia", away: "South Africa", venue: "Atlanta Stadium" },
      { matchNo: 26, stage: "小组赛", group: "B", home: "Switzerland", away: "Bosnia and Herzegovina", venue: "Los Angeles Stadium" },
      { matchNo: 27, stage: "小组赛", group: "B", home: "Canada", away: "Qatar", venue: "BC Place Vancouver" },
      { matchNo: 28, stage: "小组赛", group: "A", home: "Mexico", away: "Korea Republic", venue: "Estadio Guadalajara" }
    ]
  },
  {
    date: "2026-06-19",
    fixtures: [
      { matchNo: 29, stage: "小组赛", group: "C", home: "Brazil", away: "Haiti", venue: "Philadelphia Stadium" },
      { matchNo: 30, stage: "小组赛", group: "C", home: "Scotland", away: "Morocco", venue: "Boston Stadium" },
      { matchNo: 31, stage: "小组赛", group: "D", home: "Türkiye", away: "Paraguay", venue: "San Francisco Bay Area Stadium" },
      { matchNo: 32, stage: "小组赛", group: "D", home: "USA", away: "Australia", venue: "Seattle Stadium" }
    ]
  },
  {
    date: "2026-06-20",
    fixtures: [
      { matchNo: 33, stage: "小组赛", group: "E", home: "Germany", away: "Côte d'Ivoire", venue: "Toronto Stadium" },
      { matchNo: 34, stage: "小组赛", group: "E", home: "Ecuador", away: "Curaçao", venue: "Kansas City Stadium" },
      { matchNo: 35, stage: "小组赛", group: "F", home: "Netherlands", away: "Sweden", venue: "Houston Stadium" },
      { matchNo: 36, stage: "小组赛", group: "F", home: "Tunisia", away: "Japan", venue: "Estadio Monterrey" }
    ]
  },
  {
    date: "2026-06-21",
    fixtures: [
      { matchNo: 37, stage: "小组赛", group: "H", home: "Uruguay", away: "Cabo Verde", venue: "Miami Stadium" },
      { matchNo: 38, stage: "小组赛", group: "H", home: "Spain", away: "Saudi Arabia", venue: "Atlanta Stadium" },
      { matchNo: 39, stage: "小组赛", group: "G", home: "Belgium", away: "IR Iran", venue: "Los Angeles Stadium" },
      { matchNo: 40, stage: "小组赛", group: "G", home: "New Zealand", away: "Egypt", venue: "BC Place Vancouver" }
    ]
  },
  {
    date: "2026-06-22",
    fixtures: [
      { matchNo: 41, stage: "小组赛", group: "I", home: "Norway", away: "Senegal", venue: "New York New Jersey Stadium" },
      { matchNo: 42, stage: "小组赛", group: "I", home: "France", away: "Iraq", venue: "Philadelphia Stadium" },
      { matchNo: 43, stage: "小组赛", group: "J", home: "Argentina", away: "Austria", venue: "Dallas Stadium" },
      { matchNo: 44, stage: "小组赛", group: "J", home: "Jordan", away: "Algeria", venue: "San Francisco Bay Area Stadium" }
    ]
  },
  {
    date: "2026-06-23",
    fixtures: [
      { matchNo: 45, stage: "小组赛", group: "L", home: "England", away: "Ghana", venue: "Boston Stadium" },
      { matchNo: 46, stage: "小组赛", group: "L", home: "Panama", away: "Croatia", venue: "Toronto Stadium" },
      { matchNo: 47, stage: "小组赛", group: "K", home: "Portugal", away: "Uzbekistan", venue: "Houston Stadium" },
      { matchNo: 48, stage: "小组赛", group: "K", home: "Colombia", away: "Congo DR", venue: "Estadio Guadalajara" }
    ]
  },
  {
    date: "2026-06-24",
    fixtures: [
      { matchNo: 49, stage: "小组赛", group: "C", home: "Scotland", away: "Brazil", venue: "Miami Stadium" },
      { matchNo: 50, stage: "小组赛", group: "C", home: "Morocco", away: "Haiti", venue: "Atlanta Stadium" },
      { matchNo: 51, stage: "小组赛", group: "B", home: "Switzerland", away: "Canada", venue: "BC Place Vancouver" },
      { matchNo: 52, stage: "小组赛", group: "B", home: "Bosnia and Herzegovina", away: "Qatar", venue: "Seattle Stadium" },
      { matchNo: 53, stage: "小组赛", group: "A", home: "Czechia", away: "Mexico", venue: "Mexico City Stadium" },
      { matchNo: 54, stage: "小组赛", group: "A", home: "South Africa", away: "Korea Republic", venue: "Estadio Monterrey" }
    ]
  },
  {
    date: "2026-06-25",
    fixtures: [
      { matchNo: 55, stage: "小组赛", group: "E", home: "Curaçao", away: "Côte d'Ivoire", venue: "Philadelphia Stadium" },
      { matchNo: 56, stage: "小组赛", group: "E", home: "Ecuador", away: "Germany", venue: "New York New Jersey Stadium" },
      { matchNo: 57, stage: "小组赛", group: "F", home: "Japan", away: "Sweden", venue: "Dallas Stadium" },
      { matchNo: 58, stage: "小组赛", group: "F", home: "Tunisia", away: "Netherlands", venue: "Kansas City Stadium" },
      { matchNo: 59, stage: "小组赛", group: "D", home: "Türkiye", away: "USA", venue: "Los Angeles Stadium" },
      { matchNo: 60, stage: "小组赛", group: "D", home: "Paraguay", away: "Australia", venue: "San Francisco Bay Area Stadium" }
    ]
  },
  {
    date: "2026-06-26",
    fixtures: [
      { matchNo: 61, stage: "小组赛", group: "I", home: "Norway", away: "France", venue: "Boston Stadium" },
      { matchNo: 62, stage: "小组赛", group: "I", home: "Senegal", away: "Iraq", venue: "Toronto Stadium" },
      { matchNo: 63, stage: "小组赛", group: "G", home: "Egypt", away: "IR Iran", venue: "Seattle Stadium" },
      { matchNo: 64, stage: "小组赛", group: "G", home: "New Zealand", away: "Belgium", venue: "BC Place Vancouver" },
      { matchNo: 65, stage: "小组赛", group: "H", home: "Cabo Verde", away: "Saudi Arabia", venue: "Houston Stadium" },
      { matchNo: 66, stage: "小组赛", group: "H", home: "Uruguay", away: "Spain", venue: "Estadio Guadalajara" }
    ]
  },
  {
    date: "2026-06-27",
    fixtures: [
      { matchNo: 67, stage: "小组赛", group: "L", home: "Panama", away: "England", venue: "New York New Jersey Stadium" },
      { matchNo: 68, stage: "小组赛", group: "L", home: "Croatia", away: "Ghana", venue: "Philadelphia Stadium" },
      { matchNo: 69, stage: "小组赛", group: "J", home: "Algeria", away: "Austria", venue: "Kansas City Stadium" },
      { matchNo: 70, stage: "小组赛", group: "J", home: "Jordan", away: "Argentina", venue: "Dallas Stadium" },
      { matchNo: 71, stage: "小组赛", group: "K", home: "Colombia", away: "Portugal", venue: "Miami Stadium" },
      { matchNo: 72, stage: "小组赛", group: "K", home: "Congo DR", away: "Uzbekistan", venue: "Atlanta Stadium" }
    ]
  },
  {
    date: "2026-06-28",
    fixtures: [
      { matchNo: 73, stage: "32强赛", group: null, home: "Group A runners-up", away: "Group B runners-up", venue: "Los Angeles Stadium" }
    ]
  },
  {
    date: "2026-06-29",
    fixtures: [
      { matchNo: 74, stage: "32强赛", group: null, home: "Group E winners", away: "Best third-placed team from Groups A/B/C/D/F", venue: "Boston Stadium" },
      { matchNo: 75, stage: "32强赛", group: null, home: "Group F winners", away: "Group C runners-up", venue: "Estadio Monterrey" },
      { matchNo: 76, stage: "32强赛", group: null, home: "Group C winners", away: "Group F runners-up", venue: "Houston Stadium" }
    ]
  },
  {
    date: "2026-06-30",
    fixtures: [
      { matchNo: 77, stage: "32强赛", group: null, home: "Group I winners", away: "Best third-placed team from Groups C/D/F/G/H", venue: "New York New Jersey Stadium" },
      { matchNo: 78, stage: "32强赛", group: null, home: "Group E runners-up", away: "Group I runners-up", venue: "Dallas Stadium" },
      { matchNo: 79, stage: "32强赛", group: null, home: "Group A winners", away: "Best third-placed team from Groups C/E/F/H/I", venue: "Mexico City Stadium" }
    ]
  },
  {
    date: "2026-07-01",
    fixtures: [
      { matchNo: 80, stage: "32强赛", group: null, home: "Group L winners", away: "Best third-placed team from Groups E/H/I/J/K", venue: "Atlanta Stadium" },
      { matchNo: 81, stage: "32强赛", group: null, home: "Group D winners", away: "Best third-placed team from Groups B/E/F/I/J", venue: "San Francisco Bay Area Stadium" },
      { matchNo: 82, stage: "32强赛", group: null, home: "Group G winners", away: "Best third-placed team from Groups A/E/H/I/J", venue: "Seattle Stadium" }
    ]
  },
  {
    date: "2026-07-02",
    fixtures: [
      { matchNo: 83, stage: "32强赛", group: null, home: "Group K runners-up", away: "Group L runners-up", venue: "Toronto Stadium" },
      { matchNo: 84, stage: "32强赛", group: null, home: "Group H winners", away: "Group J runners-up", venue: "Los Angeles Stadium" },
      { matchNo: 85, stage: "32强赛", group: null, home: "Group B winners", away: "Best third-placed team from Groups E/F/G/I/J", venue: "BC Place Vancouver" }
    ]
  },
  {
    date: "2026-07-03",
    fixtures: [
      { matchNo: 86, stage: "32强赛", group: null, home: "Group J winners", away: "Group H runners-up", venue: "Miami Stadium" },
      { matchNo: 87, stage: "32强赛", group: null, home: "Group K winners", away: "Best third-placed team from Groups D/E/I/J/L", venue: "Kansas City Stadium" },
      { matchNo: 88, stage: "32强赛", group: null, home: "Group D runners-up", away: "Group G runners-up", venue: "Dallas Stadium" }
    ]
  },
  {
    date: "2026-07-04",
    fixtures: [
      { matchNo: 89, stage: "16强赛", group: null, home: "Winner Match 74", away: "Winner Match 77", venue: "Philadelphia Stadium" },
      { matchNo: 90, stage: "16强赛", group: null, home: "Winner Match 73", away: "Winner Match 75", venue: "Houston Stadium" }
    ]
  },
  {
    date: "2026-07-05",
    fixtures: [
      { matchNo: 91, stage: "16强赛", group: null, home: "Winner Match 76", away: "Winner Match 78", venue: "New York New Jersey Stadium" },
      { matchNo: 92, stage: "16强赛", group: null, home: "Winner Match 79", away: "Winner Match 80", venue: "Mexico City Stadium" }
    ]
  },
  {
    date: "2026-07-06",
    fixtures: [
      { matchNo: 93, stage: "16强赛", group: null, home: "Winner Match 83", away: "Winner Match 84", venue: "Dallas Stadium" },
      { matchNo: 94, stage: "16强赛", group: null, home: "Winner Match 81", away: "Winner Match 82", venue: "Seattle Stadium" }
    ]
  },
  {
    date: "2026-07-07",
    fixtures: [
      { matchNo: 95, stage: "16强赛", group: null, home: "Winner Match 86", away: "Winner Match 88", venue: "Atlanta Stadium" },
      { matchNo: 96, stage: "16强赛", group: null, home: "Winner Match 85", away: "Winner Match 87", venue: "BC Place Vancouver" }
    ]
  },
  {
    date: "2026-07-09",
    fixtures: [
      { matchNo: 97, stage: "1/4 决赛", group: null, home: "Winner Match 89", away: "Winner Match 90", venue: "Boston Stadium" }
    ]
  },
  {
    date: "2026-07-10",
    fixtures: [
      { matchNo: 98, stage: "1/4 决赛", group: null, home: "Winner Match 93", away: "Winner Match 94", venue: "Los Angeles Stadium" }
    ]
  },
  {
    date: "2026-07-11",
    fixtures: [
      { matchNo: 99, stage: "1/4 决赛", group: null, home: "Winner Match 91", away: "Winner Match 92", venue: "Miami Stadium" },
      { matchNo: 100, stage: "1/4 决赛", group: null, home: "Winner Match 95", away: "Winner Match 96", venue: "Kansas City Stadium" }
    ]
  },
  {
    date: "2026-07-14",
    fixtures: [
      { matchNo: 101, stage: "半决赛", group: null, home: "Winner Match 97", away: "Winner Match 98", venue: "Dallas Stadium" }
    ]
  },
  {
    date: "2026-07-15",
    fixtures: [
      { matchNo: 102, stage: "半决赛", group: null, home: "Winner Match 99", away: "Winner Match 100", venue: "Atlanta Stadium" }
    ]
  },
  {
    date: "2026-07-18",
    fixtures: [
      { matchNo: 103, stage: "季军赛", group: null, home: "Loser Match 101", away: "Loser Match 102", venue: "Miami Stadium" }
    ]
  },
  {
    date: "2026-07-19",
    fixtures: [
      { matchNo: 104, stage: "决赛", group: null, home: "Winner Match 101", away: "Winner Match 102", venue: "New York New Jersey Stadium" }
    ]
  }
];

function isSlotTeam(name) {
  return /Group|Winner|Loser|third-placed/i.test(name);
}

function formatMatchLabel(matchNo) {
  return `M${String(matchNo).padStart(3, "0")}`;
}

function createTeam(name) {
  return {
    name,
    flag: TEAM_FLAGS[name] ?? (isSlotTeam(name) ? "🏁" : "🏟️"),
    fifa_rank: null,
    form: []
  };
}

function createPrediction(matchNo, home, away) {
  const slotMatch = isSlotTeam(home) || isSlotTeam(away);
  const homeScore = slotMatch ? matchNo % 2 : matchNo % 3;
  const awayScore = slotMatch ? 1 : (matchNo + 1) % 3;
  const homeWin = 34 + (matchNo % 24);
  const draw = 20 + (matchNo % 10);
  const awayWin = Math.max(100 - homeWin - draw, 12);

  return {
    home_score: homeScore,
    away_score: awayScore,
    confidence: slotMatch ? 52 : 60 + (matchNo % 21),
    probabilities: {
      home_win: homeWin,
      draw,
      away_win: awayWin
    },
    reasoning: SOURCE_REASONING,
    predicted_at: "2026-04-18T00:00:00Z"
  };
}

function buildMatch(date, fixture, indexInDay) {
  return {
    id: `fwc2026-m${String(fixture.matchNo).padStart(3, "0")}`,
    official_match_number: fixture.matchNo,
    kickoff_label: formatMatchLabel(fixture.matchNo),
    sort_order: indexInDay + 1,
    date,
    time: "待定",
    stage: fixture.stage,
    group: fixture.group,
    venue: fixture.venue,
    home_team: createTeam(fixture.home),
    away_team: createTeam(fixture.away),
    status: "not_started",
    score: null,
    prediction: createPrediction(fixture.matchNo, fixture.home, fixture.away),
    head_to_head: null,
    key_players: {
      home_injured: [],
      away_suspended: []
    }
  };
}

const matches = OFFICIAL_FIFA_SCHEDULE.flatMap((day) =>
  day.fixtures.map((fixture, indexInDay) => buildMatch(day.date, fixture, indexInDay))
);

export const officialScheduleMetadata = {
  articleUrl:
    "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums",
  pdfUrl:
    "https://fwc26teambasecamps.fifa.com/ReactApps/TBC/dist/static/media/match-schedule-english.071cf28145379e10f0cf.pdf",
  publishedAt: "2026-03-31T00:00:00Z"
};

export const officialSchedulePayload = {
  matches,
  last_updated: officialScheduleMetadata.publishedAt,
  total: matches.length
};
