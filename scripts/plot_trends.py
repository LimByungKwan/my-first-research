"""보조 그래프: 연령대별 AI 고노출 업종(주) 비중의 연도별 흐름 (한국·미국).

판정에는 쓰지 않는다 (DESIGN.md 8절 변경 기록 참고). 흐름을 보여 주는 용도.
입력: results/kr_share_series.csv (analyze_kr.py 출력), data/raw/bls_cpsaat18b_2019~2025.pdf
출력: results/fig_trends.png, results/us_share_series.csv
실행: python3 scripts/analyze_kr.py 다음에 python3 scripts/plot_trends.py
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_us as us  # noqa: E402

BLUE, ORANGE = "#2a78d6", "#eb6834"  # 기본 팔레트 1·2번


def font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    for n in ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK JP"]:
        if n in names:
            plt.rcParams["font.family"] = n
            return


def main():
    font()
    # 한국: 반기 (2019.1/2 ~ 2025.2/2만 사용, 설계 범위 밖인 2026은 제외)
    kr = [r for r in csv.DictReader(open(ROOT / "results/kr_share_series.csv", encoding="utf-8-sig"))
          if "2019" <= r["반기"][:4] <= "2025"]
    kx = [int(r["반기"][:4]) + (0.25 if r["반기"].endswith("1/2") else 0.75) for r in kr]
    ky_y = [float(r["청년_고노출주(%)"]) for r in kr]
    ky_o = [float(r["중장년_고노출주(%)"]) for r in kr]

    # 미국: 연평균 2019~2025
    years = list(range(2019, 2026))
    rows = []
    for y in years:
        d = us.extract(y)
        rows.append((y, us.share(d, us.HIGH_MAIN, us.YOUNG_MAIN), us.share(d, us.HIGH_MAIN, us.OLD)))
    with open(ROOT / "results/us_share_series.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["연도", "청년16~24_고노출주(%)", "중장년35~64_고노출주(%)"])
        for y, a, b in rows:
            w.writerow([y, round(a, 2), round(b, 2)])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    panels = [
        (axes[0], "한국 (지역별고용조사, 반기)", kx, ky_y, ky_o, "청년 15~29세", "중장년 30~59세"),
        (axes[1], "미국 (CPS 연평균)", [r[0] + 0.5 for r in rows], [r[1] for r in rows], [r[2] for r in rows],
         "청년 16~24세", "중장년 35~64세"),
    ]
    for ax, title, x, yy, yo, ly, lo in panels:
        ax.plot(x, yy, color=BLUE, lw=2, marker="o", ms=4, label=ly)
        ax.plot(x, yo, color=ORANGE, lw=2, marker="s", ms=4, label=lo)
        ax.axvline(2022 + 11 / 12, color="#888888", ls="--", lw=1)
        ax.text(2022 + 11 / 12, ax.get_ylim()[1], " ChatGPT 공개\n (2022.11)", va="top", fontsize=8, color="#555555")
        ax.set_title(title, fontsize=11)
        ax.set_xlim(2019, 2026)
        ax.set_xticks(range(2019, 2026))
        ax.set_ylabel("연령대 취업자 중 고노출 업종 비중 (%)", fontsize=9)
        ax.grid(axis="y", color="#e5e5e5", lw=0.8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.legend(frameon=False, fontsize=9, loc="lower right" if "한국" in title else "center right")
    fig.suptitle("AI 고노출 업종(정보통신·전문과학기술 / Information·Professional and technical) 비중의 흐름", fontsize=11)
    fig.text(0.01, 0.01, "판정에는 2019·2022·2024 시점만 사용(사전등록). 미국 2025는 산업분류 변경·11개월 평균. 자료: KOSIS, BLS", fontsize=7.5, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(ROOT / "results/fig_trends.png", dpi=160)
    for y, a, b in rows:
        print(y, f"청년 {a:.2f}%  중장년 {b:.2f}%")


if __name__ == "__main__":
    main()
