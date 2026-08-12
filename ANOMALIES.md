# Data Anomalies Report
**Source:** `Data\In\data_pack_new\review.csv`
**Generated:** 2026-08-12 20:34:03
**Total rows:** 207

## Missing Values
- **id**: 2 missing (1.0%)
- **name**: 2 missing (1.0%)
- **category**: 2 missing (1.0%)
- **city**: 2 missing (1.0%)
- **address**: 3 missing (1.4%)
- **rating**: 21 missing (10.1%)
- **reviews_count**: 3 missing (1.4%)
- **site**: 60 missing (29.0%)
- **phone**: 22 missing (10.6%)

## Rating Out of Range (0–5)
Found 2 rows with rating outside 0–5.
- id: c_001122, name: ООО «Восток Лаб», rating: -3.0
- id: c_001186, name: ООО «Опора Медиа», rating: 7.2

## Negative Reviews Count
Found 1 rows with negative reviews_count.
- id: c_001116, name: ИП Богданов Б. П., reviews_count: -10.0

## Duplicate IDs
Found 4 duplicate ID entries.
- id: c_001049, name: «Ритм Сервис»
- id: c_001049, name: «Ритм Сервис»
- id: c_001050, name: ООО «Кварц Тех»
- id: c_001050, name: ООО «Кварц Тех»
- id: c_001075, name: ООО «Восток Групп»
- id: c_001075, name: ООО «Восток Групп»
- id: nan, name: nan
- id: nan, name: nan

## Missing Critical Fields (id or name)
Found 2 rows missing either 'id' or 'name'.
- id: nan, name: nan
- id: nan, name: nan

## NULL IDs Dropped
Before loading, 1 rows with NULL 'id' were removed.
