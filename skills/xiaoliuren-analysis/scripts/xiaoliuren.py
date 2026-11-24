#!/usr/bin/env python3
"""
小六壬占卜脚本
按农历月、日、时辰三数起课，推算六宫掌诀（大安/留连/速喜/赤口/小吉/空亡）。
内置 bazi_core.py（v1.1 起自包含，不再依赖外部技能）做公历→农历转换。

用法:
  python xiaoliuren.py date=2026-08-09 hour=10 minute=0
  # date 省略默认今天；hour/minute 用 24 小时制本地时间
  # 可选 city=北京（默认北京）

输出 JSON: {input, lunar, gan_zhi, xun(三传), result(落宫), meaning, advice}
"""
import sys
import os
import json
from datetime import datetime

# ── 六宫基础表 ──────────────────────────────────────────────
# 顺序即掌诀固定顺序（大安起正月，顺数）
# 数据来源：2026-08 调研（5 源交叉验证），采用主流版：小吉=水/黑/北/六合/5·8·11，
# 空亡=土/黄/中央/勾陈/6·9·12；起句用经典口诀（留连卒未归时、速喜人便至时）。
# 版本分歧（流传变体）：小吉另作木/1·5·7，留连另作"人未归时"，速喜另作"人即至时"。
LIUREN = {
    1: {"name": "大安", "symbol": "身不动时", "ji": "吉",
        "element": "木", "direction": "东方", "number": "1、5、7", "shen": "青龙",
        "quick": "大安事事昌，求谋在东方，失物去不远，宅舍保安康，行人身未动，病者主无妨",
        "detail": "大安：身不动时，五行属木，颜色青色，方位东方，临青龙，凡谋事主一、五、七。"
                  "有静止、心安、吉祥之含义，是六宫中最吉的之一。"
                  "问工作：顺利稳当；问感情：关系稳定；问财运：正财可期；问健康：无大碍；问失物：去不远。"},
    2: {"name": "留连", "symbol": "卒未归时", "ji": "凶",
        "element": "水", "direction": "北方", "number": "2、8、10", "shen": "玄武",
        "quick": "留连事难成，求谋日未明，官事只宜缓，去者未回程，失物南方见，急讨方称心",
        "detail": "留连：卒未归时，五行属水，颜色黑色，方位北方，临玄武，凡谋事主二、八、十。"
                  "有喑味不明、延迟、纠缠、拖延、漫长之含义。"
                  "问工作：进展慢；问感情：暧昧纠缠；问财运：财来财去；问健康：小恙拖久；问失物：急讨方称心。"},
    3: {"name": "速喜", "symbol": "人便至时", "ji": "吉",
        "element": "火", "direction": "南方", "number": "3、6、9", "shen": "朱雀",
        "quick": "速喜喜来临，求财向南行，失物申未午，逢人路上寻，官事有福德，病者无祸侵",
        "detail": "速喜：人便至时，五行属火，颜色红色，方位南方，临朱雀，谋事主三、六、九。"
                  "有快速、喜庆、吉利之含义，指时机已到。"
                  "问工作：有进展好消息；问感情：桃花旺；问财运：进财快；问健康：康复快；问失物：申未午方寻。"},
    4: {"name": "赤口", "symbol": "官事凶时", "ji": "凶",
        "element": "金", "direction": "西方", "number": "4、7、10", "shen": "白虎",
        "quick": "赤口主口舌，官非切要防，失物急去寻，行人有惊慌，鸡犬多作怪，病者出西方",
        "detail": "赤口：官事凶时，五行属金，颜色白色，方位西方，临白虎，谋事主四、七、十。"
                  "有不吉、惊恐、凶险、口舌是非之含义。"
                  "问工作：防小人；问感情：易争吵；问财运：防破财；问健康：防炎症外伤；问失物：急去寻。"},
    5: {"name": "小吉", "symbol": "人来喜时", "ji": "吉",
        "element": "水", "direction": "北方", "number": "5、8、11", "shen": "六合",
        "quick": "小吉最吉昌，路上好商量，阳人来报喜，失物在坤方，行人即便至，交关甚是强",
        "detail": "小吉：人来喜时，五行属水，颜色黑色，方位北方（断辞另指坤方/西南），临六合，凡谋事主五、八、十一。"
                  "有和合、吉利之含义，六合大吉。"
                  "问工作：贵人提携；问感情：和和美美；问财运：偏财进账；问健康：平安；问失物：坤方（西南）寻。"},
    6: {"name": "空亡", "symbol": "音信稀时", "ji": "凶",
        "element": "土", "direction": "中央", "number": "6、9、12", "shen": "勾陈",
        "quick": "空亡事不长，阴人多乖张，求财无利益，行人有灾殃，失物寻不见，官事主刑伤",
        "detail": "空亡：音信稀时，五行属土，颜色黄色，方位中央，临勾陈，谋事主六、九、十二。"
                  "有不吉、无结果、忧虑之含义。"
                  "问工作：易落空；问感情：没结果；问财运：求财难得；问健康：防脾胃虚；问失物：寻不见。"},
}

