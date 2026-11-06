"""미국 분석: BLS CPS 연평균 표 18b → 연령대별 AI 노출 업종 비중과 격차.

설계: DESIGN.md (사전등록 커밋 aad1c5a)
입력: data/raw/bls_cpsaat18b_{2019,2022,2024,2025}.pdf (BLS에서 받은 그대로)
출력: data/us_extracted.csv (PDF에서 뽑은 행), results/us_summary.txt
실행: python3 scripts/analyze_us.py   (pypdf 필요: pip install pypdf)
"""
import csv
import re
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
OUT = ROOT / "results"
YEARS = [2019, 2022, 2024, 2025]
COLS = ["total", "16-19", "20-24", "25-34", "35-44", "45-54", "55-64", "65+"]

TOTAL_LABELS = ["Total, 16 years and over", "Total employed"]
HIGH_MAIN = ["Information", "Professional and technical services"]
HIGH_SUB = HIGH_MAIN + ["Finance and insurance"]
LOW = ["Accommodation and food services"]

YOUNG_MAIN = ["16-19", "20-24"]
YOUNG_SUB = ["16-19", "20-24", "25-34"]
OLD = ["35-44", "45-54", "55-64"]
THRESH = 0.5


def extract(year):
    text = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(RAW / f"bls_cpsaat18b_{year}.pdf").pages)
    rows = {}
    for line in text.split("\n"):
        s = line.strip()
        for label in TOTAL_LABELS + HIGH_SUB + LOW:
            if s.startswith(label) and label not in rows:
                nums = re.findall(r"\d[\d,]*", s[len(label):])
                if len(nums) >= 8:
                    key = "Total" if label in TOTAL_LABELS else label
                    if key not in rows:
                        rows[key] = [int(n.replace(",", "")) for n in nums[:8]]
    return rows


def share(d, industries, ages):
    idx = [COLS.index(a) for a in ages]
    num = sum(d[ind][i] for ind in industries for i in idx)
    den = sum(d["Total"][i] for i in idx)
    return 100 * num / den


def main():
    OUT.mkdir(exist_ok=True)
    data = {y: extract(y) for y in YEARS}
    with open(ROOT / "data/us_extracted.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["year", "industry"] + COLS)
        for y in YEARS:
            for k, v in data[y].items():
                w.writerow([y, k] + v)

    lines = ["PDF에서 뽑은 행 수: " + ", ".join(f"{y}: {len(data[y])}" for y in YEARS), ""]
    for post, tag in ((2024, "주 분석 (2022→2024)"), (2025, "보조 분석 (2022→2025, 산업분류 변경·11개월 평균)")):
        for young, ytag in ((YOUNG_MAIN, "청년 16~24세"), (YOUNG_SUB, "청년 16~34세(보조)")):
            for inds, itag in ((HIGH_MAIN, "고노출 주(Information + Prof./tech.)"), (HIGH_SUB, "고노출 보조(+Finance/insurance)")):
                s = {(g, y): share(data[y], inds, ages) for g, ages in (("청년", young), ("중장년", OLD)) for y in (2019, 2022, post)}
                low = {(g, y): share(data[y], LOW, ages) for g, ages in (("청년", young), ("중장년", OLD)) for y in (2022, post)}
                dpre = {g: s[(g, 2022)] - s[(g, 2019)] for g in ("청년", "중장년")}
                dpost = {g: s[(g, post)] - s[(g, 2022)] for g in ("청년", "중장년")}
                gpre, gpost = dpre["청년"] - dpre["중장년"], dpost["청년"] - dpost["중장년"]
                gpost_low = (low[("청년", post)] - low[("청년", 2022)]) - (low[("중장년", post)] - low[("중장년", 2022)])
                c1 = gpost <= -THRESH
                c2 = (gpre - gpost) >= THRESH
                c3 = (gpost_low - gpost) >= THRESH
                lines.append(f"=== {tag} / {ytag} / {itag} ===")
                for g in ("청년", "중장년"):
                    lines.append(f"  {g}: 2019 {s[(g, 2019)]:.2f}% → 2022 {s[(g, 2022)]:.2f}% → {post} {s[(g, post)]:.2f}%"
                                 f"  (이전 {dpre[g]:+.2f}%p, 이후 {dpost[g]:+.2f}%p)")
                lines.append(f"  이전 격차 {gpre:+.2f}%p / 이후 격차 {gpost:+.2f}%p / 저노출 이후 격차 {gpost_low:+.2f}%p")
                lines.append(f"  조건1 {c1} / 조건2 {c2} / 조건3 {c3} → {'미국 지지' if (c1 and c2 and c3) else '미국 지지 아님'}")
                lines.append(f"  추가 확인: 청년 비중 {post} {s[('청년', post)]:.2f}% vs 2019 {s[('청년', 2019)]:.2f}% (차이 {s[('청년', post)] - s[('청년', 2019)]:+.2f}%p)")
                lines.append("")
    text = "\n".join(lines)
    (OUT / "us_summary.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
