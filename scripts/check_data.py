"""원자료 점검: 설계서에 적은 자료가 원자료 파일에 빠짐없이 있는지 확인한다 (C26).

실행: python3 scripts/check_data.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_kr as k  # noqa: E402
import analyze_us as u  # noqa: E402


def main():
    periods, labels, col, data = k.load()
    halves = sorted({p for p in periods[1:] if "2019" <= p[:4] <= "2025"})
    industries = ["계"] + sorted(set(k.HIGH_SUB + k.LOW))
    ages = k.YOUNG + k.OLD
    need = [(i, p, a) for i in industries for p in halves for a in ages]
    missing = [x for x in need if (x[1], x[2]) not in col or data[x[0]][col[(x[1], x[2])]].strip() in ("", "-")]
    print(f"한국: 반기 {len(halves)}개({halves[0]}~{halves[-1]}) × 업종 {len(industries)}개 × 연령 {len(ages)}개 = 필요한 칸 {len(need)}개, 빠진 칸 {len(missing)}개")

    years = list(range(2019, 2026))
    ok = True
    for y in years:
        d = u.extract(y)
        good = set(d) == {"Total"} | set(u.HIGH_SUB + u.LOW) and all(len(v) == 8 for v in d.values())
        ok &= good
        print(f"미국 {y}: 필요한 행 5개 중 {len(d)}개 추출, 연령 칸 8개씩 {'OK' if good else '확인 필요'}")
    print("결과:", "설계서의 자료가 모두 있음" if (not missing and ok) else "빠진 자료 있음")


if __name__ == "__main__":
    main()
