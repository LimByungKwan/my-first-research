"""한국 분석: 지역별고용조사 산업/연령별 취업자 → 연령대별 AI 노출 업종 비중과 격차.

설계: DESIGN.md (사전등록 커밋 aad1c5a)
입력: data/raw/kosis_regional_employment_industry_age_20261106.csv (KOSIS에서 받은 그대로, cp949)
출력: results/kr_share_series.csv (반기별 비중 전체), results/kr_summary.txt (판정용 계산)
실행: python3 scripts/analyze_kr.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/kosis_regional_employment_industry_age_20261106.csv"
OUT = ROOT / "results"

# 설계서 3절
HIGH_MAIN = ["정보통신업(58~63)", "전문, 과학 및 기술 서비스업(70~73)"]
HIGH_SUB = HIGH_MAIN + ["금융 및 보험업(64~66)"]
LOW = ["숙박 및 음식점업(55~56)"]
# 설계서 4절
YOUNG = ["연령(15~29세)"]
OLD = ["연령(30~39세)", "연령(40~49세)", "연령(50~59세)"]
# 설계서 2·5절: 매년 하반기
Y2019, Y2022, Y2024, Y2025 = "2019.2/2", "2022.2/2", "2024.2/2", "2025.2/2"
THRESH = 0.5  # 설계서 6절, %포인트


def load():
    rows = list(csv.reader(RAW.read_bytes().decode("cp949").splitlines()))
    periods, labels = rows[0], rows[1]
    col = {}
    for i in range(1, len(labels)):
        col[(periods[i], labels[i])] = i
    data = {r[0]: r for r in rows[2:] if r and r[0]}
    return periods, labels, col, data


def val(data, col, industry, period, label):
    v = data[industry][col[(period, label)]]
    return float(v.replace(",", ""))


def rse_flag(data, labels, col, industry, period, label):
    """나이 열 바로 다음 열이 RSE이면 그 값을 돌려준다('*'는 신뢰도 낮음)."""
    i = col[(period, label)]
    if i + 1 < len(labels) and labels[i + 1] == "RSE":
        return data[industry][i + 1].strip()
    return "(RSE 열 없음)"


def share(data, col, industries, ages, period):
    num = sum(val(data, col, ind, period, a) for ind in industries for a in ages)
    den = sum(val(data, col, "계", period, a) for a in ages)
    return 100 * num / den


def gaps(data, col, industries, post_end):
    s = {}
    for grp, ages in (("청년", YOUNG), ("중장년", OLD)):
        for y in (Y2019, Y2022, post_end):
            s[(grp, y)] = share(data, col, industries, ages, y)
    d_pre = {g: s[(g, Y2022)] - s[(g, Y2019)] for g in ("청년", "중장년")}
    d_post = {g: s[(g, post_end)] - s[(g, Y2022)] for g in ("청년", "중장년")}
    return s, d_pre, d_post, d_pre["청년"] - d_pre["중장년"], d_post["청년"] - d_post["중장년"]


def verdict(gap_pre, gap_post, gap_post_low):
    c1 = gap_post <= -THRESH                      # 이후 격차 < 0 (0.5%p 이상)
    c2 = (gap_pre - gap_post) >= THRESH           # 이후 격차가 이전 격차보다 0.5%p 이상 작음
    c3 = (gap_post_low - gap_post) >= THRESH      # 고노출 이후 격차가 저노출보다 0.5%p 이상 작음
    return c1, c2, c3


def main():
    OUT.mkdir(exist_ok=True)
    periods, labels, col, data = load()
    lines = [f"입력 파일: {RAW.name}", ""]

    # 반기별 전체 비중 (그래프용, 판정에는 하반기 값만 씀)
    plist = sorted({p for p in periods[1:]})
    with open(OUT / "kr_share_series.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["반기", "청년_고노출주(%)", "중장년_고노출주(%)", "청년_고노출보조(%)", "중장년_고노출보조(%)", "청년_저노출(%)", "중장년_저노출(%)"])
        for p in plist:
            w.writerow([p] + [round(share(data, col, inds, ages, p), 2)
                              for inds in (HIGH_MAIN, HIGH_SUB, LOW) for ages in (YOUNG, OLD)])

    # RSE 점검
    lines.append("[RSE 점검: 판정에 쓰는 칸]")
    flagged = []
    for ind in sorted(set(HIGH_SUB + LOW)) + ["계"]:
        for y in (Y2019, Y2022, Y2024, Y2025):
            for a in YOUNG + OLD:
                f = rse_flag(data, labels, col, ind, y, a)
                if f == "*":
                    flagged.append(f"{ind} {y} {a}")
    lines.append("  '*' 표시 칸: " + (", ".join(flagged) if flagged else "없음"))
    lines.append("")

    for post_end, tag in ((Y2024, "주 분석 (2022→2024)"), (Y2025, "보조 분석 (2022→2025)")):
        for inds, itag in ((HIGH_MAIN, "고노출 주(J+M)"), (HIGH_SUB, "고노출 보조(J+M+K)")):
            s, dpre, dpost, gpre, gpost = gaps(data, col, inds, post_end)
            _, _, _, _, gpost_low = gaps(data, col, LOW, post_end)
            c1, c2, c3 = verdict(gpre, gpost, gpost_low)
            lines.append(f"=== {tag} / {itag} ===")
            for g in ("청년", "중장년"):
                lines.append(f"  {g}: 비중 2019 {s[(g, Y2019)]:.2f}% → 2022 {s[(g, Y2022)]:.2f}% → {post_end[:4]} {s[(g, post_end)]:.2f}%"
                             f"  (이전 변화 {dpre[g]:+.2f}%p, 이후 변화 {dpost[g]:+.2f}%p)")
            lines.append(f"  이전 격차(청년−중장년) {gpre:+.2f}%p / 이후 격차 {gpost:+.2f}%p / 저노출(I) 이후 격차 {gpost_low:+.2f}%p")
            lines.append(f"  조건1 이후 격차<0: {c1} / 조건2 이후<이전: {c2} / 조건3 고노출<저노출: {c3}"
                         f"  → {'한국 지지' if (c1 and c2 and c3) else '한국 지지 아님'}")
            y19, ypost = s[("청년", Y2019)], s[("청년", post_end)]
            lines.append(f"  추가 확인: 청년 비중 {post_end[:4]} {ypost:.2f}% vs 2019 {y19:.2f}% (차이 {ypost - y19:+.2f}%p)")
            lines.append("")

    text = "\n".join(lines)
    (OUT / "kr_summary.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
