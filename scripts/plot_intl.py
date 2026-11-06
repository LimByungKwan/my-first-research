"""추가 분석(탐색적) 그림: 일본·EU27·호주의 연도별 AI 고노출 업종(주) 비중.

입력: results/intl_share_series.csv (analyze_intl.py 출력)
출력: results/fig_intl.png
"""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
BLUE, ORANGE = "#2a78d6", "#eb6834"
OLD_LABEL = {"일본": "중장년 35~64세", "EU27": "중장년 40~64세", "호주": "중장년 35~64세"}


def font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    for n in ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK JP"]:
        if n in names:
            plt.rcParams["font.family"] = n
            return


def main():
    font()
    rows = list(csv.DictReader(open(ROOT / "results/intl_share_series.csv", encoding="utf-8-sig")))
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    for ax, region in zip(axes, ["일본", "EU27", "호주"]):
        r = [x for x in rows if x["지역"] == region]
        yrs = [int(x["연도"]) for x in r]
        ax.plot(yrs, [float(x["청년_고노출주(%)"]) for x in r], "o-", color=BLUE, label="청년 15~24세")
        ax.plot(yrs, [float(x["중장년_고노출주(%)"]) for x in r], "s-", color=ORANGE, label=OLD_LABEL[region])
        ax.axvline(2022.9, color="gray", ls="--", lw=0.8)
        ax.set_title(region, fontsize=11)
        ax.set_xticks(yrs)
        ax.tick_params(labelsize=8)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8, loc="best")
    axes[0].set_ylabel("연령대 취업자 중 고노출 업종 비중 (%)", fontsize=9)
    fig.suptitle("추가 분석(탐색적): AI 고노출 업종(주) 비중의 흐름, 연평균", fontsize=11)
    fig.text(0.5, 0.005, "점선: ChatGPT 공개(2022.11). 자료: 일본 총무성 노동력조사, Eurostat EU-LFS(2021년 시계열 단절), 호주 ABS EQ12(4개 분기 평균)",
             ha="center", fontsize=7.5, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(ROOT / "results/fig_intl.png", dpi=160)


if __name__ == "__main__":
    main()
