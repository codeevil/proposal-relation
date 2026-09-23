# RELATIONAL实验数据(AgentRank)

## TPCDS

### query013_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 937.72 | 1.00x |  | ok |  |
| 1 | proposal_1 | 1875.27 | 0.50x | Yes | hint_error | Rows(date_dim *0.5) \| Rows hint requires at least two rel... |
| 2 | proposal_2 | 6384.98 | 0.15x |  | ok |  |
| 3 | proposal_3 | 953.60 | 0.98x |  | hint_error | Rows(store_sales *0.3) \| Rows hint requires at least two ... |
| 4 | proposal_4 | 2284.60 | 0.41x |  | ok |  |
| 5 | proposal_5 | 8966.70 | 0.10x |  | ok |  |
| 6 | proposal_6 | 1477.94 | 0.63x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 7 | proposal_7 | 2281.73 | 0.41x |  | hint_error | Rows(household_demographics *3.0) \| Rows hint requires at... |
| 8 | proposal_8 | 2395.93 | 0.39x |  | ok |  |
| 9 | proposal_9 | 2319.52 | 0.40x |  | ok |  |
| 10 | proposal_10 | 959.99 | 0.98x |  | ok |  |
| 11 | proposal_11 | 1628.28 | 0.58x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 12 | proposal_12 | 2318.98 | 0.40x |  | hint_error | Rows(customer_demographics *0.1) \| Rows hint requires at ... |
| 13 | proposal_13 | 955.04 | 0.98x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 14 | proposal_14 | 636.45 | 1.47x |  | ok |  |
| 15 | proposal_15 | 973.87 | 0.96x |  | ok |  |
| 16 | proposal_16 | 11031.99 | 0.08x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 17 | proposal_17 | 2367.11 | 0.40x |  | ok |  |
| 18 | proposal_18 | 965.67 | 0.97x |  | hint_error | Rows(store_sales *0.5) \| Rows hint requires at least two ... |
| 19 | proposal_19 | 1947.91 | 0.48x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 20 | proposal_20 | 967.85 | 0.97x |  | ok |  |