SHICHEN_ORDER = "子丑寅卯辰巳午未申酉戌亥"  # 子=1 ... 亥=12


def get_lunar(dt_local: datetime, city: str = "北京"):
    """内置 bazi_core 农历转换（v1.1 起自包含，不再依赖外部技能）。返回 (month_no, day, shichen_idx_1based)"""
    import io, contextlib
    import pytz
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        from bazi_core import locate_lunar_date
    # 城市坐标表（本技能自带 references/cities.json）
    cities_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "cities.json")
    with open(cities_path, "r", encoding="utf-8") as f:
        cities = json.load(f)
    if city not in cities:
        raise ValueError(f"城市不支持: {city}，请用 references/cities.json 中的现名")
    info = cities[city]
    tz = pytz.timezone(info["tz"])
    if dt_local.tzinfo is None:
        dt_local = tz.localize(dt_local)
    r = locate_lunar_date(dt_local, info["lat"], info["lon"], info["tz"], True)
    ld = r["lunar"]["date"]
    month_no = ld["month_no"]
    day = ld["day"]
    shichen = ld["shichen"]
    shichen_idx = SHICHEN_ORDER.index(shichen) + 1
    gz = r["lunar"]["gan_zhi"]["four_pillars"]
    month_cn = ld["month_cn"]
    return month_no, day, shichen_idx, shichen, month_cn, gz, r["lunar"]["date"].get("day_cn", "")


def compute(month_no: int, day: int, shichen_idx: int):
    """小六壬起课：大安起正月顺数 → 月上起日 → 日上起时。返回三传 + 落宫。"""
    # 初传：月份落宫（正月=1 大安）
    chu = (month_no - 1) % 6 + 1
    # 中传：从月初传位置起初一，顺数到当日
    zhong = (chu - 1 + day - 1) % 6 + 1
    # 末传：从中传位置起子时(1)，顺数到当前时辰
    mo = (zhong - 1 + shichen_idx - 1) % 6 + 1
    return chu, zhong, mo


def main():
    args = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            args[k.strip()] = v.strip().strip('"').strip("'")

    city = args.get("city", "北京")
    if args.get("date"):
        dt = datetime.strptime(args["date"], "%Y-%m-%d")
        if args.get("hour") is not None:
            dt = dt.replace(hour=int(args["hour"]), minute=int(args.get("minute", 0)))
    else:
        dt = datetime.now()

    month_no, day, shichen_idx, shichen, month_cn, gz, _ = get_lunar(dt, city)

    chu, zhong, mo = compute(month_no, day, shichen_idx)
    gongs = [LIUREN[chu], LIUREN[zhong], LIUREN[mo]]

    # 锐评：按落宫生成
    roasts = {
        1: "今天这卦挺稳，适合按计划走。但别太安逸，稳中求进才是真。",
        2: "留连留连，拖拖拉拉——想做的事趁早决定，别让犹豫吃掉机会。",
        3: "火速有喜！但要小心冲动消费，喜讯来了也别飘。",
        4: "赤口当值，口舌是非多。今天少说话多做事，键盘侠退散！",
        5: "小吉小吉，贵人运在线。今天适合社交，说不定有意外收获～",
        6: "空亡空亡，万事皆空？别慌，放平心态，明天太阳照常升起。",
    }
    result = {
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "city": city},
        "lunar": {"month_no": month_no, "day": day, "shichen": shichen, "month_cn": month_cn},
        "gan_zhi": gz,
        "xun": [{"name": g["name"], "ji": g["ji"]} for g in gongs],
        "result": {k: gongs[-1][k] for k in ["name", "symbol", "ji", "element", "direction", "number", "quick", "detail"]},
        "roast": roasts[mo],
        "advice": LIUREN[mo]["detail"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
