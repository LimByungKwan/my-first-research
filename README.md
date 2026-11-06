# 생성형 AI 확산 이후 AI 노출 업종의 청년 고용 비중 변화: 한국과 미국의 공개 통계 비교 — 재현 패키지

저자: 임병관 (Aleph) · 2026년 11월 6일

이 폴더 하나로 논문 3장의 표와 그림 1을 다시 만들 수 있습니다. 원자료는 내려받은 그대로 들어 있어 인터넷 연결 없이 실행됩니다.

## 1. 폴더 구성

| 경로 | 내용 |
|---|---|
| `paper/paper.md` | 논문 본문 (표지, 초록, 1~5장, 참고문헌, 부록 A) |
| `DESIGN.md` | 분석 전에 정해 커밋한 설계서 (가설, 지표, 판정 기준, 변경 기록) |
| `data/raw/` | 원자료. 내려받은 그대로이며 손대지 않음 |
| `data/us_extracted.csv` | 미국 PDF에서 뽑은 행 (`analyze_us.py`가 만듦) |
| `scripts/` | 분석 코드 6개 (본 분석 4개 + 추가 분석 2개) |
| `results/` | 코드 실행 결과 (요약, 비중 시계열, 그림) |
| `requirements.txt` | 필요한 파이썬 패키지와 버전 |

## 2. 원자료

| 파일 | 출처 | 내려받은 날 |
|---|---|---|
| `kosis_regional_employment_industry_age_20261106.csv` | 국가데이터처 KOSIS, 지역별고용조사 「전국 산업/연령/교육정도/종사상지위별 취업자」. 반기, 2019.1/2~2026.1/2, 산업(대분류)×연령, 추정치와 상대표준오차. 인코딩 cp949 | 2026-11-06 |
| `japan_estat_lfs_table2-2-1_20261106.csv` | (추가 분석) 일본 총무성 노동력조사 기본집계 표 2-2-1 「年齢階級，産業別就業者数」, e-Stat 통계표 ID 0003007108, 연평균, 만 명, 인코딩 cp932 | 2026-11-06 |
| `eu_eurostat_lfsa_egan2_20261106.xlsx` | (추가 분석) Eurostat `lfsa_egan2`, EU27(2020년부터), 성별 Total, 연령 15~24·15~39·40~64세, NACE Total·I·J·K·M, 2019~2025 | 2026-11-06 |
| `australia_abs_EQ12_20261106.xlsx` | (추가 분석) ABS Labour Force, Australia, Detailed EQ12 (연령 × 산업 대분류), 분기별, 천 명 | 2026-11-06 |
| `bls_cpsaat18b_2019.pdf` ~ `bls_cpsaat18b_2025.pdf` | U.S. Bureau of Labor Statistics, CPS 연평균 Table 18b (Employed persons by detailed industry and age). `https://www.bls.gov/cps/data/aa{연도}/cpsaat18b.pdf` | 2026-11-06 |

주의할 점:
- KOSIS 표의 `*`는 상대표준오차 25% 이상인 칸입니다. 판정에 쓰는 칸 중 해당 칸은 없습니다 (`results/kr_summary.txt` 맨 위 참고).
- KOSIS 표는 제11차 한국표준산업분류를 2013년 상반기부터 소급 반영해, 2019~2025년이 같은 분류 기준입니다.
- 2026.1/2 값은 받은 파일에 들어 있지만 설계 범위 밖이라 분석에서 뺐습니다.
- BLS 2025년 표는 2022년 Census 산업분류를 쓰는 새 기준이고 11개월 평균입니다. 그래서 2025년은 보조 분석으로만 씁니다.

## 3. 실행 방법

Python 3.13에서 실행해 확인했습니다.

```bash
pip install -r requirements.txt

python scripts/analyze_kr.py    # 한국: results/kr_summary.txt, results/kr_share_series.csv
python scripts/analyze_us.py    # 미국: results/us_summary.txt, data/us_extracted.csv
python scripts/plot_trends.py   # 그림 1: results/fig_trends.png, results/us_share_series.csv
python scripts/check_data.py    # 자료 점검: 빠진 칸이 없는지 확인 (추가 분석 자료 포함)
python scripts/analyze_intl.py  # 추가 분석(탐색적): results/intl_summary.txt, results/intl_share_series.csv
python scripts/plot_intl.py     # 그림 2: results/fig_intl.png
```

순서대로 실행하세요. `plot_trends.py`는 `analyze_kr.py`가 만든 `kr_share_series.csv`를 읽습니다. 그림의 한글은 맑은 고딕, AppleGothic, 나눔고딕, Noto Sans CJK 중 설치된 글꼴을 씁니다. 하나도 없으면 한글이 네모로 보일 수 있지만 숫자에는 영향이 없습니다.

## 4. 결과와 논문의 대응

| 논문 | 파일 |
|---|---|
| 표 1~2 (한국 비중과 격차) | `results/kr_summary.txt` |
| 표 3~4 (미국 비중과 격차) | `results/us_summary.txt` |
| 표 5 (최종 판정) | 두 요약 파일의 "→ 지지 / 지지 아님" 줄 |
| 그림 1 (연도별 흐름) | `results/fig_trends.png` (자료: `kr_share_series.csv`, `us_share_series.csv`) |
| 2.9 계산 확인 | `scripts/check_data.py` 출력 |
| 표 6~7 (추가 분석: 일본·EU·호주) | `results/intl_summary.txt` |
| 그림 2 (추가 분석 흐름) | `results/fig_intl.png` (자료: `intl_share_series.csv`) |

핵심 숫자 (주 분석, 2022→2024년, 고노출 업종 = 정보통신업 + 전문·과학·기술서비스업):

| | 이전 격차 (2019→2022) | 이후 격차 (2022→2024) | 판정 |
|---|---|---|---|
| 한국 (15~29세 vs 30~59세) | +0.65%p | −0.18%p | 지지 아님 |
| 미국 (16~24세 vs 35~64세) | −1.08%p | +0.21%p | 지지 아님 |

격차 = 청년층 비중 변화 − 중장년층 비중 변화. 사전 기준(이후 격차 −0.5%p 이하 등 세 조건)에 따라 가설은 기각되었습니다.

추가 분석(탐색적, 설계서 9절)에서 일본·EU27·호주의 주 분석 이후 격차는 −0.20%p, −0.48%p, −0.06%p로 세 지역 모두 "같은 패턴 아님"이었습니다. 2025년 보조 분석에서는 EU만 조건을 충족했습니다(−0.98%p). 이 결과는 본 판정을 바꾸지 않습니다.

## 5. 사전 등록과 변경 기록

설계서는 분석 전에 GitHub(`LimByungKwan/my-first-research`)에 커밋했습니다. 추가 분석 설계(9절)도 각 지역 자료를 받기 전에 커밋했습니다(6400add, ceeea9e). 그 뒤에 바뀐 점과 이유는 `DESIGN.md` 8장 변경 기록에 남겼습니다. 판정 기준과 판정 결과는 바꾸지 않았습니다.

## 6. AI 활용

분석 코드는 Claude(Anthropic)가 작성했고, 연구자가 2024년 한국 값을 손으로 다시 계산해 대조했습니다. 누가 무엇을 했는지는 논문 부록 A에 정리했습니다.
