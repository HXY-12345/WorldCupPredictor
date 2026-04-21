/* 核心功能：导出基于 FIFA 官方赛程整理并统一转换为北京时间的 2026 世界杯静态兜底赛程。 */
export const officialScheduleMetadata = {
  "articleUrl": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/updated-fifa-world-cup-2026-match-schedule-now-available",
  "pdfUrl": "https://digitalhub.fifa.com/asset/4b5d4417-3343-4732-9cdf-14b6662af407/FWC26-Match-Schedule_English.pdf",
  "publishedAt": "2026-04-20T00:00:00Z",
  "displayTimezone": "Asia/Shanghai"
};

export const officialSchedulePayload = {
  "matches": [
    {
      "id": "fwc2026-m001",
      "official_match_number": 1,
      "kickoff_label": "M001",
      "sort_order": 1,
      "date": "2026-06-12",
      "time": "03:00",
      "stage": "小组赛",
      "group": "A",
      "venue": "Mexico City Stadium",
      "home_team": {
        "name": "Mexico",
        "flag": "🇲🇽",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "South Africa",
        "flag": "🇿🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 61,
        "probabilities": {
          "home_win": 35,
          "draw": 21,
          "away_win": 44
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m002",
      "official_match_number": 2,
      "kickoff_label": "M002",
      "sort_order": 2,
      "date": "2026-06-12",
      "time": "10:00",
      "stage": "小组赛",
      "group": "A",
      "venue": "Estadio Guadalajara",
      "home_team": {
        "name": "Korea Republic",
        "flag": "🇰🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Czechia",
        "flag": "🇨🇿",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 62,
        "probabilities": {
          "home_win": 36,
          "draw": 22,
          "away_win": 42
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m003",
      "official_match_number": 3,
      "kickoff_label": "M003",
      "sort_order": 3,
      "date": "2026-06-13",
      "time": "03:00",
      "stage": "小组赛",
      "group": "B",
      "venue": "Toronto Stadium",
      "home_team": {
        "name": "Canada",
        "flag": "🇨🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Bosnia and Herzegovina",
        "flag": "🇧🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 63,
        "probabilities": {
          "home_win": 37,
          "draw": 23,
          "away_win": 40
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m004",
      "official_match_number": 4,
      "kickoff_label": "M004",
      "sort_order": 4,
      "date": "2026-06-13",
      "time": "09:00",
      "stage": "小组赛",
      "group": "D",
      "venue": "Los Angeles Stadium",
      "home_team": {
        "name": "USA",
        "flag": "🇺🇸",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Paraguay",
        "flag": "🇵🇾",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 64,
        "probabilities": {
          "home_win": 38,
          "draw": 24,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m006",
      "official_match_number": 6,
      "kickoff_label": "M006",
      "sort_order": 6,
      "date": "2026-06-13",
      "time": "12:00",
      "stage": "小组赛",
      "group": "D",
      "venue": "BC Place Vancouver",
      "home_team": {
        "name": "Australia",
        "flag": "🇦🇺",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Türkiye",
        "flag": "🇹🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 66,
        "probabilities": {
          "home_win": 40,
          "draw": 26,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m008",
      "official_match_number": 8,
      "kickoff_label": "M008",
      "sort_order": 8,
      "date": "2026-06-14",
      "time": "03:00",
      "stage": "小组赛",
      "group": "B",
      "venue": "San Francisco Bay Area Stadium",
      "home_team": {
        "name": "Qatar",
        "flag": "🇶🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Switzerland",
        "flag": "🇨🇭",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 68,
        "probabilities": {
          "home_win": 42,
          "draw": 28,
          "away_win": 30
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m007",
      "official_match_number": 7,
      "kickoff_label": "M007",
      "sort_order": 7,
      "date": "2026-06-14",
      "time": "06:00",
      "stage": "小组赛",
      "group": "C",
      "venue": "New York New Jersey Stadium",
      "home_team": {
        "name": "Brazil",
        "flag": "🇧🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Morocco",
        "flag": "🇲🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 67,
        "probabilities": {
          "home_win": 41,
          "draw": 27,
          "away_win": 32
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m005",
      "official_match_number": 5,
      "kickoff_label": "M005",
      "sort_order": 5,
      "date": "2026-06-14",
      "time": "09:00",
      "stage": "小组赛",
      "group": "C",
      "venue": "Boston Stadium",
      "home_team": {
        "name": "Haiti",
        "flag": "🇭🇹",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Scotland",
        "flag": "🏴",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 65,
        "probabilities": {
          "home_win": 39,
          "draw": 25,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m010",
      "official_match_number": 10,
      "kickoff_label": "M010",
      "sort_order": 10,
      "date": "2026-06-15",
      "time": "01:00",
      "stage": "小组赛",
      "group": "E",
      "venue": "Houston Stadium",
      "home_team": {
        "name": "Germany",
        "flag": "🇩🇪",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Curaçao",
        "flag": "🇨🇼",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 70,
        "probabilities": {
          "home_win": 44,
          "draw": 20,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m011",
      "official_match_number": 11,
      "kickoff_label": "M011",
      "sort_order": 11,
      "date": "2026-06-15",
      "time": "04:00",
      "stage": "小组赛",
      "group": "F",
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "Netherlands",
        "flag": "🇳🇱",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Japan",
        "flag": "🇯🇵",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 71,
        "probabilities": {
          "home_win": 45,
          "draw": 21,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m009",
      "official_match_number": 9,
      "kickoff_label": "M009",
      "sort_order": 9,
      "date": "2026-06-15",
      "time": "07:00",
      "stage": "小组赛",
      "group": "E",
      "venue": "Philadelphia Stadium",
      "home_team": {
        "name": "Côte d'Ivoire",
        "flag": "🏟️",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Ecuador",
        "flag": "🇪🇨",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 69,
        "probabilities": {
          "home_win": 43,
          "draw": 29,
          "away_win": 28
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m012",
      "official_match_number": 12,
      "kickoff_label": "M012",
      "sort_order": 12,
      "date": "2026-06-15",
      "time": "10:00",
      "stage": "小组赛",
      "group": "F",
      "venue": "Estadio Monterrey",
      "home_team": {
        "name": "Sweden",
        "flag": "🇸🇪",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Tunisia",
        "flag": "🇹🇳",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 72,
        "probabilities": {
          "home_win": 46,
          "draw": 22,
          "away_win": 32
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m014",
      "official_match_number": 14,
      "kickoff_label": "M014",
      "sort_order": 14,
      "date": "2026-06-16",
      "time": "00:00",
      "stage": "小组赛",
      "group": "H",
      "venue": "Atlanta Stadium",
      "home_team": {
        "name": "Spain",
        "flag": "🇪🇸",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Cabo Verde",
        "flag": "🇨🇻",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 74,
        "probabilities": {
          "home_win": 48,
          "draw": 24,
          "away_win": 28
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m016",
      "official_match_number": 16,
      "kickoff_label": "M016",
      "sort_order": 16,
      "date": "2026-06-16",
      "time": "03:00",
      "stage": "小组赛",
      "group": "G",
      "venue": "Seattle Stadium",
      "home_team": {
        "name": "Belgium",
        "flag": "🇧🇪",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Egypt",
        "flag": "🇪🇬",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 76,
        "probabilities": {
          "home_win": 50,
          "draw": 26,
          "away_win": 24
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m013",
      "official_match_number": 13,
      "kickoff_label": "M013",
      "sort_order": 13,
      "date": "2026-06-16",
      "time": "06:00",
      "stage": "小组赛",
      "group": "H",
      "venue": "Miami Stadium",
      "home_team": {
        "name": "Saudi Arabia",
        "flag": "🇸🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Uruguay",
        "flag": "🇺🇾",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 73,
        "probabilities": {
          "home_win": 47,
          "draw": 23,
          "away_win": 30
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m015",
      "official_match_number": 15,
      "kickoff_label": "M015",
      "sort_order": 15,
      "date": "2026-06-16",
      "time": "09:00",
      "stage": "小组赛",
      "group": "G",
      "venue": "Los Angeles Stadium",
      "home_team": {
        "name": "IR Iran",
        "flag": "🇮🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "New Zealand",
        "flag": "🇳🇿",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 75,
        "probabilities": {
          "home_win": 49,
          "draw": 25,
          "away_win": 26
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m020",
      "official_match_number": 20,
      "kickoff_label": "M020",
      "sort_order": 20,
      "date": "2026-06-16",
      "time": "12:00",
      "stage": "小组赛",
      "group": "J",
      "venue": "San Francisco Bay Area Stadium",
      "home_team": {
        "name": "Austria",
        "flag": "🇦🇹",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Jordan",
        "flag": "🇯🇴",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 80,
        "probabilities": {
          "home_win": 54,
          "draw": 20,
          "away_win": 26
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m017",
      "official_match_number": 17,
      "kickoff_label": "M017",
      "sort_order": 17,
      "date": "2026-06-17",
      "time": "03:00",
      "stage": "小组赛",
      "group": "I",
      "venue": "New York New Jersey Stadium",
      "home_team": {
        "name": "France",
        "flag": "🇫🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Senegal",
        "flag": "🇸🇳",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 77,
        "probabilities": {
          "home_win": 51,
          "draw": 27,
          "away_win": 22
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m018",
      "official_match_number": 18,
      "kickoff_label": "M018",
      "sort_order": 18,
      "date": "2026-06-17",
      "time": "06:00",
      "stage": "小组赛",
      "group": "I",
      "venue": "Boston Stadium",
      "home_team": {
        "name": "Iraq",
        "flag": "🇮🇶",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Norway",
        "flag": "🇳🇴",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 78,
        "probabilities": {
          "home_win": 52,
          "draw": 28,
          "away_win": 20
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m019",
      "official_match_number": 19,
      "kickoff_label": "M019",
      "sort_order": 19,
      "date": "2026-06-17",
      "time": "09:00",
      "stage": "小组赛",
      "group": "J",
      "venue": "Kansas City Stadium",
      "home_team": {
        "name": "Argentina",
        "flag": "🇦🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Algeria",
        "flag": "🇩🇿",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 79,
        "probabilities": {
          "home_win": 53,
          "draw": 29,
          "away_win": 18
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m023",
      "official_match_number": 23,
      "kickoff_label": "M023",
      "sort_order": 23,
      "date": "2026-06-18",
      "time": "01:00",
      "stage": "小组赛",
      "group": "K",
      "venue": "Houston Stadium",
      "home_team": {
        "name": "Portugal",
        "flag": "🇵🇹",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Congo DR",
        "flag": "🇨🇩",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 62,
        "probabilities": {
          "home_win": 57,
          "draw": 23,
          "away_win": 20
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m022",
      "official_match_number": 22,
      "kickoff_label": "M022",
      "sort_order": 22,
      "date": "2026-06-18",
      "time": "04:00",
      "stage": "小组赛",
      "group": "L",
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "England",
        "flag": "🏴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Croatia",
        "flag": "🇭🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 61,
        "probabilities": {
          "home_win": 56,
          "draw": 22,
          "away_win": 22
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m021",
      "official_match_number": 21,
      "kickoff_label": "M021",
      "sort_order": 21,
      "date": "2026-06-18",
      "time": "07:00",
      "stage": "小组赛",
      "group": "L",
      "venue": "Toronto Stadium",
      "home_team": {
        "name": "Ghana",
        "flag": "🇬🇭",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Panama",
        "flag": "🇵🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 60,
        "probabilities": {
          "home_win": 55,
          "draw": 21,
          "away_win": 24
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m024",
      "official_match_number": 24,
      "kickoff_label": "M024",
      "sort_order": 24,
      "date": "2026-06-18",
      "time": "10:00",
      "stage": "小组赛",
      "group": "K",
      "venue": "Mexico City Stadium",
      "home_team": {
        "name": "Uzbekistan",
        "flag": "🇺🇿",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Colombia",
        "flag": "🇨🇴",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 63,
        "probabilities": {
          "home_win": 34,
          "draw": 24,
          "away_win": 42
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m025",
      "official_match_number": 25,
      "kickoff_label": "M025",
      "sort_order": 25,
      "date": "2026-06-19",
      "time": "00:00",
      "stage": "小组赛",
      "group": "A",
      "venue": "Atlanta Stadium",
      "home_team": {
        "name": "Czechia",
        "flag": "🇨🇿",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "South Africa",
        "flag": "🇿🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 64,
        "probabilities": {
          "home_win": 35,
          "draw": 25,
          "away_win": 40
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m026",
      "official_match_number": 26,
      "kickoff_label": "M026",
      "sort_order": 26,
      "date": "2026-06-19",
      "time": "03:00",
      "stage": "小组赛",
      "group": "B",
      "venue": "Los Angeles Stadium",
      "home_team": {
        "name": "Switzerland",
        "flag": "🇨🇭",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Bosnia and Herzegovina",
        "flag": "🇧🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 65,
        "probabilities": {
          "home_win": 36,
          "draw": 26,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m027",
      "official_match_number": 27,
      "kickoff_label": "M027",
      "sort_order": 27,
      "date": "2026-06-19",
      "time": "06:00",
      "stage": "小组赛",
      "group": "B",
      "venue": "BC Place Vancouver",
      "home_team": {
        "name": "Canada",
        "flag": "🇨🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Qatar",
        "flag": "🇶🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 66,
        "probabilities": {
          "home_win": 37,
          "draw": 27,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m028",
      "official_match_number": 28,
      "kickoff_label": "M028",
      "sort_order": 28,
      "date": "2026-06-19",
      "time": "09:00",
      "stage": "小组赛",
      "group": "A",
      "venue": "Estadio Guadalajara",
      "home_team": {
        "name": "Mexico",
        "flag": "🇲🇽",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Korea Republic",
        "flag": "🇰🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 67,
        "probabilities": {
          "home_win": 38,
          "draw": 28,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m032",
      "official_match_number": 32,
      "kickoff_label": "M032",
      "sort_order": 32,
      "date": "2026-06-20",
      "time": "03:00",
      "stage": "小组赛",
      "group": "D",
      "venue": "Seattle Stadium",
      "home_team": {
        "name": "USA",
        "flag": "🇺🇸",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Australia",
        "flag": "🇦🇺",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 71,
        "probabilities": {
          "home_win": 42,
          "draw": 22,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m030",
      "official_match_number": 30,
      "kickoff_label": "M030",
      "sort_order": 30,
      "date": "2026-06-20",
      "time": "06:00",
      "stage": "小组赛",
      "group": "C",
      "venue": "Boston Stadium",
      "home_team": {
        "name": "Scotland",
        "flag": "🏴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Morocco",
        "flag": "🇲🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 69,
        "probabilities": {
          "home_win": 40,
          "draw": 20,
          "away_win": 40
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m029",
      "official_match_number": 29,
      "kickoff_label": "M029",
      "sort_order": 29,
      "date": "2026-06-20",
      "time": "08:30",
      "stage": "小组赛",
      "group": "C",
      "venue": "Philadelphia Stadium",
      "home_team": {
        "name": "Brazil",
        "flag": "🇧🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Haiti",
        "flag": "🇭🇹",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 68,
        "probabilities": {
          "home_win": 39,
          "draw": 29,
          "away_win": 32
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m031",
      "official_match_number": 31,
      "kickoff_label": "M031",
      "sort_order": 31,
      "date": "2026-06-20",
      "time": "11:00",
      "stage": "小组赛",
      "group": "D",
      "venue": "San Francisco Bay Area Stadium",
      "home_team": {
        "name": "Türkiye",
        "flag": "🇹🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Paraguay",
        "flag": "🇵🇾",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 70,
        "probabilities": {
          "home_win": 41,
          "draw": 21,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m036",
      "official_match_number": 36,
      "kickoff_label": "M036",
      "sort_order": 36,
      "date": "2026-06-20",
      "time": "12:00",
      "stage": "小组赛",
      "group": "F",
      "venue": "Estadio Monterrey",
      "home_team": {
        "name": "Tunisia",
        "flag": "🇹🇳",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Japan",
        "flag": "🇯🇵",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 75,
        "probabilities": {
          "home_win": 46,
          "draw": 26,
          "away_win": 28
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m035",
      "official_match_number": 35,
      "kickoff_label": "M035",
      "sort_order": 35,
      "date": "2026-06-21",
      "time": "01:00",
      "stage": "小组赛",
      "group": "F",
      "venue": "Houston Stadium",
      "home_team": {
        "name": "Netherlands",
        "flag": "🇳🇱",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Sweden",
        "flag": "🇸🇪",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 74,
        "probabilities": {
          "home_win": 45,
          "draw": 25,
          "away_win": 30
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m033",
      "official_match_number": 33,
      "kickoff_label": "M033",
      "sort_order": 33,
      "date": "2026-06-21",
      "time": "04:00",
      "stage": "小组赛",
      "group": "E",
      "venue": "Toronto Stadium",
      "home_team": {
        "name": "Germany",
        "flag": "🇩🇪",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Côte d'Ivoire",
        "flag": "🏟️",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 72,
        "probabilities": {
          "home_win": 43,
          "draw": 23,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m034",
      "official_match_number": 34,
      "kickoff_label": "M034",
      "sort_order": 34,
      "date": "2026-06-21",
      "time": "08:00",
      "stage": "小组赛",
      "group": "E",
      "venue": "Kansas City Stadium",
      "home_team": {
        "name": "Ecuador",
        "flag": "🇪🇨",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Curaçao",
        "flag": "🇨🇼",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 73,
        "probabilities": {
          "home_win": 44,
          "draw": 24,
          "away_win": 32
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m038",
      "official_match_number": 38,
      "kickoff_label": "M038",
      "sort_order": 38,
      "date": "2026-06-22",
      "time": "00:00",
      "stage": "小组赛",
      "group": "H",
      "venue": "Atlanta Stadium",
      "home_team": {
        "name": "Spain",
        "flag": "🇪🇸",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Saudi Arabia",
        "flag": "🇸🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 77,
        "probabilities": {
          "home_win": 48,
          "draw": 28,
          "away_win": 24
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m039",
      "official_match_number": 39,
      "kickoff_label": "M039",
      "sort_order": 39,
      "date": "2026-06-22",
      "time": "03:00",
      "stage": "小组赛",
      "group": "G",
      "venue": "Los Angeles Stadium",
      "home_team": {
        "name": "Belgium",
        "flag": "🇧🇪",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "IR Iran",
        "flag": "🇮🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 78,
        "probabilities": {
          "home_win": 49,
          "draw": 29,
          "away_win": 22
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m037",
      "official_match_number": 37,
      "kickoff_label": "M037",
      "sort_order": 37,
      "date": "2026-06-22",
      "time": "06:00",
      "stage": "小组赛",
      "group": "H",
      "venue": "Miami Stadium",
      "home_team": {
        "name": "Uruguay",
        "flag": "🇺🇾",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Cabo Verde",
        "flag": "🇨🇻",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 76,
        "probabilities": {
          "home_win": 47,
          "draw": 27,
          "away_win": 26
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m040",
      "official_match_number": 40,
      "kickoff_label": "M040",
      "sort_order": 40,
      "date": "2026-06-22",
      "time": "09:00",
      "stage": "小组赛",
      "group": "G",
      "venue": "BC Place Vancouver",
      "home_team": {
        "name": "New Zealand",
        "flag": "🇳🇿",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Egypt",
        "flag": "🇪🇬",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 79,
        "probabilities": {
          "home_win": 50,
          "draw": 20,
          "away_win": 30
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m043",
      "official_match_number": 43,
      "kickoff_label": "M043",
      "sort_order": 43,
      "date": "2026-06-23",
      "time": "01:00",
      "stage": "小组赛",
      "group": "J",
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "Argentina",
        "flag": "🇦🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Austria",
        "flag": "🇦🇹",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 61,
        "probabilities": {
          "home_win": 53,
          "draw": 23,
          "away_win": 24
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m042",
      "official_match_number": 42,
      "kickoff_label": "M042",
      "sort_order": 42,
      "date": "2026-06-23",
      "time": "05:00",
      "stage": "小组赛",
      "group": "I",
      "venue": "Philadelphia Stadium",
      "home_team": {
        "name": "France",
        "flag": "🇫🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Iraq",
        "flag": "🇮🇶",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 60,
        "probabilities": {
          "home_win": 52,
          "draw": 22,
          "away_win": 26
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m041",
      "official_match_number": 41,
      "kickoff_label": "M041",
      "sort_order": 41,
      "date": "2026-06-23",
      "time": "08:00",
      "stage": "小组赛",
      "group": "I",
      "venue": "New York New Jersey Stadium",
      "home_team": {
        "name": "Norway",
        "flag": "🇳🇴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Senegal",
        "flag": "🇸🇳",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 80,
        "probabilities": {
          "home_win": 51,
          "draw": 21,
          "away_win": 28
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m044",
      "official_match_number": 44,
      "kickoff_label": "M044",
      "sort_order": 44,
      "date": "2026-06-23",
      "time": "11:00",
      "stage": "小组赛",
      "group": "J",
      "venue": "San Francisco Bay Area Stadium",
      "home_team": {
        "name": "Jordan",
        "flag": "🇯🇴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Algeria",
        "flag": "🇩🇿",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 62,
        "probabilities": {
          "home_win": 54,
          "draw": 24,
          "away_win": 22
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m047",
      "official_match_number": 47,
      "kickoff_label": "M047",
      "sort_order": 47,
      "date": "2026-06-24",
      "time": "01:00",
      "stage": "小组赛",
      "group": "K",
      "venue": "Houston Stadium",
      "home_team": {
        "name": "Portugal",
        "flag": "🇵🇹",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Uzbekistan",
        "flag": "🇺🇿",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 65,
        "probabilities": {
          "home_win": 57,
          "draw": 27,
          "away_win": 16
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m045",
      "official_match_number": 45,
      "kickoff_label": "M045",
      "sort_order": 45,
      "date": "2026-06-24",
      "time": "04:00",
      "stage": "小组赛",
      "group": "L",
      "venue": "Boston Stadium",
      "home_team": {
        "name": "England",
        "flag": "🏴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Ghana",
        "flag": "🇬🇭",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 63,
        "probabilities": {
          "home_win": 55,
          "draw": 25,
          "away_win": 20
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m046",
      "official_match_number": 46,
      "kickoff_label": "M046",
      "sort_order": 46,
      "date": "2026-06-24",
      "time": "07:00",
      "stage": "小组赛",
      "group": "L",
      "venue": "Toronto Stadium",
      "home_team": {
        "name": "Panama",
        "flag": "🇵🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Croatia",
        "flag": "🇭🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 64,
        "probabilities": {
          "home_win": 56,
          "draw": 26,
          "away_win": 18
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m048",
      "official_match_number": 48,
      "kickoff_label": "M048",
      "sort_order": 48,
      "date": "2026-06-24",
      "time": "10:00",
      "stage": "小组赛",
      "group": "K",
      "venue": "Estadio Guadalajara",
      "home_team": {
        "name": "Colombia",
        "flag": "🇨🇴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Congo DR",
        "flag": "🇨🇩",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 66,
        "probabilities": {
          "home_win": 34,
          "draw": 28,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m051",
      "official_match_number": 51,
      "kickoff_label": "M051",
      "sort_order": 51,
      "date": "2026-06-25",
      "time": "03:00",
      "stage": "小组赛",
      "group": "B",
      "venue": "BC Place Vancouver",
      "home_team": {
        "name": "Switzerland",
        "flag": "🇨🇭",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Canada",
        "flag": "🇨🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 69,
        "probabilities": {
          "home_win": 37,
          "draw": 21,
          "away_win": 42
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m052",
      "official_match_number": 52,
      "kickoff_label": "M052",
      "sort_order": 52,
      "date": "2026-06-25",
      "time": "03:00",
      "stage": "小组赛",
      "group": "B",
      "venue": "Seattle Stadium",
      "home_team": {
        "name": "Bosnia and Herzegovina",
        "flag": "🇧🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Qatar",
        "flag": "🇶🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 70,
        "probabilities": {
          "home_win": 38,
          "draw": 22,
          "away_win": 40
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m049",
      "official_match_number": 49,
      "kickoff_label": "M049",
      "sort_order": 49,
      "date": "2026-06-25",
      "time": "06:00",
      "stage": "小组赛",
      "group": "C",
      "venue": "Miami Stadium",
      "home_team": {
        "name": "Scotland",
        "flag": "🏴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Brazil",
        "flag": "🇧🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 67,
        "probabilities": {
          "home_win": 35,
          "draw": 29,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m050",
      "official_match_number": 50,
      "kickoff_label": "M050",
      "sort_order": 50,
      "date": "2026-06-25",
      "time": "06:00",
      "stage": "小组赛",
      "group": "C",
      "venue": "Atlanta Stadium",
      "home_team": {
        "name": "Morocco",
        "flag": "🇲🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Haiti",
        "flag": "🇭🇹",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 68,
        "probabilities": {
          "home_win": 36,
          "draw": 20,
          "away_win": 44
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m053",
      "official_match_number": 53,
      "kickoff_label": "M053",
      "sort_order": 53,
      "date": "2026-06-25",
      "time": "09:00",
      "stage": "小组赛",
      "group": "A",
      "venue": "Mexico City Stadium",
      "home_team": {
        "name": "Czechia",
        "flag": "🇨🇿",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Mexico",
        "flag": "🇲🇽",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 71,
        "probabilities": {
          "home_win": 39,
          "draw": 23,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m054",
      "official_match_number": 54,
      "kickoff_label": "M054",
      "sort_order": 54,
      "date": "2026-06-25",
      "time": "09:00",
      "stage": "小组赛",
      "group": "A",
      "venue": "Estadio Monterrey",
      "home_team": {
        "name": "South Africa",
        "flag": "🇿🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Korea Republic",
        "flag": "🇰🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 72,
        "probabilities": {
          "home_win": 40,
          "draw": 24,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m055",
      "official_match_number": 55,
      "kickoff_label": "M055",
      "sort_order": 55,
      "date": "2026-06-26",
      "time": "04:00",
      "stage": "小组赛",
      "group": "E",
      "venue": "Philadelphia Stadium",
      "home_team": {
        "name": "Curaçao",
        "flag": "🇨🇼",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Côte d'Ivoire",
        "flag": "🏟️",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 73,
        "probabilities": {
          "home_win": 41,
          "draw": 25,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m056",
      "official_match_number": 56,
      "kickoff_label": "M056",
      "sort_order": 56,
      "date": "2026-06-26",
      "time": "04:00",
      "stage": "小组赛",
      "group": "E",
      "venue": "New York New Jersey Stadium",
      "home_team": {
        "name": "Ecuador",
        "flag": "🇪🇨",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Germany",
        "flag": "🇩🇪",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 74,
        "probabilities": {
          "home_win": 42,
          "draw": 26,
          "away_win": 32
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m057",
      "official_match_number": 57,
      "kickoff_label": "M057",
      "sort_order": 57,
      "date": "2026-06-26",
      "time": "07:00",
      "stage": "小组赛",
      "group": "F",
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "Japan",
        "flag": "🇯🇵",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Sweden",
        "flag": "🇸🇪",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 75,
        "probabilities": {
          "home_win": 43,
          "draw": 27,
          "away_win": 30
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m058",
      "official_match_number": 58,
      "kickoff_label": "M058",
      "sort_order": 58,
      "date": "2026-06-26",
      "time": "07:00",
      "stage": "小组赛",
      "group": "F",
      "venue": "Kansas City Stadium",
      "home_team": {
        "name": "Tunisia",
        "flag": "🇹🇳",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Netherlands",
        "flag": "🇳🇱",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 76,
        "probabilities": {
          "home_win": 44,
          "draw": 28,
          "away_win": 28
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m059",
      "official_match_number": 59,
      "kickoff_label": "M059",
      "sort_order": 59,
      "date": "2026-06-26",
      "time": "10:00",
      "stage": "小组赛",
      "group": "D",
      "venue": "Los Angeles Stadium",
      "home_team": {
        "name": "Türkiye",
        "flag": "🇹🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "USA",
        "flag": "🇺🇸",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 77,
        "probabilities": {
          "home_win": 45,
          "draw": 29,
          "away_win": 26
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m060",
      "official_match_number": 60,
      "kickoff_label": "M060",
      "sort_order": 60,
      "date": "2026-06-26",
      "time": "10:00",
      "stage": "小组赛",
      "group": "D",
      "venue": "San Francisco Bay Area Stadium",
      "home_team": {
        "name": "Paraguay",
        "flag": "🇵🇾",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Australia",
        "flag": "🇦🇺",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 78,
        "probabilities": {
          "home_win": 46,
          "draw": 20,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m061",
      "official_match_number": 61,
      "kickoff_label": "M061",
      "sort_order": 61,
      "date": "2026-06-27",
      "time": "03:00",
      "stage": "小组赛",
      "group": "I",
      "venue": "Boston Stadium",
      "home_team": {
        "name": "Norway",
        "flag": "🇳🇴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "France",
        "flag": "🇫🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 79,
        "probabilities": {
          "home_win": 47,
          "draw": 21,
          "away_win": 32
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m062",
      "official_match_number": 62,
      "kickoff_label": "M062",
      "sort_order": 62,
      "date": "2026-06-27",
      "time": "03:00",
      "stage": "小组赛",
      "group": "I",
      "venue": "Toronto Stadium",
      "home_team": {
        "name": "Senegal",
        "flag": "🇸🇳",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Iraq",
        "flag": "🇮🇶",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 80,
        "probabilities": {
          "home_win": 48,
          "draw": 22,
          "away_win": 30
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m065",
      "official_match_number": 65,
      "kickoff_label": "M065",
      "sort_order": 65,
      "date": "2026-06-27",
      "time": "08:00",
      "stage": "小组赛",
      "group": "H",
      "venue": "Houston Stadium",
      "home_team": {
        "name": "Cabo Verde",
        "flag": "🇨🇻",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Saudi Arabia",
        "flag": "🇸🇦",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 62,
        "probabilities": {
          "home_win": 51,
          "draw": 25,
          "away_win": 24
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m066",
      "official_match_number": 66,
      "kickoff_label": "M066",
      "sort_order": 66,
      "date": "2026-06-27",
      "time": "08:00",
      "stage": "小组赛",
      "group": "H",
      "venue": "Estadio Guadalajara",
      "home_team": {
        "name": "Uruguay",
        "flag": "🇺🇾",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Spain",
        "flag": "🇪🇸",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 63,
        "probabilities": {
          "home_win": 52,
          "draw": 26,
          "away_win": 22
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m063",
      "official_match_number": 63,
      "kickoff_label": "M063",
      "sort_order": 63,
      "date": "2026-06-27",
      "time": "11:00",
      "stage": "小组赛",
      "group": "G",
      "venue": "Seattle Stadium",
      "home_team": {
        "name": "Egypt",
        "flag": "🇪🇬",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "IR Iran",
        "flag": "🇮🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 60,
        "probabilities": {
          "home_win": 49,
          "draw": 23,
          "away_win": 28
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m064",
      "official_match_number": 64,
      "kickoff_label": "M064",
      "sort_order": 64,
      "date": "2026-06-27",
      "time": "11:00",
      "stage": "小组赛",
      "group": "G",
      "venue": "BC Place Vancouver",
      "home_team": {
        "name": "New Zealand",
        "flag": "🇳🇿",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Belgium",
        "flag": "🇧🇪",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 61,
        "probabilities": {
          "home_win": 50,
          "draw": 24,
          "away_win": 26
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m067",
      "official_match_number": 67,
      "kickoff_label": "M067",
      "sort_order": 67,
      "date": "2026-06-28",
      "time": "05:00",
      "stage": "小组赛",
      "group": "L",
      "venue": "New York New Jersey Stadium",
      "home_team": {
        "name": "Panama",
        "flag": "🇵🇦",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "England",
        "flag": "🏴",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 64,
        "probabilities": {
          "home_win": 53,
          "draw": 27,
          "away_win": 20
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m068",
      "official_match_number": 68,
      "kickoff_label": "M068",
      "sort_order": 68,
      "date": "2026-06-28",
      "time": "05:00",
      "stage": "小组赛",
      "group": "L",
      "venue": "Philadelphia Stadium",
      "home_team": {
        "name": "Croatia",
        "flag": "🇭🇷",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Ghana",
        "flag": "🇬🇭",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 65,
        "probabilities": {
          "home_win": 54,
          "draw": 28,
          "away_win": 18
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m071",
      "official_match_number": 71,
      "kickoff_label": "M071",
      "sort_order": 71,
      "date": "2026-06-28",
      "time": "07:30",
      "stage": "小组赛",
      "group": "K",
      "venue": "Miami Stadium",
      "home_team": {
        "name": "Colombia",
        "flag": "🇨🇴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Portugal",
        "flag": "🇵🇹",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 2,
        "away_score": 0,
        "confidence": 68,
        "probabilities": {
          "home_win": 57,
          "draw": 21,
          "away_win": 22
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m072",
      "official_match_number": 72,
      "kickoff_label": "M072",
      "sort_order": 72,
      "date": "2026-06-28",
      "time": "07:30",
      "stage": "小组赛",
      "group": "K",
      "venue": "Atlanta Stadium",
      "home_team": {
        "name": "Congo DR",
        "flag": "🇨🇩",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Uzbekistan",
        "flag": "🇺🇿",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 69,
        "probabilities": {
          "home_win": 34,
          "draw": 22,
          "away_win": 44
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m069",
      "official_match_number": 69,
      "kickoff_label": "M069",
      "sort_order": 69,
      "date": "2026-06-28",
      "time": "10:00",
      "stage": "小组赛",
      "group": "J",
      "venue": "Kansas City Stadium",
      "home_team": {
        "name": "Algeria",
        "flag": "🇩🇿",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Austria",
        "flag": "🇦🇹",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 66,
        "probabilities": {
          "home_win": 55,
          "draw": 29,
          "away_win": 16
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m070",
      "official_match_number": 70,
      "kickoff_label": "M070",
      "sort_order": 70,
      "date": "2026-06-28",
      "time": "10:00",
      "stage": "小组赛",
      "group": "J",
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "Jordan",
        "flag": "🇯🇴",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Argentina",
        "flag": "🇦🇷",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 2,
        "confidence": 67,
        "probabilities": {
          "home_win": 56,
          "draw": 20,
          "away_win": 24
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m073",
      "official_match_number": 73,
      "kickoff_label": "M073",
      "sort_order": 73,
      "date": "2026-06-29",
      "time": "03:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Los Angeles Stadium",
      "home_team": {
        "name": "Group A runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Group B runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 35,
          "draw": 23,
          "away_win": 42
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m076",
      "official_match_number": 76,
      "kickoff_label": "M076",
      "sort_order": 76,
      "date": "2026-06-30",
      "time": "01:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Houston Stadium",
      "home_team": {
        "name": "Group C winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Group F runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 38,
          "draw": 26,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m074",
      "official_match_number": 74,
      "kickoff_label": "M074",
      "sort_order": 74,
      "date": "2026-06-30",
      "time": "04:30",
      "stage": "32强赛",
      "group": null,
      "venue": "Boston Stadium",
      "home_team": {
        "name": "Group E winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Best third-placed team from Groups A/B/C/D/F",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 36,
          "draw": 24,
          "away_win": 40
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m075",
      "official_match_number": 75,
      "kickoff_label": "M075",
      "sort_order": 75,
      "date": "2026-06-30",
      "time": "09:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Estadio Monterrey",
      "home_team": {
        "name": "Group F winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Group C runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 37,
          "draw": 25,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m078",
      "official_match_number": 78,
      "kickoff_label": "M078",
      "sort_order": 78,
      "date": "2026-07-01",
      "time": "01:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "Group E runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Group I runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 40,
          "draw": 28,
          "away_win": 32
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m077",
      "official_match_number": 77,
      "kickoff_label": "M077",
      "sort_order": 77,
      "date": "2026-07-01",
      "time": "05:00",
      "stage": "32强赛",
      "group": null,
      "venue": "New York New Jersey Stadium",
      "home_team": {
        "name": "Group I winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Best third-placed team from Groups C/D/F/G/H",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 39,
          "draw": 27,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m079",
      "official_match_number": 79,
      "kickoff_label": "M079",
      "sort_order": 79,
      "date": "2026-07-01",
      "time": "09:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Mexico City Stadium",
      "home_team": {
        "name": "Group A winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Best third-placed team from Groups C/E/F/H/I",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 41,
          "draw": 29,
          "away_win": 30
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m080",
      "official_match_number": 80,
      "kickoff_label": "M080",
      "sort_order": 80,
      "date": "2026-07-02",
      "time": "00:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Atlanta Stadium",
      "home_team": {
        "name": "Group L winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Best third-placed team from Groups E/H/I/J/K",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 42,
          "draw": 20,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m082",
      "official_match_number": 82,
      "kickoff_label": "M082",
      "sort_order": 82,
      "date": "2026-07-02",
      "time": "04:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Seattle Stadium",
      "home_team": {
        "name": "Group G winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Best third-placed team from Groups A/E/H/I/J",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 44,
          "draw": 22,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m081",
      "official_match_number": 81,
      "kickoff_label": "M081",
      "sort_order": 81,
      "date": "2026-07-02",
      "time": "08:00",
      "stage": "32强赛",
      "group": null,
      "venue": "San Francisco Bay Area Stadium",
      "home_team": {
        "name": "Group D winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Best third-placed team from Groups B/E/F/I/J",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 43,
          "draw": 21,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m084",
      "official_match_number": 84,
      "kickoff_label": "M084",
      "sort_order": 84,
      "date": "2026-07-03",
      "time": "03:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Los Angeles Stadium",
      "home_team": {
        "name": "Group H winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Group J runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 46,
          "draw": 24,
          "away_win": 30
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m083",
      "official_match_number": 83,
      "kickoff_label": "M083",
      "sort_order": 83,
      "date": "2026-07-03",
      "time": "07:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Toronto Stadium",
      "home_team": {
        "name": "Group K runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Group L runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 45,
          "draw": 23,
          "away_win": 32
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m085",
      "official_match_number": 85,
      "kickoff_label": "M085",
      "sort_order": 85,
      "date": "2026-07-03",
      "time": "11:00",
      "stage": "32强赛",
      "group": null,
      "venue": "BC Place Vancouver",
      "home_team": {
        "name": "Group B winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Best third-placed team from Groups E/F/G/I/J",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 47,
          "draw": 25,
          "away_win": 28
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m088",
      "official_match_number": 88,
      "kickoff_label": "M088",
      "sort_order": 88,
      "date": "2026-07-04",
      "time": "02:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "Group D runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Group G runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 50,
          "draw": 28,
          "away_win": 22
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m086",
      "official_match_number": 86,
      "kickoff_label": "M086",
      "sort_order": 86,
      "date": "2026-07-04",
      "time": "06:00",
      "stage": "32强赛",
      "group": null,
      "venue": "Miami Stadium",
      "home_team": {
        "name": "Group J winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Group H runners-up",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 48,
          "draw": 26,
          "away_win": 26
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m087",
      "official_match_number": 87,
      "kickoff_label": "M087",
      "sort_order": 87,
      "date": "2026-07-04",
      "time": "09:30",
      "stage": "32强赛",
      "group": null,
      "venue": "Kansas City Stadium",
      "home_team": {
        "name": "Group K winners",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Best third-placed team from Groups D/E/I/J/L",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 49,
          "draw": 27,
          "away_win": 24
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m090",
      "official_match_number": 90,
      "kickoff_label": "M090",
      "sort_order": 90,
      "date": "2026-07-05",
      "time": "01:00",
      "stage": "16强赛",
      "group": null,
      "venue": "Houston Stadium",
      "home_team": {
        "name": "Winner Match 73",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 75",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 52,
          "draw": 20,
          "away_win": 28
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m089",
      "official_match_number": 89,
      "kickoff_label": "M089",
      "sort_order": 89,
      "date": "2026-07-05",
      "time": "05:00",
      "stage": "16强赛",
      "group": null,
      "venue": "Philadelphia Stadium",
      "home_team": {
        "name": "Winner Match 74",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 77",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 51,
          "draw": 29,
          "away_win": 20
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m091",
      "official_match_number": 91,
      "kickoff_label": "M091",
      "sort_order": 91,
      "date": "2026-07-06",
      "time": "04:00",
      "stage": "16强赛",
      "group": null,
      "venue": "New York New Jersey Stadium",
      "home_team": {
        "name": "Winner Match 76",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 78",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 53,
          "draw": 21,
          "away_win": 26
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m092",
      "official_match_number": 92,
      "kickoff_label": "M092",
      "sort_order": 92,
      "date": "2026-07-06",
      "time": "08:00",
      "stage": "16强赛",
      "group": null,
      "venue": "Mexico City Stadium",
      "home_team": {
        "name": "Winner Match 79",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 80",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 54,
          "draw": 22,
          "away_win": 24
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m093",
      "official_match_number": 93,
      "kickoff_label": "M093",
      "sort_order": 93,
      "date": "2026-07-07",
      "time": "03:00",
      "stage": "16强赛",
      "group": null,
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "Winner Match 83",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 84",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 55,
          "draw": 23,
          "away_win": 22
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m094",
      "official_match_number": 94,
      "kickoff_label": "M094",
      "sort_order": 94,
      "date": "2026-07-07",
      "time": "08:00",
      "stage": "16强赛",
      "group": null,
      "venue": "Seattle Stadium",
      "home_team": {
        "name": "Winner Match 81",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 82",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 56,
          "draw": 24,
          "away_win": 20
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m095",
      "official_match_number": 95,
      "kickoff_label": "M095",
      "sort_order": 95,
      "date": "2026-07-08",
      "time": "00:00",
      "stage": "16强赛",
      "group": null,
      "venue": "Atlanta Stadium",
      "home_team": {
        "name": "Winner Match 86",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 88",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 57,
          "draw": 25,
          "away_win": 18
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m096",
      "official_match_number": 96,
      "kickoff_label": "M096",
      "sort_order": 96,
      "date": "2026-07-08",
      "time": "04:00",
      "stage": "16强赛",
      "group": null,
      "venue": "BC Place Vancouver",
      "home_team": {
        "name": "Winner Match 85",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 87",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 34,
          "draw": 26,
          "away_win": 40
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m097",
      "official_match_number": 97,
      "kickoff_label": "M097",
      "sort_order": 97,
      "date": "2026-07-10",
      "time": "04:00",
      "stage": "1/4 决赛",
      "group": null,
      "venue": "Boston Stadium",
      "home_team": {
        "name": "Winner Match 89",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 90",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 35,
          "draw": 27,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m098",
      "official_match_number": 98,
      "kickoff_label": "M098",
      "sort_order": 98,
      "date": "2026-07-11",
      "time": "03:00",
      "stage": "1/4 决赛",
      "group": null,
      "venue": "Los Angeles Stadium",
      "home_team": {
        "name": "Winner Match 93",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 94",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 36,
          "draw": 28,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m099",
      "official_match_number": 99,
      "kickoff_label": "M099",
      "sort_order": 99,
      "date": "2026-07-12",
      "time": "05:00",
      "stage": "1/4 决赛",
      "group": null,
      "venue": "Miami Stadium",
      "home_team": {
        "name": "Winner Match 91",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 92",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 37,
          "draw": 29,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m100",
      "official_match_number": 100,
      "kickoff_label": "M100",
      "sort_order": 100,
      "date": "2026-07-12",
      "time": "09:00",
      "stage": "1/4 决赛",
      "group": null,
      "venue": "Kansas City Stadium",
      "home_team": {
        "name": "Winner Match 95",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 96",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 38,
          "draw": 20,
          "away_win": 42
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m101",
      "official_match_number": 101,
      "kickoff_label": "M101",
      "sort_order": 101,
      "date": "2026-07-15",
      "time": "03:00",
      "stage": "半决赛",
      "group": null,
      "venue": "Dallas Stadium",
      "home_team": {
        "name": "Winner Match 97",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 98",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 39,
          "draw": 21,
          "away_win": 40
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m102",
      "official_match_number": 102,
      "kickoff_label": "M102",
      "sort_order": 102,
      "date": "2026-07-16",
      "time": "03:00",
      "stage": "半决赛",
      "group": null,
      "venue": "Atlanta Stadium",
      "home_team": {
        "name": "Winner Match 99",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 100",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 40,
          "draw": 22,
          "away_win": 38
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m103",
      "official_match_number": 103,
      "kickoff_label": "M103",
      "sort_order": 103,
      "date": "2026-07-19",
      "time": "05:00",
      "stage": "季军赛",
      "group": null,
      "venue": "Miami Stadium",
      "home_team": {
        "name": "Loser Match 101",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Loser Match 102",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 1,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 41,
          "draw": 23,
          "away_win": 36
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    },
    {
      "id": "fwc2026-m104",
      "official_match_number": 104,
      "kickoff_label": "M104",
      "sort_order": 104,
      "date": "2026-07-20",
      "time": "03:00",
      "stage": "决赛",
      "group": null,
      "venue": "New York New Jersey Stadium",
      "home_team": {
        "name": "Winner Match 101",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "away_team": {
        "name": "Winner Match 102",
        "flag": "🏁",
        "fifa_rank": null,
        "form": []
      },
      "status": "not_started",
      "score": null,
      "prediction": {
        "home_score": 0,
        "away_score": 1,
        "confidence": 52,
        "probabilities": {
          "home_win": 42,
          "draw": 24,
          "away_win": 34
        },
        "reasoning": "赛程依据 FIFA 官方页面整理，预测卡当前为前端静态占位，用于展示卡片结构。",
        "predicted_at": "2026-04-18T00:00:00Z"
      },
      "head_to_head": null,
      "key_players": {
        "home_injured": [],
        "away_suspended": []
      }
    }
  ],
  "last_updated": "2026-04-20T00:00:00Z",
  "total": 104
};
