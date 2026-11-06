"""추가 분석(탐색적): 일본·EU 27개국·호주에 한국·미국과 같은 지표와 판정 조건을 적용한다.

설계: DESIGN.md 9절 (일본·EU는 커밋 6400add, EU 연령 결정과 호주는 커밋 ceeea9e)
입력:
  data/raw/japan_estat_lfs_table2-2-1_20261106.csv  (e-Stat 노동력조사 표 2-2-1, cp932, 만 명)
  data/raw/eu_eurostat_lfsa_egan2_20261106.xlsx     (Eurostat lfsa_egan2, EU27_2020, 천 명)
  data/raw/australia_abs_EQ12_20261106.xlsx         (ABS EQ12, 분기별, 천 명)
출력:
  results/intl_summary.txt     (지역별 비중·격차·조건 판정)
  results/intl_share_series.csv (2019~2025 연도별 비중, 그래프용)
"""
import csv
import io
import warnings
from pathlib import Path

import openpyxl

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
OUT = ROOT / "results"
THRESH = 0.5
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


# ---------- 일본 ----------
JP_FILE = RAW / "japan_estat_lfs_table2-2-1_20261106.csv"
JP = {
    "total": "全産業",
    "high_main": ["情報通信業", "学術研究，専門・技術サービス業"],
    "high_sub": ["情報通信業", "学術研究，専門・技術サービス業", "金融業，保険業"],
    "low": ["宿泊業，飲食サービス業"],
    "young": ["15～19歳", "20～24歳"],
    "young_sub": ["15～19歳", "20～24歳", "25～29歳", "30～34歳"],
    "old": ["35～39歳", "40～44歳", "45～49歳", "50～54歳", "55～59歳", "60～64歳"],  # 55～64歳 구간은 업종별 값이 *** 라 5세 구간을 더함
}


def load_japan():
    rows = list(csv.reader(io.StringIO(JP_FILE.read_text(encoding="cp932"))))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "表章項目 コード")
    head = rows[hi]
    idx = {}
    for name in [JP["total"]] + JP["high_sub"] + JP["low"]:
        hits = [j for j, h in enumerate(head) if h == name]
        assert len(hits) == 1, name
        idx[name] = hits[0]
    cell = {}  # (age, year, industry) -> 만 명
    for r in rows[hi + 1:]:
        if len(r) < 17 or r[5] != "総数" or r[11] != "全国":
            continue
        year = int(r[14].replace("年", ""))
        if year not in YEARS:
            continue
        for name, j in idx.items():
            if r[j] != "***":  # *** = 집계하지 않은 칸. 계산에 필요한 칸이면 아래 share()에서 KeyError로 멈춤
                cell[(r[8], year, name)] = float(r[j])
    return cell


# ---------- EU ----------
EU_FILE = RAW / "eu_eurostat_lfsa_egan2_20261106.xlsx"
EU_GEO = "European Union - 27 countries (from 2020)"
EU = {
    "total": "Total - all NACE activities",
    "high_main": ["Information and communication", "Professional, scientific and technical activities"],
    "high_sub": ["Information and communication", "Professional, scientific and technical activities",
                 "Financial and insurance activities"],
    "low": ["Accommodation and food service activities"],
    "young": ["From 15 to 24 years"],
    "young_sub": ["From 15 to 39 years"],   # 설계서 9.3: 15~34세 대신 가장 가까운 15~39세
    "old": ["From 40 to 64 years"],          # 설계서 9.3: 35~64세 대신 가장 가까운 40~64세
}


def load_eu():
    wb = openpyxl.load_workbook(EU_FILE)

    def rows_of(ws):  # 시트마다 앞쪽 빈 열이 있어 맨 앞의 빈 칸을 지운다
        out = []
        for r in ws.iter_rows(values_only=True):
            r = list(r)
            while r and r[0] is None:
                r.pop(0)
            if r:
                out.append(r)
        return out

    sheets = {}
    for r in rows_of(wb["Summary"]):
        if str(r[0]).startswith(("Sheet ", "Flags ")):
            sheets[r[0]] = (r[4], r[5])  # (age, nace)
    cell, flags = {}, {}
    for name, (age, nace) in sheets.items():
        rows = rows_of(wb[name])
        t = next(r for r in rows if r and r[0] == "TIME")
        g = next(r for r in rows if r and r[0] == EU_GEO)
        for j, y in enumerate(t):
            if j == 0 or y in (None, "") or int(y) not in YEARS:
                continue
            if name.startswith("Sheet"):
                cell[(age, int(y), nace)] = float(g[j])
            else:
                flags[(age, int(y), nace)] = g[j] or ""
    return cell, flags


# ---------- 호주 ----------
AU_FILE = RAW / "australia_abs_EQ12_20261106.xlsx"
AU = {
    "total": "__all__",
    "high_main": ["Information Media and Telecommunications", "Professional, Scientific and Technical Services"],
    "high_sub": ["Information Media and Telecommunications", "Professional, Scientific and Technical Services",
                 "Financial and Insurance Services"],
    "low": ["Accommodation and Food Services"],
    "young": ["15-19 years", "20-24 years"],
    "young_sub": ["15-19 years", "20-24 years", "25-29 years", "30-34 years"],
    "old": ["35-39 years", "40-44 years", "45-49 years", "50-54 years", "55-59 years", "60-64 years"],
}