### query018_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 646.10 | 1.00x |  | ok |  |
| 1 | proposal_1 | 2302.84 | 0.28x |  | ok |  |
| 2 | proposal_2 | 2799.56 | 0.23x |  | ok |  |
| 3 | proposal_3 | 3742.21 | 0.17x |  | hint_error | NoNestLoop(*) \| NoNestLoop hint requires at least two rel... |
| 4 | proposal_4 | 16585.57 | 0.04x |  | hint_error | Rows(catalog_sales *0.15) Rows(customer *0.2) \| Rows hint... |
| 5 | proposal_5 | 1219.08 | 0.53x |  | ok |  |
| 6 | proposal_6 | 599.82 | 1.08x |  | hint_error | NoNestLoop(*) \| NoNestLoop hint requires at least two rel... |
| 7 | proposal_7 | 610.93 | 1.06x |  | hint_error | NoNestLoop(*) Set(work_mem '128MB') \| NoNestLoop hint req... |
| 8 | proposal_8 | 1008.88 | 0.64x |  | hint_error | Parallel(catalog_sales 12 soft) \| number of workers = 12 ... |
| 9 | proposal_9 | 604.25 | 1.07x |  | hint_error | NoNestLoop(*) Parallel(catalog_sales 10 soft) \| number of... |
| 10 | proposal_10 | 724.49 | 0.89x | Yes | ok |  |
| 11 | proposal_11 | 623.67 | 1.04x |  | hint_error | Rows(catalog_sales *0.12) Rows(customer *0.25) \| Rows hin... |
| 12 | proposal_12 | 782.21 | 0.83x |  | hint_error | NoHashJoin(*) \| NoHashJoin hint requires at least two rel... |
| 13 | proposal_13 | 547.13 | 1.18x |  | hint_error | NoNestLoop(*) Parallel(catalog_sales 12 soft) \| number of... |
| 14 | proposal_14 | 1109.69 | 0.58x |  | ok |  |
| 15 | proposal_15 | 951.64 | 0.68x |  | ok |  |
| 16 | proposal_16 | 773.72 | 0.84x |  | ok |  |
| 17 | proposal_17 | 522.40 | 1.24x |  | hint_error | Rows(catalog_sales *0.1) Rows(customer *0.2) Parallel(cat... |
| 18 | proposal_18 | 1015.99 | 0.64x |  | ok |  |
| 19 | proposal_19 | 751.92 | 0.86x |  | ok |  |
| 20 | proposal_20 | 533.39 | 1.21x |  | hint_error | NoNestLoop(*) Parallel(catalog_sales 12 soft) \| number of... |


### query019_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 271.55 | 1.00x |  | ok |  |
| 1 | proposal_1 | 213.49 | 1.27x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 2 | proposal_2 | 333.21 | 0.81x |  | ok |  |
| 3 | proposal_3 | 21176.80 | 0.01x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 4 | proposal_4 | 339.81 | 0.80x |  | ok |  |
| 5 | proposal_5 | 3521.18 | 0.08x |  | ok |  |
| 6 | proposal_6 | 278.45 | 0.98x |  | ok |  |
| 7 | proposal_7 | 273.90 | 0.99x |  | ok |  |
| 8 | proposal_8 | 273.69 | 0.99x |  | ok |  |
| 9 | proposal_9 | 319.69 | 0.85x |  | ok |  |
| 10 | proposal_10 | 267.39 | 1.02x |  | hint_error | Leading(((date_dim store_sales) (customer customer_addres... |
| 11 | proposal_11 | 2950.99 | 0.09x |  | ok |  |
| 12 | proposal_12 | 271.46 | 1.00x | Yes | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 13 | proposal_13 | 341.89 | 0.79x |  | ok |  |
| 14 | proposal_14 | 204.51 | 1.33x |  | ok |  |
| 15 | proposal_15 | 333.63 | 0.81x |  | ok |  |
| 16 | proposal_16 | 3863.19 | 0.07x |  | ok |  |
| 17 | proposal_17 | 269.43 | 1.01x |  | ok |  |
| 18 | proposal_18 | 266.17 | 1.02x |  | ok |  |
| 19 | proposal_19 | 273.64 | 0.99x |  | hint_error | Leading(((date_dim store_sales) (customer customer_addres... |
| 20 | proposal_20 | 2806.26 | 0.10x |  | ok |  |


### query025_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1624.32 | 1.00x |  | ok |  |
| 1 | proposal_1 | 46493.74 | 0.03x | Yes | ok |  |
| 2 | proposal_2 | 37210.37 | 0.04x |  | hint_error | Rows(d1 *0.1) \| Rows hint requires at least two relations... |
| 3 | proposal_3 | 6021.80 | 0.27x |  | ok |  |
| 4 | proposal_4 | 6280.39 | 0.26x |  | ok |  |
| 5 | proposal_5 | 6194.96 | 0.26x |  | ok |  |
| 6 | proposal_6 | 45643.20 | 0.04x |  | ok |  |
| 7 | proposal_7 | 6161.12 | 0.26x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 8 | proposal_8 | 6299.11 | 0.26x |  | ok |  |
| 9 | proposal_9 | 5677.30 | 0.29x |  | ok |  |
| 10 | proposal_10 | 36809.93 | 0.04x |  | ok |  |
| 11 | proposal_11 | 6148.42 | 0.26x |  | hint_error | Rows(d2 *1.0) Rows(d3 *1.0) \| Rows hint requires at least... |
| 12 | proposal_12 | 5308.54 | 0.31x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 13 | proposal_13 | 48102.04 | 0.03x |  | ok |  |
| 14 | proposal_14 | 45380.74 | 0.04x |  | ok |  |
| 15 | proposal_15 | 5983.04 | 0.27x |  | ok |  |
| 16 | proposal_16 | 5185.78 | 0.31x |  | ok |  |
| 17 | proposal_17 | 6391.81 | 0.25x |  | ok |  |
| 18 | proposal_18 | 6197.18 | 0.26x |  | ok |  |
| 19 | proposal_19 | 5939.93 | 0.27x |  | ok |  |
| 20 | proposal_20 | 37628.39 | 0.04x |  | ok |  |


### query027_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1029.27 | 1.00x |  | ok |  |
| 1 | proposal_1 | 29137.64 | 0.04x |  | ok |  |
| 2 | proposal_2 | 1672.19 | 0.62x |  | hint_error | Rows(store_sales *0.8) \| Rows hint requires at least two ... |
| 3 | proposal_3 | 1003.26 | 1.03x |  | hint_error | Leading(((customer_demographics item) store_sales store))... |
| 4 | proposal_4 | 1284.64 | 0.80x |  | hint_error | Rows(store_sales *0.9) \| Rows hint requires at least two ... |
| 5 | proposal_5 | 2082.43 | 0.49x |  | ok |  |
| 6 | proposal_6 | 796.88 | 1.29x |  | ok |  |
| 7 | proposal_7 | 2130.16 | 0.48x |  | ok |  |
| 8 | proposal_8 | 1004.72 | 1.02x |  | hint_error | Rows(customer_demographics *0.5) \| Rows hint requires at ... |
| 9 | proposal_9 | 977.34 | 1.05x |  | hint_error | Rows(store *0.3) \| Rows hint requires at least two relati... |
| 10 | proposal_10 | 995.88 | 1.03x |  | ok |  |
| 11 | proposal_11 | 1620.47 | 0.64x |  | hint_error | Rows(item *0.7) \| Rows hint requires at least two relatio... |
| 12 | proposal_12 | 975.83 | 1.05x |  | ok |  |
| 13 | proposal_13 | 949.71 | 1.08x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 14 | proposal_14 | 1920.47 | 0.54x |  | ok |  |
| 15 | proposal_15 | 967.00 | 1.06x |  | ok |  |
| 16 | proposal_16 | 1285.75 | 0.80x |  | hint_error | Rows(store_sales *0.8) \| Rows hint requires at least two ... |
| 17 | proposal_17 | 3324.08 | 0.31x |  | ok |  |
| 18 | proposal_18 | 1356.59 | 0.76x |  | ok |  |
| 19 | proposal_19 | 959.39 | 1.07x |  | ok |  |
| 20 | proposal_20 | 9236.72 | 0.11x | Yes | ok |  |


### query050_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 354.68 | 1.00x |  | ok |  |
| 1 | proposal_1 | 6920.94 | 0.05x |  | hint_error | Rows(store_returns *0.05) \| Rows hint requires at least t... |
| 2 | proposal_2 | 6796.17 | 0.05x |  | ok |  |
| 3 | proposal_3 | 9948.47 | 0.04x |  | ok |  |
| 4 | proposal_4 | 7854.42 | 0.05x |  | ok |  |
| 5 | proposal_5 | 7840.01 | 0.05x |  | ok |  |
| 6 | proposal_6 | 7907.39 | 0.04x |  | ok |  |
| 7 | proposal_7 | 976.32 | 0.36x |  | ok |  |
| 8 | proposal_8 | 21434.97 | 0.02x |  | ok |  |
| 9 | proposal_9 | 6475.81 | 0.05x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 10 | proposal_10 | 11667.33 | 0.03x |  | ok |  |
| 11 | proposal_11 | 1123.93 | 0.32x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 12 | proposal_12 | 6594.45 | 0.05x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 13 | proposal_13 | 19025.78 | 0.02x |  | ok |  |
| 14 | proposal_14 | 7933.22 | 0.04x |  | ok |  |
| 15 | proposal_15 | 6981.68 | 0.05x |  | ok |  |
| 16 | proposal_16 | 9515.74 | 0.04x |  | ok |  |
| 17 | proposal_17 | 20197.16 | 0.02x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 18 | proposal_18 | 6615.38 | 0.05x |  | ok |  |
| 19 | proposal_19 | 7239.92 | 0.05x |  | ok |  |
| 20 | proposal_20 | 11374.33 | 0.03x | Yes | ok |  |


### query072_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 533.40 | 1.00x |  | ok |  |
| 1 | proposal_1 | 1068.01 | 0.50x |  | hint_error | Rows(d1 *0.1) Rows(catalog_sales *0.16) \| Rows hint requi... |
| 2 | proposal_2 | 602.10 | 0.89x |  | ok |  |
| 3 | proposal_3 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 4 | proposal_4 | 522.74 | 1.02x |  | ok |  |
| 5 | proposal_5 | 527.45 | 1.01x |  | ok |  |
| 6 | proposal_6 | 1764.93 | 0.30x |  | ok |  |
| 7 | proposal_7 | 525.33 | 1.02x |  | ok |  |
| 8 | proposal_8 | 3387.64 | 0.16x |  | ok |  |
| 9 | proposal_9 | 531.39 | 1.00x |  | ok |  |
| 10 | proposal_10 | 543.57 | 0.98x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 11 | proposal_11 | 829.75 | 0.64x |  | hint_error | Rows(d1 *0.1) \| Rows hint requires at least two relations... |
| 12 | proposal_12 | 534.86 | 1.00x |  | ok |  |
| 13 | proposal_13 | 534.76 | 1.00x |  | ok |  |
| 14 | proposal_14 | 13954.80 | 0.04x |  | ok |  |
| 15 | proposal_15 | 525.42 | 1.02x |  | ok |  |
| 16 | proposal_16 | 526.65 | 1.01x |  | ok |  |
| 17 | proposal_17 | 1309.07 | 0.41x |  | ok |  |
| 18 | proposal_18 | 542.16 | 0.98x |  | hint_error | Leading(((warehouse inventory d2) (d1 (catalog_sales (ite... |
| 19 | proposal_19 | 548.02 | 0.97x |  | ok |  |
| 20 | proposal_20 | 780.00 | 0.68x | Yes | hint_error | Set(work_mem '512MB') Rows(catalog_sales *0.16) Rows(d1 *... |


### query085_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 380.94 | 1.00x |  | ok |  |
| 1 | proposal_1 | 476.85 | 0.80x |  | hint_error | Leading((web_returns (customer_address customer_demograph... |
| 2 | proposal_2 | 349.26 | 1.09x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 3 | proposal_3 | 353.16 | 1.08x |  | hint_error | Leading((date_dim web_sales web_returns (customer_address... |
| 4 | proposal_4 | 460.68 | 0.83x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 5 | proposal_5 | 336.09 | 1.13x |  | ok |  |
| 6 | proposal_6 | 3679.40 | 0.10x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 7 | proposal_7 | 356.82 | 1.07x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 8 | proposal_8 | 348.87 | 1.09x |  | ok |  |
| 9 | proposal_9 | 1065.50 | 0.36x |  | ok |  |
| 10 | proposal_10 | 350.47 | 1.09x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 11 | proposal_11 | 359.91 | 1.06x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 12 | proposal_12 | 356.92 | 1.07x |  | ok |  |
| 13 | proposal_13 | 511.05 | 0.75x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 14 | proposal_14 | 355.12 | 1.07x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 15 | proposal_15 | 351.17 | 1.08x |  | ok |  |
| 16 | proposal_16 | 3952.45 | 0.10x |  | ok |  |
| 17 | proposal_17 | 333.66 | 1.14x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 18 | proposal_18 | 459.87 | 0.83x |  | ok |  |
| 19 | proposal_19 | 352.93 | 1.08x |  | hint_error | Rows(web_returns customer_address 21000) \| Unrecognized r... |
| 20 | proposal_20 | 444.72 | 0.86x | Yes | hint_error | Leading((date_dim web_sales web_returns (customer_address... |


### query099_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 91.36 | 1.00x |  | ok |  |
| 1 | proposal_1 | 2873.38 | 0.03x |  | hint_error | Rows(date_dim *0.075) \| Rows hint requires at least two r... |
| 2 | proposal_2 | 2513.46 | 0.04x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 3 | proposal_3 | 94.70 | 0.96x |  | hint_error | Leading((date_dim ((call_center warehouse) ship_mode) cat... |
| 4 | proposal_4 | 2976.67 | 0.03x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 5 | proposal_5 | 94.36 | 0.97x |  | hint_error | Rows(warehouse *0.5) \| Rows hint requires at least two re... |
| 6 | proposal_6 | 86.87 | 1.05x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 7 | proposal_7 | 694.02 | 0.13x |  | ok |  |
| 8 | proposal_8 | 87.21 | 1.05x |  | ok |  |
| 9 | proposal_9 | 90.75 | 1.01x | Yes | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 10 | proposal_10 | 94.29 | 0.97x |  | hint_error | Leading((date_dim (call_center warehouse ship_mode) catal... |
| 11 | proposal_11 | 118.81 | 0.77x |  | hint_error | NoNestLoop(*) \| NoNestLoop hint requires at least two rel... |
| 12 | proposal_12 | 2870.79 | 0.03x |  | ok |  |
| 13 | proposal_13 | 92.43 | 0.99x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 14 | proposal_14 | 2863.59 | 0.03x |  | ok |  |
| 15 | proposal_15 | 94.35 | 0.97x |  | hint_error | NoNestLoop(*) HashJoin(*) NoMemoize(*) \| NoNestLoop hint ... |
| 16 | proposal_16 | 98.85 | 0.92x |  | ok |  |
| 17 | proposal_17 | 89.07 | 1.03x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 18 | proposal_18 | 689.71 | 0.13x |  | ok |  |
| 19 | proposal_19 | 112.06 | 0.82x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 20 | proposal_20 | 2965.04 | 0.03x |  | hint_error | Rows(date_dim *0.075) \| Rows hint requires at least two r... |


### query100_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 158.61 | 1.00x |  | ok |  |
| 1 | proposal_1 | 3074.45 | 0.05x |  | ok |  |
| 2 | proposal_2 | 146.95 | 1.08x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 3 | proposal_3 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 4 | proposal_4 | 153.32 | 1.03x |  | ok |  |
| 5 | proposal_5 | 158.28 | 1.00x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 6 | proposal_6 | 152.48 | 1.04x |  | ok |  |
| 7 | proposal_7 | 161.09 | 0.98x |  | hint_error | Parallel(store_sales 12 soft) \| number of workers = 12 is... |
| 8 | proposal_8 | 160.13 | 0.99x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 9 | proposal_9 | 2406.48 | 0.07x |  | ok |  |
| 10 | proposal_10 | 157.01 | 1.01x |  | ok |  |
| 11 | proposal_11 | 159.25 | 1.00x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 12 | proposal_12 | 158.63 | 1.00x |  | ok |  |
| 13 | proposal_13 | 159.17 | 1.00x |  | ok |  |
| 14 | proposal_14 | 11908.98 | 0.01x |  | ok |  |
| 15 | proposal_15 | 198.64 | 0.80x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 16 | proposal_16 | 153.14 | 1.04x |  | ok |  |
| 17 | proposal_17 | 167.98 | 0.94x |  | hint_error | NoIndexScan(s1 _dta_index_store_sales_6_1333579789__k1_k3... |
| 18 | proposal_18 | 180.76 | 0.88x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 19 | proposal_19 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 20 | proposal_20 | 386.29 | 0.41x | Yes | hint_error | Parallel(store_sales 10 soft) \| number of workers = 10 is... |


### query101_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 676.58 | 1.00x |  | ok |  |
| 1 | proposal_1 | 1268.08 | 0.53x |  | ok |  |
| 2 | proposal_2 | 4973.80 | 0.14x |  | ok |  |
| 3 | proposal_3 | 17137.70 | 0.04x |  | ok |  |
| 4 | proposal_4 | 695.02 | 0.97x |  | ok |  |
| 5 | proposal_5 | 1299.09 | 0.52x |  | ok |  |
| 6 | proposal_6 | 5761.40 | 0.12x |  | ok |  |
| 7 | proposal_7 | 700.88 | 0.97x |  | ok |  |
| 8 | proposal_8 | 683.38 | 0.99x |  | ok |  |
| 9 | proposal_9 | 688.33 | 0.98x |  | ok |  |
| 10 | proposal_10 | 698.92 | 0.97x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 11 | proposal_11 | 1090.60 | 0.62x |  | ok |  |
| 12 | proposal_12 | 695.13 | 0.97x |  | ok |  |
| 13 | proposal_13 | 3664.70 | 0.18x |  | ok |  |
| 14 | proposal_14 | 662.84 | 1.02x |  | ok |  |
| 15 | proposal_15 | 11458.80 | 0.06x |  | ok |  |
| 16 | proposal_16 | 675.76 | 1.00x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 17 | proposal_17 | 3936.69 | 0.17x |  | ok |  |
| 18 | proposal_18 | 1289.72 | 0.52x |  | ok |  |
| 19 | proposal_19 | 5743.98 | 0.12x |  | ok |  |
| 20 | proposal_20 | 4248.32 | 0.16x | Yes | ok |  |


### query102_spj_0.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 6003.99 | 1.00x |  | ok |  |
| 1 | proposal_1 | 6136.02 | 0.98x |  | ok |  |
| 2 | proposal_2 | 16584.26 | 0.36x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 3 | proposal_3 | 24687.93 | 0.24x |  | ok |  |
| 4 | proposal_4 | 4203.36 | 1.43x |  | hint_error | Rows(item *0.03) \| Rows hint requires at least two relati... |
| 5 | proposal_5 | 44238.81 | 0.14x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 6 | proposal_6 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 7 | proposal_7 | 5818.57 | 1.03x |  | ok |  |
| 8 | proposal_8 | 15694.93 | 0.38x |  | ok |  |
| 9 | proposal_9 | 2823.64 | 2.13x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 10 | proposal_10 | 15468.29 | 0.39x |  | ok |  |
| 11 | proposal_11 | 5577.60 | 1.08x |  | hint_error | Rows(date_dim *0.003) \| Rows hint requires at least two r... |
| 12 | proposal_12 | 5650.35 | 1.06x |  | ok |  |
| 13 | proposal_13 | 4059.68 | 1.48x |  | ok |  |
| 14 | proposal_14 | 5550.86 | 1.08x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 15 | proposal_15 | 15769.01 | 0.38x |  | ok |  |
| 16 | proposal_16 | 5593.64 | 1.07x |  | ok |  |
| 17 | proposal_17 | 15588.83 | 0.39x |  | ok |  |
| 18 | proposal_18 | 36848.61 | 0.16x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 19 | proposal_19 | 5978.97 | 1.00x |  | ok |  |
| 20 | proposal_20 | 16056.62 | 0.37x | Yes | hint_error | Rows(store_sales *0.1) \| Rows hint requires at least two ... |


## IMDB

### 07c.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 5374.45 | 1.00x |  | ok |  |
| 1 | proposal_1 | 3910.11 | 1.37x |  | ok |  |
| 2 | proposal_2 | 5091.82 | 1.06x |  | ok |  |
| 3 | proposal_3 | 2764.52 | 1.94x |  | ok |  |
| 4 | proposal_4 | 5092.09 | 1.06x |  | ok |  |
| 5 | proposal_5 | 4159.53 | 1.29x |  | ok |  |
| 6 | proposal_6 | 5212.76 | 1.03x |  | ok |  |
| 7 | proposal_7 | 3470.48 | 1.55x |  | ok |  |
| 8 | proposal_8 | 3384.02 | 1.59x |  | ok |  |
| 9 | proposal_9 | 5268.62 | 1.02x |  | ok |  |
| 10 | proposal_10 | 5206.20 | 1.03x |  | ok |  |
| 11 | proposal_11 | 5187.90 | 1.04x |  | ok |  |
| 12 | proposal_12 | 6117.95 | 0.88x |  | ok |  |
| 13 | proposal_13 | 5144.10 | 1.04x |  | ok |  |
| 14 | proposal_14 | 5427.13 | 0.99x |  | hint_error | Parallel(cast_info 12 soft) \| number of workers = 12 is l... |
| 15 | proposal_15 | 5388.51 | 1.00x |  | ok |  |
| 16 | proposal_16 | 3167.82 | 1.70x |  | ok |  |
| 17 | proposal_17 | 2857.43 | 1.88x | Yes | hint_error | Parallel(cast_info 10 soft) Parallel(movie_link 10 soft) ... |
| 18 | proposal_18 | 5401.36 | 1.00x |  | ok |  |
| 19 | proposal_19 | 4842.14 | 1.11x |  | ok |  |
| 20 | proposal_20 | 3347.36 | 1.61x |  | hint_error | Parallel(cast_info 12 soft) \| number of workers = 12 is l... |


### 13d.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 2983.51 | 1.00x |  | ok |  |
| 1 | proposal_1 | 2791.26 | 1.07x |  | ok |  |
| 2 | proposal_2 | 2599.98 | 1.15x |  | ok |  |
| 3 | proposal_3 | 14935.13 | 0.20x |  | ok |  |
| 4 | proposal_4 | 2791.49 | 1.07x |  | ok |  |
| 5 | proposal_5 | 1407.63 | 2.12x |  | ok |  |
| 6 | proposal_6 | 2585.49 | 1.15x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 7 | proposal_7 | 2979.29 | 1.00x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 8 | proposal_8 | 6795.62 | 0.44x |  | ok |  |
| 9 | proposal_9 | 12205.17 | 0.24x |  | ok |  |
| 10 | proposal_10 | 6378.05 | 0.47x |  | ok |  |
| 11 | proposal_11 | 2527.05 | 1.18x |  | ok |  |
| 12 | proposal_12 | 3061.71 | 0.97x |  | ok |  |
| 13 | proposal_13 | 2661.85 | 1.12x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 14 | proposal_14 | 1620.42 | 1.84x |  | ok |  |
| 15 | proposal_15 | 11635.13 | 0.26x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 16 | proposal_16 | 2837.58 | 1.05x |  | ok |  |
| 17 | proposal_17 | 3003.15 | 0.99x |  | hint_error | Set(work_mem '128MB') \| Conflict scan method hint. Confli... |
| 18 | proposal_18 | 2628.36 | 1.14x |  | ok |  |
| 19 | proposal_19 | 2995.65 | 1.00x |  | ok |  |
| 20 | proposal_20 | 2076.27 | 1.44x | Yes | ok |  |


### 16b.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed) |
| 1 | proposal_1 | timeout | N/A | Yes | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 2 | proposal_2 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 3 | proposal_3 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 4 | proposal_4 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 5 | proposal_5 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 6 | proposal_6 | 36527.02 | N/A |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 7 | proposal_7 | 21505.71 | N/A |  | ok |  |
| 8 | proposal_8 | 26355.95 | N/A |  | ok |  |
| 9 | proposal_9 | 27802.72 | N/A |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 10 | proposal_10 | 21963.80 | N/A |  | ok |  |
| 11 | proposal_11 | 32640.12 | N/A |  | ok |  |
| 12 | proposal_12 | 26822.14 | N/A |  | ok |  |
| 13 | proposal_13 | 25650.99 | N/A |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 14 | proposal_14 | 23327.97 | N/A |  | ok |  |
| 15 | proposal_15 | 33261.16 | N/A |  | ok |  |
| 16 | proposal_16 | 18089.46 | N/A |  | ok |  |
| 17 | proposal_17 | 17409.16 | N/A |  | ok |  |
| 18 | proposal_18 | 33384.33 | N/A |  | ok |  |
| 19 | proposal_19 | 16792.51 | N/A |  | ok |  |
| 20 | proposal_20 | 25990.45 | N/A |  | ok |  |


### 17a.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 14093.29 | 1.00x |  | ok |  |
| 1 | proposal_1 | 12659.84 | 1.11x |  | ok |  |
| 2 | proposal_2 | 22939.81 | 0.61x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 3 | proposal_3 | 16862.37 | 0.84x |  | hint_error | Rows(ci *0.001) \| Rows hint requires at least two relatio... |
| 4 | proposal_4 | 11790.40 | 1.20x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 5 | proposal_5 | 17790.82 | 0.79x |  | ok |  |
| 6 | proposal_6 | 17310.48 | 0.81x |  | ok |  |
| 7 | proposal_7 | 22314.38 | 0.63x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 8 | proposal_8 | 22292.80 | 0.63x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 9 | proposal_9 | 15103.98 | 0.93x |  | ok |  |
| 10 | proposal_10 | 21252.09 | 0.66x |  | hint_error | Rows(cn *0.01) \| Rows hint requires at least two relation... |
| 11 | proposal_11 | 15745.22 | 0.90x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 12 | proposal_12 | 18931.26 | 0.74x |  | hint_error | Leading(((keyword movie_keyword) (title movie_companies) ... |
| 13 | proposal_13 | 18928.43 | 0.74x |  | hint_error | Rows(mc *0.01) \| Rows hint requires at least two relation... |
| 14 | proposal_14 | 21026.05 | 0.67x |  | ok |  |
| 15 | proposal_15 | 13351.31 | 1.06x |  | ok |  |
| 16 | proposal_16 | 4476.91 | 3.15x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 17 | proposal_17 | 21641.41 | 0.65x |  | hint_error | Rows(n *0.005) \| Rows hint requires at least two relation... |
| 18 | proposal_18 | 13347.60 | 1.06x |  | hint_error | Rows(k *1.0) \| Rows hint requires at least two relations.... |
| 19 | proposal_19 | 11088.39 | 1.27x |  | ok |  |
| 20 | proposal_20 | 21559.55 | 0.65x | Yes | ok |  |


### 17e.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 19425.86 | 1.00x |  | ok |  |
| 1 | proposal_1 | 3506.66 | 5.54x |  | ok |  |
| 2 | proposal_2 | 14051.92 | 1.38x |  | ok |  |
| 3 | proposal_3 | 22241.62 | 0.87x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 4 | proposal_4 | 20926.95 | 0.93x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 5 | proposal_5 | 6888.61 | 2.82x |  | ok |  |
| 6 | proposal_6 | 18223.00 | 1.07x |  | ok |  |
| 7 | proposal_7 | 21590.04 | 0.90x |  | ok |  |
| 8 | proposal_8 | 21306.30 | 0.91x |  | ok |  |
| 9 | proposal_9 | 21967.82 | 0.88x |  | ok |  |
| 10 | proposal_10 | 11842.16 | 1.64x |  | ok |  |
| 11 | proposal_11 | 5722.14 | 3.39x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 12 | proposal_12 | 6460.53 | 3.01x |  | ok |  |
| 13 | proposal_13 | 18721.34 | 1.04x |  | ok |  |
| 14 | proposal_14 | 19389.10 | 1.00x |  | ok |  |
| 15 | proposal_15 | 3905.99 | 4.97x |  | ok |  |
| 16 | proposal_16 | 13076.67 | 1.49x |  | ok |  |
| 17 | proposal_17 | 21132.46 | 0.92x |  | ok |  |
| 18 | proposal_18 | 17134.58 | 1.13x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 19 | proposal_19 | 6515.75 | 2.98x |  | ok |  |
| 20 | proposal_20 | 14087.03 | 1.38x | Yes | ok |  |


### 17f.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 15200.80 | 1.00x |  | ok |  |
| 1 | proposal_1 | 4629.51 | 3.28x |  | ok |  |
| 2 | proposal_2 | 15405.76 | 0.99x |  | ok |  |
| 3 | proposal_3 | 12787.23 | 1.19x |  | ok |  |
| 4 | proposal_4 | 33700.15 | 0.45x |  | ok |  |
| 5 | proposal_5 | 10255.86 | 1.48x |  | ok |  |
| 6 | proposal_6 | 15637.89 | 0.97x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 7 | proposal_7 | 14451.76 | 1.05x |  | ok |  |
| 8 | proposal_8 | 16333.09 | 0.93x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 9 | proposal_9 | 33080.16 | 0.46x |  | ok |  |
| 10 | proposal_10 | 15224.60 | 1.00x |  | ok |  |
| 11 | proposal_11 | 2734.01 | 5.56x |  | ok |  |
| 12 | proposal_12 | 10376.31 | 1.46x |  | hint_error | Leading((k (mk t) (mc cn) ci n)) \| Leading hint requires ... |
| 13 | proposal_13 | 30743.91 | 0.49x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 14 | proposal_14 | 9456.30 | 1.61x |  | ok |  |
| 15 | proposal_15 | 14767.32 | 1.03x |  | ok |  |
| 16 | proposal_16 | 14905.94 | 1.02x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 17 | proposal_17 | 10042.31 | 1.51x |  | ok |  |
| 18 | proposal_18 | 10205.06 | 1.49x |  | ok |  |
| 19 | proposal_19 | 4236.53 | 3.59x |  | ok |  |
| 20 | proposal_20 | 2774.85 | 5.48x | Yes | ok |  |


### 18c.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 5946.40 | 1.00x |  | ok |  |
| 1 | proposal_1 | 3586.53 | 1.66x |  | hint_error | Rows(movie_info_idx *0.2) \| Rows hint requires at least t... |
| 2 | proposal_2 | 5666.79 | 1.05x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 3 | proposal_3 | 4353.04 | 1.37x |  | ok |  |
| 4 | proposal_4 | 5130.51 | 1.16x |  | ok |  |
| 5 | proposal_5 | 10228.17 | 0.58x | Yes | ok |  |
| 6 | proposal_6 | 5107.16 | 1.16x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 7 | proposal_7 | 3422.70 | 1.74x |  | ok |  |
| 8 | proposal_8 | 6382.31 | 0.93x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 9 | proposal_9 | 4112.69 | 1.45x |  | ok |  |
| 10 | proposal_10 | 4873.81 | 1.22x |  | ok |  |
| 11 | proposal_11 | 5873.59 | 1.01x |  | ok |  |
| 12 | proposal_12 | 6607.33 | 0.90x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 13 | proposal_13 | 3722.81 | 1.60x |  | ok |  |
| 14 | proposal_14 | 6521.37 | 0.91x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 15 | proposal_15 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 16 | proposal_16 | 5152.77 | 1.15x |  | ok |  |
| 17 | proposal_17 | 6343.90 | 0.94x |  | ok |  |
| 18 | proposal_18 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 19 | proposal_19 | 6407.21 | 0.93x |  | ok |  |
| 20 | proposal_20 | 11837.13 | 0.50x |  | ok |  |


### 19d.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 15801.86 | 1.00x |  | ok |  |
| 1 | proposal_1 | 22247.17 | 0.71x | Yes | ok |  |
| 2 | proposal_2 | 16679.81 | 0.95x |  | ok |  |
| 3 | proposal_3 | 19312.70 | 0.82x |  | ok |  |
| 4 | proposal_4 | 16498.77 | 0.96x |  | ok |  |
| 5 | proposal_5 | 5390.32 | 2.93x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 6 | proposal_6 | 12414.01 | 1.27x |  | ok |  |
| 7 | proposal_7 | 18693.92 | 0.85x |  | ok |  |
| 8 | proposal_8 | 12760.30 | 1.24x |  | ok |  |
| 9 | proposal_9 | 13298.30 | 1.19x |  | ok |  |
| 10 | proposal_10 | 12705.55 | 1.24x |  | hint_error | Parallel(cast_info 16 soft) Parallel(title 16 soft) Paral... |
| 11 | proposal_11 | 12870.32 | 1.23x |  | hint_error | Set(work_mem '256MB') Rows(title *0.2) \| Rows hint requir... |
| 12 | proposal_12 | 22880.46 | 0.69x |  | hint_error | Set(work_mem '128MB') \| Conflict join method hint. \| pg_h... |
| 13 | proposal_13 | 18472.29 | 0.86x |  | ok |  |
| 14 | proposal_14 | 18740.09 | 0.84x |  | ok |  |
| 15 | proposal_15 | 15682.42 | 1.01x |  | ok |  |
| 16 | proposal_16 | 16459.28 | 0.96x |  | ok |  |
| 17 | proposal_17 | 19236.25 | 0.82x |  | ok |  |
| 18 | proposal_18 | 15969.31 | 0.99x |  | hint_error | Set(work_mem '128MB') \| Conflict join method hint. \| pg_h... |
| 19 | proposal_19 | 22560.15 | 0.70x |  | ok |  |
| 20 | proposal_20 | 12903.79 | 1.22x |  | hint_error | Set(work_mem '256MB') Rows(title *0.2) \| Rows hint requir... |


### 25c.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 8377.18 | 1.00x |  | ok |  |
| 1 | proposal_1 | 5845.42 | 1.43x | Yes | ok |  |
| 2 | proposal_2 | 10028.14 | 0.84x |  | ok |  |
| 3 | proposal_3 | 15759.03 | 0.53x |  | ok |  |
| 4 | proposal_4 | 12810.34 | 0.65x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 5 | proposal_5 | 13144.61 | 0.64x |  | ok |  |
| 6 | proposal_6 | 4420.82 | 1.89x |  | ok |  |
| 7 | proposal_7 | 8420.99 | 0.99x |  | ok |  |
| 8 | proposal_8 | 12735.01 | 0.66x |  | ok |  |
| 9 | proposal_9 | 11104.19 | 0.75x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 10 | proposal_10 | 9657.16 | 0.87x |  | ok |  |
| 11 | proposal_11 | 7266.90 | 1.15x |  | ok |  |
| 12 | proposal_12 | 10982.69 | 0.76x |  | ok |  |
| 13 | proposal_13 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 14 | proposal_14 | 12511.88 | 0.67x |  | ok |  |
| 15 | proposal_15 | 11171.74 | 0.75x |  | ok |  |
| 16 | proposal_16 | 10033.51 | 0.83x |  | ok |  |
| 17 | proposal_17 | 9741.70 | 0.86x |  | ok |  |
| 18 | proposal_18 | 13636.22 | 0.61x |  | ok |  |
| 19 | proposal_19 | 13023.43 | 0.64x |  | ok |  |
| 20 | proposal_20 | 3648.47 | 2.30x |  | ok |  |


### 28a.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1391.57 | 1.00x |  | ok |  |
| 1 | proposal_1 | 945.07 | 1.47x | Yes | hint_error | Rows(movie_keyword *40.7) \| Rows hint requires at least t... |
| 2 | proposal_2 | 1744.75 | 0.80x |  | ok |  |
| 3 | proposal_3 | 1059.87 | 1.31x |  | ok |  |
| 4 | proposal_4 | 20260.34 | 0.07x |  | ok |  |
| 5 | proposal_5 | 1015.72 | 1.37x |  | hint_error | Leading(((k mk) (it1 mi) (t kt) (cc cct1) (mc cn) (mi_idx... |
| 6 | proposal_6 | 1100.81 | 1.26x |  | ok |  |
| 7 | proposal_7 | 920.61 | 1.51x |  | ok |  |
| 8 | proposal_8 | 863.74 | 1.61x |  | ok |  |
| 9 | proposal_9 | 1677.14 | 0.83x |  | ok |  |
| 10 | proposal_10 | 1666.00 | 0.84x |  | ok |  |
| 11 | proposal_11 | 20301.45 | 0.07x |  | ok |  |
| 12 | proposal_12 | 1515.34 | 0.92x |  | hint_error | Set(work_mem '256MB') Rows(movie_companies *1000) \| Rows ... |
| 13 | proposal_13 | 1472.69 | 0.94x |  | ok |  |
| 14 | proposal_14 | 951.87 | 1.46x |  | hint_error | Set(work_mem '256MB') \| Conflict scan method hint. \| pg_h... |
| 15 | proposal_15 | 1351.36 | 1.03x |  | ok |  |
| 16 | proposal_16 | 971.63 | 1.43x |  | ok |  |
| 17 | proposal_17 | 1618.35 | 0.86x |  | hint_error | Leading(((k mk) mi_idx mi t)) Set(work_mem '256MB') \| Lea... |
| 18 | proposal_18 | 1581.76 | 0.88x |  | ok |  |
| 19 | proposal_19 | 1491.74 | 0.93x |  | ok |  |
| 20 | proposal_20 | 1409.60 | 0.99x |  | ok |  |


### 28b.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1019.14 | 1.00x |  | ok |  |
| 1 | proposal_1 | 942.72 | 1.08x | Yes | ok |  |
| 2 | proposal_2 | 971.26 | 1.05x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 3 | proposal_3 | 964.33 | 1.06x |  | ok |  |
| 4 | proposal_4 | 980.63 | 1.04x |  | hint_error | Rows(movie_keyword *41.2) \| Rows hint requires at least t... |
| 5 | proposal_5 | 619.88 | 1.64x |  | ok |  |
| 6 | proposal_6 | 1022.76 | 1.00x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 7 | proposal_7 | 1043.09 | 0.98x |  | ok |  |
| 8 | proposal_8 | 1061.25 | 0.96x |  | ok |  |
| 9 | proposal_9 | 1066.78 | 0.96x |  | ok |  |
| 10 | proposal_10 | 1066.04 | 0.96x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 11 | proposal_11 | 1054.82 | 0.97x |  | ok |  |
| 12 | proposal_12 | 977.23 | 1.04x |  | ok |  |
| 13 | proposal_13 | 809.42 | 1.26x |  | ok |  |
| 14 | proposal_14 | 566.74 | 1.80x |  | ok |  |
| 15 | proposal_15 | 917.21 | 1.11x |  | ok |  |
| 16 | proposal_16 | 1073.75 | 0.95x |  | ok |  |
| 17 | proposal_17 | 980.50 | 1.04x |  | ok |  |
| 18 | proposal_18 | 624.67 | 1.63x |  | ok |  |
| 19 | proposal_19 | 638.52 | 1.60x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 20 | proposal_20 | 660.10 | 1.54x |  | ok |  |


### 28c.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1999.33 | 1.00x |  | ok |  |
| 1 | proposal_1 | 1400.44 | 1.43x |  | hint_error | Rows(keyword *0.75) Rows(movie_keyword *40.7) \| Rows hint... |
| 2 | proposal_2 | 1063.38 | 1.88x |  | ok |  |
| 3 | proposal_3 | 1870.24 | 1.07x |  | ok |  |
| 4 | proposal_4 | 2218.01 | 0.90x |  | ok |  |
| 5 | proposal_5 | 2073.54 | 0.96x |  | ok |  |
| 6 | proposal_6 | 4297.95 | 0.47x |  | ok |  |
| 7 | proposal_7 | 3264.16 | 0.61x |  | ok |  |
| 8 | proposal_8 | 1989.49 | 1.00x |  | ok |  |
| 9 | proposal_9 | 1341.63 | 1.49x |  | ok |  |
| 10 | proposal_10 | 1877.40 | 1.06x |  | ok |  |
| 11 | proposal_11 | 1865.63 | 1.07x |  | ok |  |
| 12 | proposal_12 | 1939.37 | 1.03x |  | ok |  |
| 13 | proposal_13 | 1137.70 | 1.76x |  | ok |  |
| 14 | proposal_14 | 1359.36 | 1.47x |  | ok |  |
| 15 | proposal_15 | 601.65 | 3.32x |  | ok |  |
| 16 | proposal_16 | 3152.04 | 0.63x |  | ok |  |
| 17 | proposal_17 | 1331.91 | 1.50x |  | ok |  |
| 18 | proposal_18 | 2318.03 | 0.86x |  | ok |  |
| 19 | proposal_19 | 1242.36 | 1.61x |  | ok |  |
| 20 | proposal_20 | 3751.69 | 0.53x | Yes | hint_error | Rows(movie_keyword *40.7) \| Rows hint requires at least t... |


### 29a.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 299.20 | 1.00x |  | ok |  |
| 1 | proposal_1 | 277.99 | 1.08x | Yes | hint_error | Rows(mk *0.001) \| Rows hint requires at least two relatio... |
| 2 | proposal_2 | 313.63 | 0.95x |  | hint_error | Rows(mk *0.001) \| Rows hint requires at least two relatio... |
| 3 | proposal_3 | 303.81 | 0.98x |  | hint_error | Rows(mi *0.001) Rows(cc *0.001) \| Rows hint requires at l... |
| 4 | proposal_4 | 294.44 | 1.02x |  | ok |  |
| 5 | proposal_5 | 324.70 | 0.92x |  | hint_error | Rows(mi *0.001) \| Rows hint requires at least two relatio... |
| 6 | proposal_6 | 302.78 | 0.99x |  | hint_error | HashJoin(chn) Leading(((title mk) (ci mi) (cc mc) (cn n) ... |
| 7 | proposal_7 | 293.14 | 1.02x |  | hint_error | Rows(cc *0.001) Rows(mc *0.001) Rows(mi *0.001) Rows(mk *... |
| 8 | proposal_8 | 318.08 | 0.94x |  | ok |  |
| 9 | proposal_9 | 259.39 | 1.15x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 10 | proposal_10 | 291.57 | 1.03x |  | ok |  |
| 11 | proposal_11 | 323.69 | 0.92x |  | ok |  |
| 12 | proposal_12 | 193.93 | 1.54x |  | hint_error | Rows(mk *0.001) Rows(ci *0.001) Rows(mi *0.001) Rows(cc *... |
| 13 | proposal_13 | 290.37 | 1.03x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 14 | proposal_14 | 286.89 | 1.04x |  | ok |  |
| 15 | proposal_15 | 203.89 | 1.47x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 16 | proposal_16 | 192.22 | 1.56x |  | ok |  |
| 17 | proposal_17 | 308.35 | 0.97x |  | ok |  |
| 18 | proposal_18 | 251.54 | 1.19x |  | hint_error | Rows(mk *0.001) Rows(ci *0.001) Rows(mi *0.001) Rows(cc *... |
| 19 | proposal_19 | 299.94 | 1.00x |  | hint_error | Conflict join method hint. Conflict join method hint. Con... |
| 20 | proposal_20 | 307.35 | 0.97x |  | ok |  |


### 29b.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 305.06 | 1.00x |  | ok |  |
| 1 | proposal_1 | 304.30 | 1.00x | Yes | hint_error | Rows(movie_keyword *414.0) \| Rows hint requires at least ... |
| 2 | proposal_2 | 237.33 | 1.29x |  | ok |  |
| 3 | proposal_3 | 285.43 | 1.07x |  | hint_error | Rows(ci *38.0) \| Rows hint requires at least two relation... |
| 4 | proposal_4 | 312.10 | 0.98x |  | ok |  |
| 5 | proposal_5 | 252.83 | 1.21x |  | ok |  |
| 6 | proposal_6 | 11074.30 | 0.03x |  | hint_error | Set(work_mem '128MB') Rows(mi *1.0) \| Rows hint requires ... |
| 7 | proposal_7 | 197.95 | 1.54x |  | ok |  |
| 8 | proposal_8 | 248.69 | 1.23x |  | ok |  |
| 9 | proposal_9 | 1197.22 | 0.25x |  | ok |  |
| 10 | proposal_10 | 309.24 | 0.99x |  | ok |  |
| 11 | proposal_11 | 284.28 | 1.07x |  | ok |  |
| 12 | proposal_12 | 274.15 | 1.11x |  | hint_error | Rows(mc *22.0) \| Rows hint requires at least two relation... |
| 13 | proposal_13 | 301.41 | 1.01x |  | ok |  |
| 14 | proposal_14 | 266.52 | 1.14x |  | ok |  |
| 15 | proposal_15 | 270.53 | 1.13x |  | ok |  |
| 16 | proposal_16 | 196.57 | 1.55x |  | ok |  |
| 17 | proposal_17 | 1243.10 | 0.25x |  | ok |  |
| 18 | proposal_18 | 251.85 | 1.21x |  | ok |  |
| 19 | proposal_19 | 270.82 | 1.13x |  | hint_error | Rows(ci *38.0) \| Rows hint requires at least two relation... |
| 20 | proposal_20 | 1996.25 | 0.15x |  | ok |  |


### 29c.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1482.84 | 1.00x |  | ok |  |
| 1 | proposal_1 | 2588.28 | 0.57x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 2 | proposal_2 | 1440.15 | 1.03x |  | ok |  |
| 3 | proposal_3 | 1447.40 | 1.02x |  | ok |  |
| 4 | proposal_4 | 2488.48 | 0.60x |  | ok |  |
| 5 | proposal_5 | 2008.34 | 0.74x |  | ok |  |
| 6 | proposal_6 | 2177.44 | 0.68x |  | ok |  |
| 7 | proposal_7 | 345.30 | 4.29x |  | ok |  |
| 8 | proposal_8 | 1561.05 | 0.95x |  | ok |  |
| 9 | proposal_9 | 1473.61 | 1.01x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 10 | proposal_10 | 2512.68 | 0.59x |  | ok |  |
| 11 | proposal_11 | 2548.86 | 0.58x |  | ok |  |
| 12 | proposal_12 | 2602.65 | 0.57x |  | ok |  |
| 13 | proposal_13 | 2790.15 | 0.53x |  | ok |  |
| 14 | proposal_14 | 2629.34 | 0.56x |  | ok |  |
| 15 | proposal_15 | 2504.17 | 0.59x |  | ok |  |
| 16 | proposal_16 | 1457.39 | 1.02x | Yes | ok |  |
| 17 | proposal_17 | 2504.60 | 0.59x |  | ok |  |
| 18 | proposal_18 | 2619.13 | 0.57x |  | hint_error | Parallel(movie_info 12 soft) \| number of workers = 12 is ... |
| 19 | proposal_19 | 651.43 | 2.28x |  | ok |  |
| 20 | proposal_20 | 1415.78 | 1.05x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |


### 31c.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 787.54 | 1.00x |  | ok |  |
| 1 | proposal_1 | 773.46 | 1.02x |  | ok |  |
| 2 | proposal_2 | 991.46 | 0.79x |  | ok |  |
| 3 | proposal_3 | 1077.67 | 0.73x |  | ok |  |
| 4 | proposal_4 | 866.67 | 0.91x | Yes | ok |  |
| 5 | proposal_5 | 653.20 | 1.21x |  | ok |  |
| 6 | proposal_6 | 15469.66 | 0.05x |  | ok |  |
| 7 | proposal_7 | 760.55 | 1.04x |  | ok |  |
| 8 | proposal_8 | 1014.27 | 0.78x |  | ok |  |
| 9 | proposal_9 | 579.23 | 1.36x |  | ok |  |
| 10 | proposal_10 | 897.69 | 0.88x |  | ok |  |
| 11 | proposal_11 | 908.21 | 0.87x |  | ok |  |
| 12 | proposal_12 | 1016.26 | 0.77x |  | ok |  |
| 13 | proposal_13 | 1104.52 | 0.71x |  | ok |  |
| 14 | proposal_14 | 14861.51 | 0.05x |  | ok |  |
| 15 | proposal_15 | 913.77 | 0.86x |  | ok |  |
| 16 | proposal_16 | 1106.86 | 0.71x |  | ok |  |
| 17 | proposal_17 | 13960.88 | 0.06x |  | ok |  |
| 18 | proposal_18 | 990.71 | 0.79x |  | ok |  |
| 19 | proposal_19 | 1519.24 | 0.52x |  | ok |  |
| 20 | proposal_20 | 5445.22 | 0.14x |  | ok |  |


### 33a.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 273.76 | 1.00x |  | ok |  |
| 1 | proposal_1 | 271.05 | 1.01x |  | hint_error | Leading(((link_type movie_link) (info_type movie_info_idx... |
| 2 | proposal_2 | 238.98 | 1.15x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 3 | proposal_3 | 260.54 | 1.05x | Yes | hint_error | Leading(((kind_type kt1) (info_type it1) (link_type lt) (... |
| 4 | proposal_4 | 268.78 | 1.02x |  | ok |  |
| 5 | proposal_5 | 263.34 | 1.04x |  | ok |  |
| 6 | proposal_6 | 237.35 | 1.15x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 7 | proposal_7 | 163.76 | 1.67x |  | ok |  |
| 8 | proposal_8 | 247.86 | 1.10x |  | ok |  |
| 9 | proposal_9 | 239.56 | 1.14x |  | ok |  |
| 10 | proposal_10 | 148.61 | 1.84x |  | ok |  |
| 11 | proposal_11 | 258.81 | 1.06x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 12 | proposal_12 | 223.57 | 1.22x |  | ok |  |
| 13 | proposal_13 | 236.26 | 1.16x |  | ok |  |
| 14 | proposal_14 | 261.23 | 1.05x |  | hint_error | Leading(((kind_type kt1) (info_type it1) (link_type lt) (... |
| 15 | proposal_15 | 226.77 | 1.21x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 16 | proposal_16 | 236.98 | 1.16x |  | ok |  |
| 17 | proposal_17 | 259.55 | 1.05x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 18 | proposal_18 | 152.53 | 1.79x |  | ok |  |
| 19 | proposal_19 | 236.33 | 1.16x |  | ok |  |
| 20 | proposal_20 | 256.27 | 1.07x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |


### 33b.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 317.72 | 1.00x |  | ok |  |
| 1 | proposal_1 | 312.15 | 1.02x |  | ok |  |
| 2 | proposal_2 | 218.81 | 1.45x |  | ok |  |
| 3 | proposal_3 | 307.98 | 1.03x | Yes | ok |  |
| 4 | proposal_4 | 302.19 | 1.05x |  | hint_error | Rows(movie_companies *0.1) \| Rows hint requires at least ... |
| 5 | proposal_5 | 285.80 | 1.11x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 6 | proposal_6 | 315.37 | 1.01x |  | ok |  |
| 7 | proposal_7 | 247.51 | 1.28x |  | ok |  |
| 8 | proposal_8 | 297.69 | 1.07x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 9 | proposal_9 | 297.41 | 1.07x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 10 | proposal_10 | 281.55 | 1.13x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 11 | proposal_11 | 311.15 | 1.02x |  | ok |  |
| 12 | proposal_12 | 167.25 | 1.90x |  | ok |  |
| 13 | proposal_13 | 298.10 | 1.07x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 14 | proposal_14 | 182.66 | 1.74x |  | ok |  |
| 15 | proposal_15 | 281.63 | 1.13x |  | ok |  |
| 16 | proposal_16 | 313.84 | 1.01x |  | ok |  |
| 17 | proposal_17 | 202.24 | 1.57x |  | ok |  |
| 18 | proposal_18 | 291.70 | 1.09x |  | ok |  |
| 19 | proposal_19 | 311.75 | 1.02x |  | ok |  |
| 20 | proposal_20 | 264.81 | 1.20x |  | ok |  |


### 33c.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 405.10 | 1.00x |  | ok |  |
| 1 | proposal_1 | 395.88 | 1.02x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 2 | proposal_2 | 430.31 | 0.94x |  | ok |  |
| 3 | proposal_3 | 260.48 | 1.56x |  | ok |  |
| 4 | proposal_4 | 392.74 | 1.03x | Yes | ok |  |
| 5 | proposal_5 | 439.41 | 0.92x |  | ok |  |
| 6 | proposal_6 | 346.93 | 1.17x |  | ok |  |
| 7 | proposal_7 | 434.27 | 0.93x |  | ok |  |
| 8 | proposal_8 | 422.91 | 0.96x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 9 | proposal_9 | 404.09 | 1.00x |  | ok |  |
| 10 | proposal_10 | 431.32 | 0.94x |  | ok |  |
| 11 | proposal_11 | 337.58 | 1.20x |  | ok |  |
| 12 | proposal_12 | 410.33 | 0.99x |  | hint_error | Leading(((movie_link info_type) (title kind_type) (movie_... |
| 13 | proposal_13 | 440.54 | 0.92x |  | ok |  |
| 14 | proposal_14 | 368.47 | 1.10x |  | ok |  |
| 15 | proposal_15 | 387.67 | 1.04x |  | ok |  |
| 16 | proposal_16 | 246.58 | 1.64x |  | ok |  |
| 17 | proposal_17 | 384.02 | 1.05x |  | ok |  |
| 18 | proposal_18 | 411.34 | 0.98x |  | ok |  |
| 19 | proposal_19 | 223.33 | 1.81x |  | ok |  |
| 20 | proposal_20 | 376.99 | 1.07x |  | ok |  |


## TPCH

### q01.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 13911.27 | 1.00x |  | ok |  |
| 1 | proposal_1 | 29306.20 | 0.47x |  | hint_error | Leading((lineitem)) Rows(lineitem *0.0042) \| Rows hint re... |
| 2 | proposal_2 | 16811.82 | 0.83x |  | hint_error | Rows(lineitem *0.0042) \| Rows hint requires at least two ... |
| 3 | proposal_3 | 17151.42 | 0.81x |  | hint_error | Rows(lineitem *0.0042) \| Rows hint requires at least two ... |
| 4 | proposal_4 | 26410.58 | 0.53x |  | hint_error | Leading((lineitem)) Rows(lineitem *0.0004) \| Rows hint re... |
| 5 | proposal_5 | 17003.50 | 0.82x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 6 | proposal_6 | 16863.92 | 0.82x |  | hint_error | Leading((lineitem)) Rows(lineitem *0.0004) \| Leading hint... |
| 7 | proposal_7 | 9224.40 | 1.51x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 8 | proposal_8 | 16833.58 | 0.83x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 9 | proposal_9 | 13310.03 | 1.05x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 10 | proposal_10 | 44380.31 | 0.31x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 11 | proposal_11 | 17140.10 | 0.81x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 12 | proposal_12 | 16926.05 | 0.82x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 13 | proposal_13 | 17035.29 | 0.82x |  | hint_error | Set(work_mem '64MB') Rows(lineitem *0.0004) \| Rows hint r... |
| 14 | proposal_14 | 26776.20 | 0.52x |  | hint_error | Unrecognized hint keyword "HashAggregate". \| pg_hint_plan... |
| 15 | proposal_15 | 17188.51 | 0.81x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 16 | proposal_16 | 17134.52 | 0.81x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 17 | proposal_17 | 27161.40 | 0.51x |  | hint_error | Rows(lineitem *0.0004) Parallel(lineitem 16 soft) \| Rows ... |
| 18 | proposal_18 | 16876.86 | 0.82x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 19 | proposal_19 | 16789.48 | 0.83x |  | hint_error | Rows(lineitem *0.0004) \| Rows hint requires at least two ... |
| 20 | proposal_20 | 26780.26 | 0.52x | Yes | hint_error | Set(work_mem '128MB') Rows(lineitem *0.0004) Parallel(lin... |


### q02.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 3290.47 | 1.00x |  | ok |  |
| 1 | proposal_1 | 7000.76 | 0.47x |  | hint_error | Rows(part *0.2) \| Rows hint requires at least two relatio... |
| 2 | proposal_2 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 3 | proposal_3 | 3255.13 | 1.01x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 4 | proposal_4 | 6664.20 | 0.49x | Yes | hint_error | Rows(part *0.1) \| Rows hint requires at least two relatio... |
| 5 | proposal_5 | 3309.07 | 0.99x |  | hint_error | Rows(part *0.03) \| Rows hint requires at least two relati... |
| 6 | proposal_6 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 7 | proposal_7 | 3068.91 | 1.07x |  | hint_error | Unrecognized hint keyword "NoSort". Conflict join method ... |
| 8 | proposal_8 | 3105.61 | 1.06x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 9 | proposal_9 | 23312.94 | 0.14x |  | ok |  |
| 10 | proposal_10 | 3224.75 | 1.02x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 11 | proposal_11 | 2519.64 | 1.31x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 12 | proposal_12 | 3258.87 | 1.01x |  | hint_error | Set(work_mem '128MB') \| Unrecognized hint keyword "NoSort... |
| 13 | proposal_13 | 3126.04 | 1.05x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 14 | proposal_14 | 3270.80 | 1.01x |  | ok |  |
| 15 | proposal_15 | 3166.82 | 1.04x |  | hint_error | Unrecognized hint keyword "NoParallel". \| pg_hint_plan: h... |
| 16 | proposal_16 | 3164.63 | 1.04x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 17 | proposal_17 | 3097.35 | 1.06x |  | ok |  |
| 18 | proposal_18 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 19 | proposal_19 | 3131.25 | 1.05x |  | ok |  |
| 20 | proposal_20 | 3122.09 | 1.05x |  | ok |  |


### q03.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 4050.68 | 1.00x |  | ok |  |
| 1 | proposal_1 | 4168.74 | 0.97x |  | hint_error | Rows(customer *0.8) \| Rows hint requires at least two rel... |
| 2 | proposal_2 | 7562.56 | 0.54x |  | ok |  |
| 3 | proposal_3 | 5025.30 | 0.81x |  | ok |  |
| 4 | proposal_4 | 12759.37 | 0.32x |  | hint_error | Unrecognized hint keyword "NoSort". \| pg_hint_plan: hint ... |
| 5 | proposal_5 | 11057.85 | 0.37x |  | hint_error | Rows(customer *0.8) \| Rows hint requires at least two rel... |
| 6 | proposal_6 | 4019.42 | 1.01x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 7 | proposal_7 | 2776.39 | 1.46x |  | ok |  |
| 8 | proposal_8 | 4154.73 | 0.97x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 9 | proposal_9 | 3052.73 | 1.33x |  | ok |  |
| 10 | proposal_10 | 4189.72 | 0.97x |  | ok |  |
| 11 | proposal_11 | 4675.02 | 0.87x |  | hint_error | Set(work_mem '128MB') \| Unrecognized hint keyword "NoPara... |
| 12 | proposal_12 | 4389.04 | 0.92x |  | ok |  |
| 13 | proposal_13 | 10490.39 | 0.39x |  | ok |  |
| 14 | proposal_14 | 15081.87 | 0.27x |  | ok |  |
| 15 | proposal_15 | 7021.13 | 0.58x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 16 | proposal_16 | 4163.09 | 0.97x |  | ok |  |
| 17 | proposal_17 | 37351.24 | 0.11x |  | ok |  |
| 18 | proposal_18 | 4114.70 | 0.98x | Yes | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 19 | proposal_19 | 4108.58 | 0.99x |  | hint_error | Set(maintenance_work_mem '1GB') Set(work_mem '512MB') \| U... |
| 20 | proposal_20 | 55304.34 | 0.07x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |


### q04.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1487.25 | 1.00x |  | ok |  |
| 1 | proposal_1 | 3635.75 | 0.41x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 2 | proposal_2 | 40642.27 | 0.04x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 3 | proposal_3 | 3778.82 | 0.39x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 4 | proposal_4 | 34534.70 | 0.04x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 5 | proposal_5 | 3835.24 | 0.39x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 6 | proposal_6 | 34067.15 | 0.04x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 7 | proposal_7 | 5012.80 | 0.30x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 8 | proposal_8 | 34525.81 | 0.04x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 9 | proposal_9 | 5016.22 | 0.30x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 10 | proposal_10 | 3697.23 | 0.40x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 11 | proposal_11 | 2176.92 | 0.68x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 12 | proposal_12 | 34832.46 | 0.04x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 13 | proposal_13 | 3494.21 | 0.43x | Yes | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 14 | proposal_14 | 4047.06 | 0.37x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 15 | proposal_15 | 4758.44 | 0.31x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 16 | proposal_16 | 4946.63 | 0.30x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 17 | proposal_17 | 3429.52 | 0.43x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 18 | proposal_18 | 35319.01 | 0.04x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 19 | proposal_19 | 35081.69 | 0.04x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 20 | proposal_20 | 3579.83 | 0.42x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |


### q05.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 2355.64 | 1.00x |  | ok |  |
| 1 | proposal_1 | 2734.19 | 0.86x | Yes | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 2 | proposal_2 | 3795.42 | 0.62x |  | ok |  |
| 3 | proposal_3 | 2291.31 | 1.03x |  | ok |  |
| 4 | proposal_4 | 1762.37 | 1.34x |  | ok |  |
| 5 | proposal_5 | 12936.24 | 0.18x |  | ok |  |
| 6 | proposal_6 | 2279.39 | 1.03x |  | ok |  |
| 7 | proposal_7 | 4419.75 | 0.53x |  | ok |  |
| 8 | proposal_8 | 2343.85 | 1.01x |  | ok |  |
| 9 | proposal_9 | 3339.33 | 0.71x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 10 | proposal_10 | 2356.86 | 1.00x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 11 | proposal_11 | 2365.40 | 1.00x |  | ok |  |
| 12 | proposal_12 | 12392.32 | 0.19x |  | ok |  |
| 13 | proposal_13 | 25309.64 | 0.09x |  | ok |  |
| 14 | proposal_14 | 2393.05 | 0.98x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 15 | proposal_15 | 2633.59 | 0.89x |  | ok |  |
| 16 | proposal_16 | 3299.14 | 0.71x |  | ok |  |
| 17 | proposal_17 | 2330.84 | 1.01x |  | hint_error | Conflict scan method hint. Conflict scan method hint. Con... |
| 18 | proposal_18 | 3633.87 | 0.65x |  | ok |  |
| 19 | proposal_19 | 2282.10 | 1.03x |  | ok |  |
| 20 | proposal_20 | 3366.02 | 0.70x |  | hint_error | Rows(orders *0.1) Rows(lineitem *0.5) \| Rows hint require... |


### q06.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 2869.80 | 1.00x |  | ok |  |
| 1 | proposal_1 | 1719.99 | 1.67x |  | hint_error | Rows(lineitem *3.5) \| Rows hint requires at least two rel... |
| 2 | proposal_2 | 2596.97 | 1.11x | Yes | hint_error | Rows(lineitem *2.8) \| Rows hint requires at least two rel... |
| 3 | proposal_3 | 1691.70 | 1.70x |  | hint_error | Set(work_mem '256MB') Rows(lineitem *3.0) Parallel(lineit... |
| 4 | proposal_4 | 2895.53 | 0.99x |  | ok |  |
| 5 | proposal_5 | 2550.00 | 1.13x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 6 | proposal_6 | 2803.74 | 1.02x |  | hint_error | Rows(lineitem #1620000) Parallel(lineitem 16 soft) \| Rows... |
| 7 | proposal_7 | 2916.32 | 0.98x |  | ok |  |
| 8 | proposal_8 | 2560.17 | 1.12x |  | hint_error | Rows(lineitem *2.5) \| Rows hint requires at least two rel... |
| 9 | proposal_9 | 1705.66 | 1.68x |  | hint_error | Set(work_mem '256MB') Parallel(lineitem 16 soft) \| number... |
| 10 | proposal_10 | 3313.86 | 0.87x |  | hint_error | Rows(lineitem *3.0) \| Rows hint requires at least two rel... |
| 11 | proposal_11 | 3194.73 | 0.90x |  | ok |  |
| 12 | proposal_12 | 2806.88 | 1.02x |  | hint_error | Rows(lineitem *2.8) Parallel(lineitem 12 soft) \| Rows hin... |
| 13 | proposal_13 | 2959.90 | 0.97x |  | hint_error | Set(work_mem '256MB') Parallel(lineitem 12 soft) \| number... |
| 14 | proposal_14 | 2582.96 | 1.11x |  | hint_error | Rows(lineitem *3.0) \| Rows hint requires at least two rel... |
| 15 | proposal_15 | 2972.73 | 0.97x |  | ok |  |
| 16 | proposal_16 | 3131.83 | 0.92x |  | hint_error | Rows(lineitem *2.5) Parallel(lineitem 16 soft) \| Rows hin... |
| 17 | proposal_17 | 2950.08 | 0.97x |  | hint_error | Set(work_mem '512MB') Parallel(lineitem 16 soft) \| number... |
| 18 | proposal_18 | 3015.27 | 0.95x |  | hint_error | Rows(lineitem *3.0) \| Rows hint requires at least two rel... |
| 19 | proposal_19 | 3010.81 | 0.95x |  | ok |  |
| 20 | proposal_20 | 3058.19 | 0.94x |  | hint_error | Rows(lineitem *2.5) Parallel(lineitem 16 soft) \| Rows hin... |


### q07.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 5293.45 | 1.00x |  | ok |  |
| 1 | proposal_1 | 24489.19 | 0.22x |  | ok |  |
| 2 | proposal_2 | 6262.87 | 0.85x |  | ok |  |
| 3 | proposal_3 | 24870.76 | 0.21x |  | ok |  |
| 4 | proposal_4 | 5048.61 | 1.05x |  | hint_error | Unrecognized hint keyword "NoSort". \| pg_hint_plan: hint ... |
| 5 | proposal_5 | 4721.10 | 1.12x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 6 | proposal_6 | 15213.64 | 0.35x | Yes | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 7 | proposal_7 | 25608.48 | 0.21x |  | hint_error | Unrecognized hint keyword "NoParallel". \| pg_hint_plan: h... |
| 8 | proposal_8 | 15203.09 | 0.35x |  | ok |  |
| 9 | proposal_9 | 5354.90 | 0.99x |  | ok |  |
| 10 | proposal_10 | 8396.17 | 0.63x |  | ok |  |
| 11 | proposal_11 | 3595.35 | 1.47x |  | ok |  |
| 12 | proposal_12 | 5315.24 | 1.00x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 13 | proposal_13 | 5121.47 | 1.03x |  | ok |  |
| 14 | proposal_14 | 6133.25 | 0.86x |  | hint_error | Unrecognized hint keyword "BitmapAnd". Conflict scan meth... |
| 15 | proposal_15 | 5256.05 | 1.01x |  | ok |  |
| 16 | proposal_16 | 24044.54 | 0.22x |  | ok |  |
| 17 | proposal_17 | 5296.68 | 1.00x |  | ok |  |
| 18 | proposal_18 | 25505.91 | 0.21x |  | hint_error | Unrecognized hint keyword "NoParallel". \| pg_hint_plan: h... |
| 19 | proposal_19 | 3615.05 | 1.46x |  | ok |  |
| 20 | proposal_20 | 5668.53 | 0.93x |  | hint_error | Unrecognized hint keyword "NoParallel". \| pg_hint_plan: h... |


### q08.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1382.29 | 1.00x |  | ok |  |
| 1 | proposal_1 | 2035.54 | 0.68x | Yes | hint_error | Rows(part *0.01) \| Rows hint requires at least two relati... |
| 2 | proposal_2 | 2136.35 | 0.65x |  | hint_error | Rows(region *0.2) \| Rows hint requires at least two relat... |
| 3 | proposal_3 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 4 | proposal_4 | 1615.58 | 0.86x |  | hint_error | Unrecognized hint keyword "NoSort". \| pg_hint_plan: hint ... |
| 5 | proposal_5 | 4834.30 | 0.29x |  | ok |  |
| 6 | proposal_6 | 1580.09 | 0.87x |  | ok |  |
| 7 | proposal_7 | 1529.28 | 0.90x |  | hint_error | Rows(customer *0.01) \| Rows hint requires at least two re... |
| 8 | proposal_8 | 4062.93 | 0.34x |  | ok |  |
| 9 | proposal_9 | 1493.77 | 0.93x |  | hint_error | Rows(supplier *0.05) \| Rows hint requires at least two re... |
| 10 | proposal_10 | 1775.37 | 0.78x |  | ok |  |
| 11 | proposal_11 | 4619.70 | 0.30x |  | ok |  |
| 12 | proposal_12 | 1570.55 | 0.88x |  | hint_error | Rows(part *0.01) \| Rows hint requires at least two relati... |
| 13 | proposal_13 | 20282.65 | 0.07x |  | ok |  |
| 14 | proposal_14 | 1511.29 | 0.91x |  | hint_error | Unrecognized hint keyword "NoSort". \| pg_hint_plan: hint ... |
| 15 | proposal_15 | 3617.49 | 0.38x |  | ok |  |
| 16 | proposal_16 | 1579.34 | 0.88x |  | hint_error | Rows(customer *0.01) \| Rows hint requires at least two re... |
| 17 | proposal_17 | 1651.23 | 0.84x |  | ok |  |
| 18 | proposal_18 | 1770.47 | 0.78x |  | ok |  |
| 19 | proposal_19 | 4758.19 | 0.29x |  | ok |  |
| 20 | proposal_20 | 20189.72 | 0.07x |  | ok |  |


### q09.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 8533.38 | 1.00x |  | ok |  |
| 1 | proposal_1 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 2 | proposal_2 | 12491.15 | 0.68x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 3 | proposal_3 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 4 | proposal_4 | 9159.97 | 0.93x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 5 | proposal_5 | 8300.18 | 1.03x |  | ok |  |
| 6 | proposal_6 | 7150.71 | 1.19x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 7 | proposal_7 | 26931.81 | 0.32x |  | hint_error | Rows(part #27196) \| Rows hint requires at least two relat... |
| 8 | proposal_8 | 8786.18 | 0.97x |  | hint_error | Unrecognized hint keyword "NoSort". \| pg_hint_plan: hint ... |
| 9 | proposal_9 | 8768.42 | 0.97x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 10 | proposal_10 | 8569.31 | 1.00x |  | ok |  |
| 11 | proposal_11 | 8919.15 | 0.96x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 12 | proposal_12 | 8684.98 | 0.98x |  | ok |  |
| 13 | proposal_13 | 8568.40 | 1.00x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 14 | proposal_14 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 15 | proposal_15 | 9219.26 | 0.93x |  | ok |  |
| 16 | proposal_16 | 8732.01 | 0.98x |  | ok |  |
| 17 | proposal_17 | 8516.46 | 1.00x |  | hint_error | Unrecognized hint keyword "NoSort". \| pg_hint_plan: hint ... |
| 18 | proposal_18 | 8639.81 | 0.99x |  | ok |  |
| 19 | proposal_19 | 12018.40 | 0.71x |  | ok |  |
| 20 | proposal_20 | timeout | N/A | Yes | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |


### q10.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 5748.24 | 1.00x |  | ok |  |
| 1 | proposal_1 | 5895.65 | 0.97x | Yes | hint_error | Rows(orders *0.24) \| Rows hint requires at least two rela... |
| 2 | proposal_2 | 5550.33 | 1.04x |  | hint_error | Rows(lineitem *0.15) \| Rows hint requires at least two re... |
| 3 | proposal_3 | 5805.25 | 0.99x |  | hint_error | Closing parenthesis is necessary. \| pg_hint_plan: hint sy... |
| 4 | proposal_4 | 3692.33 | 1.56x |  | ok |  |
| 5 | proposal_5 | 5458.34 | 1.05x |  | ok |  |
| 6 | proposal_6 | 3765.17 | 1.53x |  | ok |  |
| 7 | proposal_7 | 3643.01 | 1.58x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 8 | proposal_8 | 5616.46 | 1.02x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 9 | proposal_9 | 9584.59 | 0.60x |  | ok |  |
| 10 | proposal_10 | 6957.42 | 0.83x |  | ok |  |
| 11 | proposal_11 | 5842.08 | 0.98x |  | ok |  |
| 12 | proposal_12 | 3686.52 | 1.56x |  | ok |  |
| 13 | proposal_13 | 5675.29 | 1.01x |  | hint_error | Rows(orders *0.24) Rows(lineitem *0.15) \| Rows hint requi... |
| 14 | proposal_14 | 9353.88 | 0.61x |  | ok |  |
| 15 | proposal_15 | 6671.19 | 0.86x |  | ok |  |
| 16 | proposal_16 | 3700.11 | 1.55x |  | ok |  |
| 17 | proposal_17 | 5871.56 | 0.98x |  | ok |  |
| 18 | proposal_18 | 3733.81 | 1.54x |  | ok |  |
| 19 | proposal_19 | 6536.87 | 0.88x |  | ok |  |
| 20 | proposal_20 | 5897.34 | 0.97x |  | hint_error | Rows(orders *0.24) \| Rows hint requires at least two rela... |


### q11.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1867.09 | 1.00x |  | ok |  |
| 1 | proposal_1 | 2064.51 | 0.90x | Yes | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 2 | proposal_2 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 3 | proposal_3 | 8144.80 | 0.23x |  | ok |  |
| 4 | proposal_4 | 1817.74 | 1.03x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 5 | proposal_5 | 1978.24 | 0.94x |  | ok |  |
| 6 | proposal_6 | 1802.38 | 1.04x |  | ok |  |
| 7 | proposal_7 | 1959.44 | 0.95x |  | ok |  |
| 8 | proposal_8 | 1805.84 | 1.03x |  | ok |  |
| 9 | proposal_9 | 1800.43 | 1.04x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 10 | proposal_10 | 1813.53 | 1.03x |  | ok |  |
| 11 | proposal_11 | 1804.42 | 1.03x |  | ok |  |
| 12 | proposal_12 | 1820.79 | 1.03x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 13 | proposal_13 | 2069.30 | 0.90x |  | ok |  |
| 14 | proposal_14 | 7910.18 | 0.24x |  | ok |  |
| 15 | proposal_15 | 1815.55 | 1.03x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 16 | proposal_16 | 1816.87 | 1.03x |  | ok |  |
| 17 | proposal_17 | 1816.80 | 1.03x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 18 | proposal_18 | 1716.50 | 1.09x |  | ok |  |
| 19 | proposal_19 | 1734.83 | 1.08x |  | ok |  |
| 20 | proposal_20 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |


### q12.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 3611.89 | 1.00x |  | ok |  |
| 1 | proposal_1 | 5049.61 | 0.72x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 2 | proposal_2 | 4958.59 | 0.73x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 3 | proposal_3 | 5798.61 | 0.62x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 4 | proposal_4 | 11449.05 | 0.32x |  | hint_error | Rows(orders *0.0001) \| Rows hint requires at least two re... |
| 5 | proposal_5 | 6749.63 | 0.54x |  | ok |  |
| 6 | proposal_6 | 4938.32 | 0.73x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 7 | proposal_7 | 6750.47 | 0.54x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 8 | proposal_8 | 3514.28 | 1.03x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 9 | proposal_9 | 6036.79 | 0.60x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 10 | proposal_10 | 4337.22 | 0.83x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 11 | proposal_11 | 4786.07 | 0.75x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 12 | proposal_12 | 4972.05 | 0.73x |  | ok |  |
| 13 | proposal_13 | 4873.37 | 0.74x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 14 | proposal_14 | 6156.45 | 0.59x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 15 | proposal_15 | 9276.41 | 0.39x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 16 | proposal_16 | 4361.16 | 0.83x |  | ok |  |
| 17 | proposal_17 | 4398.42 | 0.82x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 18 | proposal_18 | 6008.39 | 0.60x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 19 | proposal_19 | 11822.88 | 0.31x |  | hint_error | Rows(orders *0.0001) \| Rows hint requires at least two re... |
| 20 | proposal_20 | 4347.32 | 0.83x | Yes | hint_error | Set(work_mem '256MB') Rows(lineitem *0.001) \| Rows hint r... |


### q13.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 5727.36 | 1.00x |  | ok |  |
| 1 | proposal_1 | 5774.97 | 0.99x | Yes | ok |  |
| 2 | proposal_2 | 25891.07 | 0.22x |  | ok |  |
| 3 | proposal_3 | 22681.87 | 0.25x |  | ok |  |
| 4 | proposal_4 | 3906.18 | 1.47x |  | ok |  |
| 5 | proposal_5 | 15697.65 | 0.36x |  | ok |  |
| 6 | proposal_6 | 15476.50 | 0.37x |  | ok |  |
| 7 | proposal_7 | 15747.64 | 0.36x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 8 | proposal_8 | 6067.19 | 0.94x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 9 | proposal_9 | 5789.93 | 0.99x |  | ok |  |
| 10 | proposal_10 | 5629.83 | 1.02x |  | ok |  |
| 11 | proposal_11 | 5599.74 | 1.02x |  | ok |  |
| 12 | proposal_12 | 15830.70 | 0.36x |  | ok |  |
| 13 | proposal_13 | 15502.21 | 0.37x |  | hint_error | Leading(((customer) orders)) \| Leading hint requires two ... |
| 14 | proposal_14 | 22393.98 | 0.26x |  | ok |  |
| 15 | proposal_15 | 24702.26 | 0.23x |  | ok |  |
| 16 | proposal_16 | 15556.22 | 0.37x |  | ok |  |
| 17 | proposal_17 | 5795.49 | 0.99x |  | ok |  |
| 18 | proposal_18 | 15995.69 | 0.36x |  | ok |  |
| 19 | proposal_19 | 22009.52 | 0.26x |  | ok |  |
| 20 | proposal_20 | 3184.52 | 1.80x |  | ok |  |


### q14.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1305.72 | 1.00x |  | ok |  |
| 1 | proposal_1 | 1113.17 | 1.17x | Yes | hint_error | Rows(lineitem *4.41) \| Rows hint requires at least two re... |
| 2 | proposal_2 | 1373.80 | 0.95x |  | ok |  |
| 3 | proposal_3 | 1195.64 | 1.09x |  | ok |  |
| 4 | proposal_4 | 1156.44 | 1.13x |  | ok |  |
| 5 | proposal_5 | 1164.69 | 1.12x |  | ok |  |
| 6 | proposal_6 | 1332.57 | 0.98x |  | hint_error | Unrecognized hint keyword "NoParallel". \| pg_hint_plan: h... |
| 7 | proposal_7 | 14606.47 | 0.09x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 8 | proposal_8 | 1200.13 | 1.09x |  | ok |  |
| 9 | proposal_9 | 14504.44 | 0.09x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 10 | proposal_10 | 1676.46 | 0.78x |  | ok |  |
| 11 | proposal_11 | 1130.70 | 1.15x |  | ok |  |
| 12 | proposal_12 | 1808.49 | 0.72x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 13 | proposal_13 | 1159.06 | 1.13x |  | ok |  |
| 14 | proposal_14 | 1127.41 | 1.16x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 15 | proposal_15 | 1109.93 | 1.18x |  | ok |  |
| 16 | proposal_16 | 1161.13 | 1.12x |  | ok |  |
| 17 | proposal_17 | 1174.99 | 1.11x |  | ok |  |
| 18 | proposal_18 | 1181.01 | 1.11x |  | ok |  |
| 19 | proposal_19 | 1149.62 | 1.14x |  | ok |  |
| 20 | proposal_20 | 1140.03 | 1.15x |  | ok |  |


### q15.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 2302.47 | 1.00x |  | ok |  |
| 1 | proposal_1 | 9464.96 | 0.24x |  | hint_error | Rows(revenue *0.98) \| Rows hint requires at least two rel... |
| 2 | proposal_2 | 3119.61 | 0.74x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 3 | proposal_3 | 2307.45 | 1.00x |  | hint_error | Set(work_mem '256MB') Rows(revenue *0.98) \| Rows hint req... |
| 4 | proposal_4 | 2378.61 | 0.97x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 5 | proposal_5 | 10717.26 | 0.21x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 6 | proposal_6 | 2467.23 | 0.93x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 7 | proposal_7 | 2386.70 | 0.96x |  | ok |  |
| 8 | proposal_8 | 2280.62 | 1.01x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 9 | proposal_9 | 9686.23 | 0.24x |  | hint_error | Set(effective_cache_size '16GB') \| Conflict join method h... |
| 10 | proposal_10 | 2339.95 | 0.98x |  | hint_error | Set(work_mem '256MB') \| Conflict scan method hint. \| pg_h... |
| 11 | proposal_11 | 2355.47 | 0.98x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 12 | proposal_12 | 2287.75 | 1.01x |  | ok |  |
| 13 | proposal_13 | 10689.41 | 0.22x |  | hint_error | Conflict join method hint. Conflict join method hint. \| p... |
| 14 | proposal_14 | 2501.67 | 0.92x |  | hint_error | Set(work_mem '256MB') Rows(revenue *0.98) \| Rows hint req... |
| 15 | proposal_15 | 9498.13 | 0.24x |  | hint_error | Set(effective_cache_size '32GB') \| Conflict scan method h... |
| 16 | proposal_16 | 2306.81 | 1.00x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 17 | proposal_17 | 2346.26 | 0.98x |  | hint_error | Set(work_mem '256MB') \| Conflict scan method hint. \| pg_h... |
| 18 | proposal_18 | 2283.93 | 1.01x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 19 | proposal_19 | 2309.55 | 1.00x |  | ok |  |
| 20 | proposal_20 | 9353.51 | 0.25x | Yes | hint_error | Set(work_mem '256MB') Rows(revenue *0.98) \| Rows hint req... |


### q16.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 1644.36 | 1.00x |  | ok |  |
| 1 | proposal_1 | 1996.43 | 0.82x |  | ok |  |
| 2 | proposal_2 | 2163.60 | 0.76x |  | ok |  |
| 3 | proposal_3 | 6874.88 | 0.24x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 4 | proposal_4 | 6971.78 | 0.24x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 5 | proposal_5 | 2753.57 | 0.60x |  | ok |  |
| 6 | proposal_6 | 2142.72 | 0.77x |  | ok |  |
| 7 | proposal_7 | 2794.06 | 0.59x |  | ok |  |
| 8 | proposal_8 | 2044.33 | 0.80x |  | ok |  |
| 9 | proposal_9 | 7507.16 | 0.22x |  | ok |  |
| 10 | proposal_10 | 2084.99 | 0.79x |  | ok |  |
| 11 | proposal_11 | 2131.37 | 0.77x | Yes | ok |  |
| 12 | proposal_12 | 2427.82 | 0.68x |  | ok |  |
| 13 | proposal_13 | 1621.39 | 1.01x |  | hint_error | Zero-length delimited string. \| pg_hint_plan: hint syntax... |
| 14 | proposal_14 | 2461.67 | 0.67x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 15 | proposal_15 | 2153.80 | 0.76x |  | ok |  |
| 16 | proposal_16 | 6871.45 | 0.24x |  | hint_error | Rows(supplier *5.6) \| Rows hint requires at least two rel... |
| 17 | proposal_17 | 2934.67 | 0.56x |  | ok |  |
| 18 | proposal_18 | 2039.59 | 0.81x |  | ok |  |
| 19 | proposal_19 | 2490.57 | 0.66x |  | ok |  |
| 20 | proposal_20 | 7365.25 | 0.22x |  | ok |  |


### q17.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 11283.05 | 1.00x |  | ok |  |
| 1 | proposal_1 | 23439.87 | 0.48x | Yes | hint_error | Rows(part *100) \| Rows hint requires at least two relatio... |
| 2 | proposal_2 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 3 | proposal_3 | 22011.71 | 0.51x |  | ok |  |
| 4 | proposal_4 | 11291.75 | 1.00x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 5 | proposal_5 | 11406.34 | 0.99x |  | hint_error | Rows(lineitem *0.001) \| Rows hint requires at least two r... |
| 6 | proposal_6 | 11370.45 | 0.99x |  | ok |  |
| 7 | proposal_7 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 8 | proposal_8 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 9 | proposal_9 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 10 | proposal_10 | 11190.19 | 1.01x |  | ok |  |
| 11 | proposal_11 | 11432.01 | 0.99x |  | ok |  |
| 12 | proposal_12 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 13 | proposal_13 | 11188.57 | 1.01x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 14 | proposal_14 | 11562.24 | 0.98x |  | ok |  |
| 15 | proposal_15 | 11433.06 | 0.99x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 16 | proposal_16 | 1507.78 | 7.48x |  | ok |  |
| 17 | proposal_17 | 11549.39 | 0.98x |  | ok |  |
| 18 | proposal_18 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 19 | proposal_19 | 10714.92 | 1.05x |  | ok |  |
| 20 | proposal_20 | 11271.34 | 1.00x |  | ok |  |


### q18.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 40385.33 | 1.00x |  | ok |  |
| 1 | proposal_1 | 21545.81 | 1.87x | Yes | hint_error | Rows(lineitem *0.0047) \| Rows hint requires at least two ... |
| 2 | proposal_2 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 3 | proposal_3 | 22743.47 | 1.78x |  | ok |  |
| 4 | proposal_4 | 55142.81 | 0.73x |  | ok |  |
| 5 | proposal_5 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 6 | proposal_6 | 32308.34 | 1.25x |  | ok |  |
| 7 | proposal_7 | 21535.47 | 1.88x |  | ok |  |
| 8 | proposal_8 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 9 | proposal_9 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 10 | proposal_10 | 27140.29 | 1.49x |  | hint_error | Rows(lineitem *0.0047) \| Rows hint requires at least two ... |
| 11 | proposal_11 | 21048.08 | 1.92x |  | ok |  |
| 12 | proposal_12 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 13 | proposal_13 | 21125.94 | 1.91x |  | ok |  |
| 14 | proposal_14 | 32176.46 | 1.26x |  | ok |  |
| 15 | proposal_15 | 21240.97 | 1.90x |  | ok |  |
| 16 | proposal_16 | 21557.01 | 1.87x |  | hint_error | Rows(orders *0.1) \| Rows hint requires at least two relat... |
| 17 | proposal_17 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  a... |
| 18 | proposal_18 | 21230.17 | 1.90x |  | ok |  |
| 19 | proposal_19 | 32126.49 | 1.26x |  | ok |  |
| 20 | proposal_20 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |


### q19.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 867.00 | 1.00x |  | ok |  |
| 1 | proposal_1 | 861.25 | 1.01x |  | hint_error | Rows(part *0.1) \| Rows hint requires at least two relatio... |
| 2 | proposal_2 | 13745.89 | 0.06x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 3 | proposal_3 | 912.81 | 0.95x |  | hint_error | Set(work_mem '64MB') \| Conflict scan method hint. \| pg_hi... |
| 4 | proposal_4 | 13880.79 | 0.06x |  | ok |  |
| 5 | proposal_5 | 908.62 | 0.95x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 6 | proposal_6 | 13868.76 | 0.06x |  | hint_error | Rows(part *0.1) \| Rows hint requires at least two relatio... |
| 7 | proposal_7 | 13387.42 | 0.06x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 8 | proposal_8 | 365.10 | 2.37x |  | hint_error | Set(work_mem '128MB') \| Conflict scan method hint. \| pg_h... |
| 9 | proposal_9 | 3498.81 | 0.25x |  | ok |  |
| 10 | proposal_10 | 3318.06 | 0.26x |  | ok |  |
| 11 | proposal_11 | 328.87 | 2.64x |  | hint_error | Rows(part *0.1) \| Rows hint requires at least two relatio... |
| 12 | proposal_12 | 328.98 | 2.64x |  | hint_error | Rows(part *0.1) \| Rows hint requires at least two relatio... |
| 13 | proposal_13 | 348.81 | 2.49x |  | ok |  |
| 14 | proposal_14 | 15616.89 | 0.06x |  | ok |  |
| 15 | proposal_15 | 344.82 | 2.51x |  | ok |  |
| 16 | proposal_16 | 3454.85 | 0.25x |  | ok |  |
| 17 | proposal_17 | 348.06 | 2.49x |  | hint_error | Rows(part *0.1) \| Rows hint requires at least two relatio... |
| 18 | proposal_18 | 3327.44 | 0.26x |  | ok |  |
| 19 | proposal_19 | 3330.33 | 0.26x |  | ok |  |
| 20 | proposal_20 | 16009.64 | 0.05x | Yes | ok |  |


### q20.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 6657.67 | 1.00x |  | ok |  |
| 1 | proposal_1 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 2 | proposal_2 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 3 | proposal_3 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 4 | proposal_4 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 5 | proposal_5 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 6 | proposal_6 | 6446.09 | 1.03x |  | ok |  |
| 7 | proposal_7 | 6422.41 | 1.04x |  | hint_error | Unrecognized hint keyword "NoParallel". \| pg_hint_plan: h... |
| 8 | proposal_8 | 6426.74 | 1.04x | Yes | hint_error | Leading((nation supplier (partsupp_filtered lineitem))) S... |
| 9 | proposal_9 | 6449.69 | 1.03x |  | hint_error | Unrecognized hint keyword "NoSort". \| pg_hint_plan: hint ... |
| 10 | proposal_10 | 6744.98 | 0.99x |  | ok |  |
| 11 | proposal_11 | 6612.75 | 1.01x |  | hint_error | Zero-length delimited string. \| pg_hint_plan: hint syntax... |
| 12 | proposal_12 | 6425.06 | 1.04x |  | hint_error | Unrecognized hint keyword "BitmapAnd". \| pg_hint_plan: hi... |
| 13 | proposal_13 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): NOTICE:  p... |
| 14 | proposal_14 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 15 | proposal_15 | 6590.64 | 1.01x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 16 | proposal_16 | 6474.84 | 1.03x |  | hint_error | Zero-length delimited string. \| pg_hint_plan: hint syntax... |
| 17 | proposal_17 | 6500.09 | 1.02x |  | ok |  |
| 18 | proposal_18 | 6668.08 | 1.00x |  | ok |  |
| 19 | proposal_19 | timeout | N/A |  | timeout | query execution exceeded 60s timeout (killed): INFO:  pg_... |
| 20 | proposal_20 | 13516.10 | 0.49x |  | hint_error | Set(work_mem '128MB') Rows(part #21551) \| Rows hint requi... |


### q21.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 8879.33 | 1.00x |  | ok |  |
| 1 | proposal_1 | 9547.37 | 0.93x | Yes | hint_error | Leading((nation (supplier (lineitem l1 orders)))) \| Leadi... |
| 2 | proposal_2 | 9328.10 | 0.95x |  | hint_error | Parallel(lineitem l1 soft) \| number of workers must be a ... |
| 3 | proposal_3 | 9542.72 | 0.93x |  | hint_error | Leading(((nation supplier) (lineitem l2 lineitem l3) (ord... |
| 4 | proposal_4 | 11186.57 | 0.79x |  | hint_error | Set(work_mem '256MB') Parallel(lineitem l1 soft) \| number... |
| 5 | proposal_5 | 8681.56 | 1.02x |  | hint_error | Parallel(lineitem l2 soft) Parallel(lineitem l3 soft) \| n... |
| 6 | proposal_6 | 9503.28 | 0.93x |  | hint_error | Leading((nation (supplier (lineitem l1 orders)))) Rows(na... |
| 7 | proposal_7 | 7045.21 | 1.26x |  | hint_error | Parallel(lineitem l1 soft) \| number of workers must be a ... |
| 8 | proposal_8 | 8915.27 | 1.00x |  | ok |  |
| 9 | proposal_9 | 9587.30 | 0.93x |  | hint_error | Parallel(lineitem l1 soft) \| number of workers must be a ... |
| 10 | proposal_10 | 8481.62 | 1.05x |  | ok |  |
| 11 | proposal_11 | 8008.18 | 1.11x |  | hint_error | Parallel(lineitem l1 soft) \| number of workers must be a ... |
| 12 | proposal_12 | 7459.05 | 1.19x |  | hint_error | Rows(orders *0.01) \| Rows hint requires at least two rela... |
| 13 | proposal_13 | 9003.07 | 0.99x |  | hint_error | Set(work_mem '1GB') Parallel(lineitem l1 soft) \| number o... |
| 14 | proposal_14 | 8961.59 | 0.99x |  | hint_error | Parallel(lineitem l1 soft) \| number of workers must be a ... |
| 15 | proposal_15 | 9653.40 | 0.92x |  | hint_error | NoSeqScan(lineitem l1) \| NoSeqScan hint accepts only one ... |
| 16 | proposal_16 | 10680.90 | 0.83x |  | ok |  |
| 17 | proposal_17 | 8786.47 | 1.01x |  | hint_error | Parallel(lineitem l1 soft) \| number of workers must be a ... |
| 18 | proposal_18 | 10532.42 | 0.84x |  | hint_error | NoBitmapScan(lineitem l1) NoBitmapScan(lineitem l2) NoBit... |
| 19 | proposal_19 | 16697.63 | 0.53x |  | hint_error | Parallel(lineitem l1 soft) \| number of workers must be a ... |
| 20 | proposal_20 | 8303.46 | 1.07x |  | hint_error | Set(effective_cache_size '16GB') Parallel(lineitem l1 sof... |


### q22.sql

| Proposal ID | Label | Elapsed (ms) | Speedup | AgentRankBest | Status | Error |
|---|---|---|---|---|---|---|
| 0 | baseline | 894.32 | 1.00x |  | ok |  |
| 1 | proposal_1 | 3836.97 | 0.23x |  | ok |  |
| 2 | proposal_2 | 870.11 | 1.03x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 3 | proposal_3 | 3616.90 | 0.25x |  | ok |  |
| 4 | proposal_4 | 3519.90 | 0.25x |  | hint_error | Rows(customer_1 *0.65) \| Rows hint requires at least two ... |
| 5 | proposal_5 | 3691.96 | 0.24x |  | hint_error | Set(merge_cost_factor 0.5) \| Conflict join method hint. \|... |
| 6 | proposal_6 | 964.75 | 0.93x |  | hint_error | Rows(customer *0.05) \| Rows hint requires at least two re... |
| 7 | proposal_7 | 3745.38 | 0.24x |  | hint_error | Conflict join method hint. \| pg_hint_plan: hint syntax er... |
| 8 | proposal_8 | 946.88 | 0.94x |  | ok |  |
| 9 | proposal_9 | 1176.77 | 0.76x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 10 | proposal_10 | 3784.21 | 0.24x |  | ok |  |
| 11 | proposal_11 | 3083.08 | 0.29x |  | hint_error | Unrecognized hint keyword "NoParallel". \| pg_hint_plan: h... |
| 12 | proposal_12 | 892.79 | 1.00x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 13 | proposal_13 | 854.02 | 1.05x |  | ok |  |
| 14 | proposal_14 | 6928.34 | 0.13x |  | ok |  |
| 15 | proposal_15 | 877.08 | 1.02x |  | ok |  |
| 16 | proposal_16 | 904.64 | 0.99x |  | ok |  |
| 17 | proposal_17 | 1133.14 | 0.79x |  | hint_error | Conflict scan method hint. \| pg_hint_plan: hint syntax er... |
| 18 | proposal_18 | 3864.93 | 0.23x |  | ok |  |
| 19 | proposal_19 | 778.04 | 1.15x |  | hint_error | Conflict scan method hint. Conflict scan method hint. \| p... |
| 20 | proposal_20 | 3910.90 | 0.23x | Yes | ok |  |
