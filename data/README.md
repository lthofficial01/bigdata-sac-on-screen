# Data

이 저장소에는 HDFS/Spark/Hive sample smoke test용 CSV만 포함합니다.

```text
data/
├── README.md
└── sample/
    ├── sac_performances_sample.csv
    ├── sac_booking_age_sample.csv
    └── population_age_sample.csv
```

Full raw 데이터는 GitHub에 포함하지 않습니다. 전체 파이프라인을 실행하려면 Ambari Files View 또는 HDFS CLI로 아래 HDFS 경로에 원본 CSV 3개를 업로드합니다.

```text
/user/maria_dev/sac_on_screen/raw/
├── sac_performances.csv
├── sac_booking_age.csv
└── population_age.csv
```

## Minimal Schema

```text
sac_performances.csv
- TITLE: 공연명
- GENRE: 공연 장르

sac_booking_age.csv
- TITLE: 공연명
- RELATION: 연령대별 예매 건수 문자열

population_age.csv
- 행정구역: 지역명과 행정구역 코드
- 2026년04월_계_0~9세 ... 2026년04월_계_100세 이상: 연령대별 인구
```

## References

- 예술의전당 종합 공연정보: https://www.culture.go.kr/data/filedat/filedatDtl.do?fileDataNo=00000000000000000428&category=A&keyword=%EC%98%88%EC%88%A0%EC%9D%98%EC%A0%84%EB%8B%B9&category=A&dataType=BATCH
- 예술의전당 연령대별 예매 건수: https://www.culture.go.kr/data/filedat/filedatDtl.do?fileDataNo=00000000000000000411&category=A&keyword=%EC%98%88%EC%88%A0%EC%9D%98%EC%A0%84%EB%8B%B9&category=A&dataType=BATCH
- 지역별 주민등록 인구통계 중 행정동별 연령별 인구현황: https://jumin.mois.go.kr/

확인 명령:

```bash
hdfs dfs -ls -h /user/maria_dev/sac_on_screen/raw
```

이후 프로젝트 루트에서 전체 파이프라인을 실행합니다.

```bash
bash scripts/run_pipeline.sh
```
