#!/usr/bin/env python3
"""
每日运势脚本 - 基于日干支五行与命主喜用神对比，输出今日运势评分与建议。

用法:
  python daily_fortune.py date=2026-08-07 day_master=丙 favorite=木,火 avoid=金,水
  # date 可省略（默认今天）；favorite/avoid 为喜用神/忌神五行列表

输出 JSON:
  {date, gan_zhi(今日干支), stem(天干), branch(地支),
   stem_element, branch_element, main_element(当日主导五行),
   score(-5~+5), level(吉/平/凶), advice, note}
"""
import sys
import json
from datetime import datetime

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
from bazi_core import gan_zhi_day
import pytz

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
# 天干五行
STEM_ELEMENT = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
                "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
# 地支五行（本气）
BRANCH_ELEMENT = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
                  "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
                  "戌": "土", "亥": "水"}
# 地支藏干（本气/中气/余气）
BRANCH_HIDDEN = {
    "子": "癸", "丑": "己癸辛", "寅": "甲丙戊", "卯": "乙", "辰": "戊乙癸",
    "巳": "丙庚戊", "午": "丁己", "未": "己丁乙", "申": "庚壬戊", "酉": "辛",
    "戌": "戊辛丁", "亥": "壬甲",
}
# 五行生克关系
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def parse_date(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y-%m-%d")


def main():
    args = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            args[k.strip()] = v.strip().strip('"').strip("'")

    # 日期
    if args.get("date"):
        dt_local = parse_date(args["date"])
    else:
        dt_local = datetime.now()
    dt_utc = dt_local.astimezone(pytz.UTC)

    # 今日干支
    gz = gan_zhi_day(dt_utc)
    stem, branch = gz[0], gz[1]
    stem_el = STEM_ELEMENT[stem]
    branch_el = BRANCH_ELEMENT[branch]

    # 主导五行：天干为主，地支为次
    main_el = stem_el
    second_el = branch_el

    # 命主信息
    day_master = args.get("day_master", "")
    fav = [x.strip() for x in args.get("favorite", "").split(",") if x.strip()]
    avoid = [x.strip() for x in args.get("avoid", "").split(",") if x.strip()]

    # 评分：喜用神得势为正，忌神得势为负；±1 为支，±2 为干
    score = 0
    reasons = []
    for el, weight, label in [(stem_el, 2, "天干"), (branch_el, 1, "地支")]:
        if el in fav:
            score += weight
            reasons.append(f"{label} {el} 为喜用神(+{weight})")
        elif el in avoid:
            score -= weight
            reasons.append(f"{label} {el} 为忌神({weight})")
        else:
            reasons.append(f"{label} {el} 平")
    score = max(-5, min(5, score))

    # 等级
    if score >= 3:
        level = "吉"
    elif score <= -3:
        level = "凶"
    elif score >= 1:
        level = "小吉"
    elif score <= -1:
        level = "小凶"
    else:
        level = "平"

    # 建议
    adv = []
    if day_master:
        dm_el = STEM_ELEMENT.get(day_master, "")
        if dm_el:
            sheng_day = SHENG.get(main_el)
            ke_day = KE.get(main_el)
            if main_el == dm_el:
                adv.append("今日与日主同气，状态稳定，适合推进计划")
            elif sheng_day == dm_el:
                adv.append("今日五行生日主，精力较充沛，适合攻坚")
            elif main_el == SHENG.get(dm_el):
                adv.append("今日日主生泄偏多，宜保存精力，避免过度消耗")
            elif main_el == KE.get(dm_el):
                adv.append("今日五行克日主，宜低调行事，重要决策缓一缓")
    if score >= 1:
        adv.append("顺势而为，宜主动争取")
    elif score <= -1:
        adv.append("宜守不宜攻，重要事项避开今日")
    else:
        adv.append("平稳日，按部就班即可")

    note = f"今日主导：{main_el}（天干{stem}属{stem_el}），地支{branch}属{branch_el}"

    result = {
        "date": dt_local.strftime("%Y-%m-%d"),
        "gan_zhi": gz,
        "stem": stem,
        "branch": branch,
        "stem_element": stem_el,
        "branch_element": branch_el,
        "main_element": main_el,
        "score": score,
        "level": level,
        "reasons": reasons,
        "advice": adv,
        "note": note,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