def load_australia():
    wb = openpyxl.load_workbook(AU_FILE, read_only=True)
    q = {}  # (age, year, industry) -> [분기 값]
    for i, r in enumerate(wb["Data 1"].iter_rows(values_only=True)):
        if i < 4 or r[0] is None or r[0].year not in YEARS:
            continue
        v = (r[3] or 0) + (r[4] or 0)  # 전일제 + 시간제 = 취업자
        for key in ((r[1], r[0].year, r[2]), (r[1], r[0].year, "__all__")):
            q.setdefault(key, {}).setdefault(r[0].month, 0.0)
            q[key][r[0].month] += v
    cell = {}
    for key, months in q.items():
        assert sorted(months) == [2, 5, 8, 11], (key, sorted(months))  # 설계서 9.6: 4개 분기 평균
        cell[key] = sum(months.values()) / 4
    return cell


# ---------- 공통 계산 ----------
def share(cell, spec, inds, ages, year):
    num = sum(cell[(a, year, i)] for a in ages for i in inds)
    den = sum(cell[(a, year, spec["total"])] for a in ages)
    return 100 * num / den


def gap_set(cell, spec, inds, young, post_end):
    s = {}
    for g, ages in (("청년", young), ("중장년", spec["old"])):
        for y in (2019, 2022, post_end):
            s[(g, y)] = share(cell, spec, inds, ages, y)
    pre = (s[("청년", 2022)] - s[("청년", 2019)]) - (s[("중장년", 2022)] - s[("중장년", 2019)])
    post = (s[("청년", post_end)] - s[("청년", 2022)]) - (s[("중장년", post_end)] - s[("중장년", 2022)])
    return s, pre, post


def verdict(gpre, gpost, gpost_low):
    return gpost <= -THRESH, (gpre - gpost) >= THRESH, (gpost_low - gpost) >= THRESH


def main():
    OUT.mkdir(exist_ok=True)
    jp = load_japan()
    eu, eu_flags = load_eu()
    au = load_australia()
    regions = [("일본", jp, JP, "15~24세", "15~34세", "35~64세"),
               ("EU27", eu, EU, "15~24세", "15~39세", "40~64세"),
               ("호주", au, AU, "15~24세", "15~34세", "35~64세")]
    lines = ["추가 분석(탐색적): 설계서 9절. 본 판정(한국·미국)과 별개.", ""]

    used = [k for k in eu_flags if k[1] in (2019, 2022, 2024, 2025) and eu_flags[k]]
    lines.append("[EU 표시(flag)가 붙은 칸 중 판정 시점(2019·2022·2024·2025)]: " +
                 (", ".join(f"{a}/{y}/{n}={eu_flags[(a, y, n)]}" for a, y, n in sorted(used)) if used else "없음"))
    f21 = sorted({eu_flags[k] for k in eu_flags if k[1] == 2021 and eu_flags[k]})
    lines.append(f"[EU 2021년 칸의 표시]: {', '.join(f21) if f21 else '없음'} (b = 시계열 단절)")
    lines.append("")

    for rname, cell, spec, ytag, ysubtag, otag in regions:
        for post_end, tag in ((2024, "주 분석 (2022→2024)"), (2025, "보조 분석 (2022→2025)")):
            for young, yt in ((spec["young"], ytag), (spec["young_sub"], ysubtag)):
                for inds, it in ((spec["high_main"], "고노출 주"), (spec["high_sub"], "고노출 보조(+금융)")):
                    s, gpre, gpost = gap_set(cell, spec, inds, young, post_end)
                    _, _, gpost_low = gap_set(cell, spec, spec["low"], young, post_end)
                    c1, c2, c3 = verdict(gpre, gpost, gpost_low)
                    lines.append(f"=== {rname} / {tag} / 청년 {yt} vs 중장년 {otag} / {it} ===")
                    for g in ("청년", "중장년"):
                        lines.append(f"  {g}: 2019 {s[(g, 2019)]:.2f}% → 2022 {s[(g, 2022)]:.2f}% → {post_end} {s[(g, post_end)]:.2f}%")
                    lines.append(f"  이전 격차 {gpre:+.2f}%p / 이후 격차 {gpost:+.2f}%p / 저노출 이후 격차 {gpost_low:+.2f}%p")
                    lines.append(f"  조건1 {c1} / 조건2 {c2} / 조건3 {c3} → "
                                 f"{'같은 패턴(세 조건 충족)' if (c1 and c2 and c3) else '같은 패턴 아님'}")
                    lines.append("")

    with open(OUT / "intl_share_series.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["지역", "연도", "청년_고노출주(%)", "중장년_고노출주(%)"])
        for rname, cell, spec, *_ in regions:
            for y in YEARS:
                w.writerow([rname, y, round(share(cell, spec, spec["high_main"], spec["young"], y), 2),
                            round(share(cell, spec, spec["high_main"], spec["old"], y), 2)])

    text = "\n".join(lines)
    (OUT / "intl_summary.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
