# Etapa 2 — correções de leitura (bootstrap, B1R_lag, padrão temporal)

Bootstrap de escolas: 1000 reamostragens pareadas por ano; intervalo 95% (percentis).
B1R_lag = baseline principal (abandono de t−1, disponível na decisão).
B1R = limite superior otimista (abandono de t, publicado depois do fim de t+1).
2025 não avaliado (teste bloqueado, D7).

## Largura mediana do intervalo 95% (Cenário B, modelos)

| etapa | metrica | larg |
|---|---|---|
| AF | Rec@10 | 0.3 |
| AF | Rec@20 | 0.22 |
| EM | Rec@10 | 0.31 |
| EM | Rec@20 | 0.25 |

## Cenário B — Rec@10 com intervalo 95%

| id | AF 2021 | AF 2022 | AF 2023 | AF 2024 | EM 2021 | EM 2022 | EM 2023 | EM 2024 |
|---|---|---|---|---|---|---|---|---|
| B1R | 0.17 [0.04, 0.32] | 0.17 [0.04, 0.31] | 0.35 [0.17, 0.57] | 0.46 [0.25, 0.60] | 0.06 [0.00, 0.25] | 0.38 [0.19, 0.56] | 0.32 [0.12, 0.53] | 0.18 [0.06, 0.37] |
| B1R_lag | 0.09 [0.00, 0.26] | 0.17 [0.04, 0.33] | 0.22 [0.04, 0.37] | 0.25 [0.08, 0.43] | 0.25 [0.06, 0.44] | 0.06 [0.00, 0.12] | 0.35 [0.12, 0.53] | 0.15 [0.00, 0.35] |
| B2 | 0.10 [0.10, 0.10] | 0.04 [0.00, 0.10] | 0.13 [0.10, 0.16] | 0.14 [0.11, 0.16] | 0.09 [0.07, 0.10] | 0.04 [0.00, 0.10] | 0.14 [0.11, 0.16] | 0.14 [0.11, 0.16] |
| B/Ridge b1 | 0.30 [0.09, 0.48] | 0.33 [0.17, 0.50] | 0.26 [0.09, 0.43] | 0.21 [0.08, 0.38] | 0.19 [0.00, 0.33] | 0.12 [0.00, 0.31] | 0.06 [0.00, 0.24] | 0.18 [0.00, 0.35] |
| B/Árvore b1 | 0.24 [0.09, 0.40] | 0.18 [0.06, 0.33] | 0.28 [0.12, 0.45] | 0.14 [0.02, 0.27] | 0.14 [0.00, 0.25] | 0.13 [0.07, 0.25] | 0.07 [0.00, 0.16] | 0.08 [0.00, 0.21] |
| B/Ridge b2 | 0.22 [0.04, 0.39] | 0.29 [0.12, 0.46] | 0.26 [0.09, 0.48] | 0.21 [0.08, 0.40] | 0.19 [0.00, 0.31] | 0.25 [0.06, 0.50] | 0.24 [0.00, 0.41] | 0.24 [0.00, 0.41] |
| B/Árvore b2 | 0.24 [0.10, 0.37] | 0.18 [0.06, 0.34] | 0.14 [0.05, 0.27] | 0.23 [0.11, 0.36] | 0.24 [0.05, 0.38] | 0.13 [0.10, 0.17] | 0.14 [0.05, 0.22] | 0.09 [0.00, 0.23] |
| B/Ridge b3 | 0.22 [0.04, 0.39] | 0.29 [0.12, 0.46] | 0.35 [0.17, 0.57] | 0.29 [0.10, 0.42] | 0.19 [0.00, 0.31] | 0.25 [0.06, 0.50] | 0.29 [0.06, 0.41] | 0.20 [0.00, 0.41] |
| B/Árvore b3 | 0.24 [0.10, 0.37] | 0.18 [0.06, 0.34] | 0.19 [0.12, 0.29] | 0.22 [0.10, 0.35] | 0.24 [0.05, 0.38] | 0.13 [0.10, 0.17] | 0.15 [0.10, 0.17] | 0.15 [0.11, 0.18] |
| B/Ridge b4 | 0.17 [0.04, 0.35] | 0.25 [0.12, 0.42] | 0.30 [0.17, 0.52] | 0.25 [0.12, 0.42] | 0.12 [0.00, 0.25] | 0.31 [0.06, 0.50] | 0.29 [0.06, 0.41] | 0.18 [0.00, 0.35] |
| B/Árvore b4 | 0.24 [0.10, 0.37] | 0.19 [0.05, 0.35] | 0.19 [0.12, 0.29] | 0.22 [0.10, 0.35] | 0.18 [0.00, 0.32] | 0.12 [0.10, 0.16] | 0.15 [0.10, 0.17] | 0.15 [0.11, 0.18] |

## Cenário B — Rec@20 com intervalo 95%

| id | AF 2021 | AF 2022 | AF 2023 | AF 2024 | EM 2021 | EM 2022 | EM 2023 | EM 2024 |
|---|---|---|---|---|---|---|---|---|
| B1R | 0.27 [0.15, 0.38] | 0.38 [0.26, 0.51] | 0.44 [0.30, 0.57] | 0.43 [0.31, 0.56] | 0.17 [0.06, 0.28] | 0.47 [0.28, 0.61] | 0.33 [0.21, 0.48] | 0.39 [0.26, 0.55] |
| B1R_lag | 0.30 [0.19, 0.41] | 0.34 [0.23, 0.47] | 0.35 [0.20, 0.46] | 0.42 [0.29, 0.52] | 0.22 [0.12, 0.38] | 0.06 [0.00, 0.21] | 0.27 [0.15, 0.43] | 0.35 [0.20, 0.50] |
| B2 | 0.20 [0.20, 0.20] | 0.07 [0.03, 0.14] | 0.24 [0.21, 0.29] | 0.26 [0.21, 0.29] | 0.19 [0.18, 0.20] | 0.07 [0.02, 0.15] | 0.26 [0.22, 0.29] | 0.28 [0.24, 0.32] |
| B/Ridge b1 | 0.49 [0.34, 0.57] | 0.47 [0.34, 0.57] | 0.26 [0.15, 0.40] | 0.39 [0.27, 0.48] | 0.19 [0.09, 0.38] | 0.28 [0.16, 0.44] | 0.19 [0.09, 0.33] | 0.32 [0.15, 0.44] |
| B/Árvore b1 | 0.32 [0.23, 0.40] | 0.32 [0.23, 0.42] | 0.29 [0.21, 0.39] | 0.29 [0.19, 0.40] | 0.18 [0.09, 0.32] | 0.35 [0.23, 0.46] | 0.17 [0.08, 0.31] | 0.20 [0.11, 0.31] |
| B/Ridge b2 | 0.38 [0.26, 0.48] | 0.45 [0.30, 0.53] | 0.37 [0.22, 0.48] | 0.44 [0.31, 0.53] | 0.22 [0.09, 0.38] | 0.34 [0.19, 0.47] | 0.21 [0.09, 0.39] | 0.41 [0.24, 0.53] |
| B/Árvore b2 | 0.40 [0.28, 0.48] | 0.39 [0.27, 0.49] | 0.35 [0.23, 0.44] | 0.38 [0.25, 0.47] | 0.20 [0.10, 0.35] | 0.29 [0.25, 0.34] | 0.21 [0.11, 0.33] | 0.27 [0.19, 0.35] |
| B/Ridge b3 | 0.38 [0.26, 0.48] | 0.45 [0.30, 0.53] | 0.42 [0.28, 0.54] | 0.39 [0.27, 0.52] | 0.22 [0.09, 0.38] | 0.34 [0.19, 0.47] | 0.36 [0.18, 0.48] | 0.38 [0.21, 0.50] |
| B/Árvore b3 | 0.40 [0.28, 0.48] | 0.39 [0.27, 0.49] | 0.36 [0.24, 0.45] | 0.35 [0.24, 0.45] | 0.20 [0.10, 0.35] | 0.29 [0.25, 0.34] | 0.25 [0.20, 0.29] | 0.28 [0.22, 0.33] |
| B/Ridge b4 | 0.36 [0.22, 0.48] | 0.40 [0.27, 0.52] | 0.38 [0.26, 0.52] | 0.42 [0.29, 0.53] | 0.16 [0.08, 0.34] | 0.31 [0.19, 0.47] | 0.36 [0.18, 0.48] | 0.38 [0.26, 0.53] |
| B/Árvore b4 | 0.41 [0.29, 0.49] | 0.40 [0.28, 0.49] | 0.36 [0.24, 0.45] | 0.35 [0.24, 0.45] | 0.25 [0.12, 0.37] | 0.28 [0.24, 0.33] | 0.25 [0.20, 0.29] | 0.28 [0.22, 0.33] |

## Decisões — Cenário B

| cenario | etapa | modelo | bloco | referencia | Rec@10 pontual | Rec@10 IC>0 | Rec@10 IC<0 | Rec@20 pontual | Rec@20 IC>0 | Rec@20 IC<0 | decisao |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B | AF | arvore | 1 | B1R | 2/4 | 0/4 | 1/4 | 1/4 | 0/4 | 0/4 | não |
| B | AF | arvore | 2 | B1R | 2/4 | 0/4 | 1/4 | 2/4 | 0/4 | 0/4 | não |
| B | AF | arvore | 3 | B1R | 2/4 | 0/4 | 1/4 | 2/4 | 0/4 | 0/4 | não |
| B | AF | arvore | 4 | B1R | 2/4 | 0/4 | 1/4 | 2/4 | 0/4 | 0/4 | não |
| B | AF | ridge | 1 | B1R | 2/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| B | AF | ridge | 2 | B1R | 2/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | não |
| B | AF | ridge | 3 | B1R | 2/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| B | AF | ridge | 4 | B1R | 1/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| B | EM | arvore | 1 | B1R | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 1/4 | não |
| B | EM | arvore | 2 | B1R | 1/4 | 0/4 | 1/4 | 1/4 | 0/4 | 0/4 | não |
| B | EM | arvore | 3 | B1R | 1/4 | 0/4 | 1/4 | 1/4 | 0/4 | 0/4 | não |
| B | EM | arvore | 4 | B1R | 1/4 | 0/4 | 1/4 | 1/4 | 0/4 | 0/4 | não |
| B | EM | ridge | 1 | B1R | 1/4 | 0/4 | 1/4 | 1/4 | 0/4 | 0/4 | não |
| B | EM | ridge | 2 | B1R | 2/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| B | EM | ridge | 3 | B1R | 2/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| B | EM | ridge | 4 | B1R | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| B | AF | arvore | 1 | B1R_lag | 3/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| B | AF | arvore | 2 | B1R_lag | 2/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | não |
| B | AF | arvore | 3 | B1R_lag | 2/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | não |
| B | AF | arvore | 4 | B1R_lag | 2/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | não |
| B | AF | ridge | 1 | B1R_lag | 3/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| B | AF | ridge | 2 | B1R_lag | 3/4 | 0/4 | 0/4 | 4/4 | 0/4 | 0/4 | indeterminado |
| B | AF | ridge | 3 | B1R_lag | 4/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | indeterminado |
| B | AF | ridge | 4 | B1R_lag | 3/4 | 0/4 | 0/4 | 4/4 | 0/4 | 0/4 | indeterminado |
| B | EM | arvore | 1 | B1R_lag | 1/4 | 0/4 | 0/4 | 1/4 | 1/4 | 0/4 | não |
| B | EM | arvore | 2 | B1R_lag | 1/4 | 0/4 | 0/4 | 1/4 | 1/4 | 0/4 | não |
| B | EM | arvore | 3 | B1R_lag | 2/4 | 0/4 | 0/4 | 1/4 | 1/4 | 0/4 | não |
| B | EM | arvore | 4 | B1R_lag | 2/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| B | EM | ridge | 1 | B1R_lag | 2/4 | 0/4 | 0/4 | 1/4 | 1/4 | 0/4 | não |
| B | EM | ridge | 2 | B1R_lag | 2/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| B | EM | ridge | 3 | B1R_lag | 2/4 | 0/4 | 0/4 | 3/4 | 1/4 | 0/4 | não |
| B | EM | ridge | 4 | B1R_lag | 2/4 | 0/4 | 0/4 | 3/4 | 1/4 | 0/4 | não |
| B | AF | arvore | 1 | B2 | 4/4 | 0/4 | 0/4 | 4/4 | 2/4 | 0/4 | indeterminado |
| B | AF | arvore | 2 | B2 | 4/4 | 1/4 | 0/4 | 4/4 | 3/4 | 0/4 | indeterminado |
| B | AF | arvore | 3 | B2 | 4/4 | 1/4 | 0/4 | 4/4 | 2/4 | 0/4 | indeterminado |
| B | AF | arvore | 4 | B2 | 4/4 | 1/4 | 0/4 | 4/4 | 2/4 | 0/4 | indeterminado |
| B | AF | ridge | 1 | B2 | 4/4 | 1/4 | 0/4 | 4/4 | 3/4 | 0/4 | indeterminado |
| B | AF | ridge | 2 | B2 | 4/4 | 1/4 | 0/4 | 4/4 | 3/4 | 0/4 | indeterminado |
| B | AF | ridge | 3 | B2 | 4/4 | 2/4 | 0/4 | 4/4 | 4/4 | 0/4 | indeterminado |
| B | AF | ridge | 4 | B2 | 4/4 | 2/4 | 0/4 | 4/4 | 4/4 | 0/4 | indeterminado |
| B | EM | arvore | 1 | B2 | 2/4 | 1/4 | 0/4 | 1/4 | 1/4 | 0/4 | não |
| B | EM | arvore | 2 | B2 | 3/4 | 1/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| B | EM | arvore | 3 | B2 | 4/4 | 1/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| B | EM | arvore | 4 | B2 | 4/4 | 1/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| B | EM | ridge | 1 | B2 | 3/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| B | EM | ridge | 2 | B2 | 4/4 | 1/4 | 0/4 | 3/4 | 1/4 | 0/4 | indeterminado |
| B | EM | ridge | 3 | B2 | 4/4 | 1/4 | 0/4 | 4/4 | 1/4 | 0/4 | indeterminado |
| B | EM | ridge | 4 | B2 | 4/4 | 1/4 | 0/4 | 3/4 | 1/4 | 0/4 | indeterminado |
| B | AF | arvore | 2 | bloco 1 | 3/4 | 0/4 | 0/4 | 4/4 | 0/4 | 0/4 | indeterminado |
| B | AF | ridge | 2 | bloco 1 | 0/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| B | EM | arvore | 2 | bloco 1 | 3/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | indeterminado |
| B | EM | ridge | 2 | bloco 1 | 3/4 | 0/4 | 0/4 | 4/4 | 0/4 | 0/4 | indeterminado |
| B | AF | arvore | 3 | bloco 2 | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| B | AF | ridge | 3 | bloco 2 | 2/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| B | EM | arvore | 3 | bloco 2 | 2/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| B | EM | ridge | 3 | bloco 2 | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| B | AF | arvore | 4 | bloco 3 | 1/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| B | AF | ridge | 4 | bloco 3 | 0/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| B | EM | arvore | 4 | bloco 3 | 0/4 | 0/4 | 1/4 | 1/4 | 0/4 | 0/4 | não |
| B | EM | ridge | 4 | bloco 3 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | não |

## Padrão temporal contra o B1R (M = modelo vence, B = B1R vence, ? = intervalo cruza zero)

| etapa | modelo | bloco | metrica | pontual 21-22-23-24 | bootstrap 21-22-23-24 | padrao_exato | ruptura>estavel |
|---|---|---|---|---|---|---|---|
| AF | arvore | 1 | Rec@10 | MMBB | ???B | True | True |
| AF | arvore | 1 | Rec@20 | MBBB | ???? | False | True |
| AF | arvore | 2 | Rec@10 | MMBB | ??B? | True | True |
| AF | arvore | 2 | Rec@20 | MMBB | ???? | True | True |
| AF | arvore | 3 | Rec@10 | MMBB | ???B | True | True |
| AF | arvore | 3 | Rec@20 | MMBB | ???? | True | True |
| AF | arvore | 4 | Rec@10 | MMBB | ???B | True | True |
| AF | arvore | 4 | Rec@20 | MMBB | ???? | True | True |
| AF | ridge | 1 | Rec@10 | MMBB | ???? | True | True |
| AF | ridge | 1 | Rec@20 | MMBB | M??? | True | True |
| AF | ridge | 2 | Rec@10 | MMBB | ???? | True | True |
| AF | ridge | 2 | Rec@20 | MMBM | ???? | False | True |
| AF | ridge | 3 | Rec@10 | MM=B | ???? | False | True |
| AF | ridge | 3 | Rec@20 | MMBB | ???? | True | True |
| AF | ridge | 4 | Rec@10 | =MBB | ???? | False | True |
| AF | ridge | 4 | Rec@20 | MMBB | ???? | True | True |
| EM | arvore | 1 | Rec@10 | MBBB | ???? | False | True |
| EM | arvore | 1 | Rec@20 | MBBB | ???B | False | True |
| EM | arvore | 2 | Rec@10 | MBBB | ?B?? | False | True |
| EM | arvore | 2 | Rec@20 | MBBB | ???? | False | True |
| EM | arvore | 3 | Rec@10 | MBBB | ?B?? | False | True |
| EM | arvore | 3 | Rec@20 | MBBB | ???? | False | True |
| EM | arvore | 4 | Rec@10 | MBBB | ?B?? | False | True |
| EM | arvore | 4 | Rec@20 | MBBB | ???? | False | True |
| EM | ridge | 1 | Rec@10 | MBB= | ?B?? | False | True |
| EM | ridge | 1 | Rec@20 | MBBB | ???? | False | True |
| EM | ridge | 2 | Rec@10 | MBBM | ???? | False | False |
| EM | ridge | 2 | Rec@20 | MBBM | ???? | False | False |
| EM | ridge | 3 | Rec@10 | MBBM | ???? | False | False |
| EM | ridge | 3 | Rec@20 | MBMB | ???? | False | False |
| EM | ridge | 4 | Rec@10 | MBB= | ???? | False | True |
| EM | ridge | 4 | Rec@20 | BBMB | ???? | False | False |

## Decisões — Cenário A (referência)

| cenario | etapa | modelo | bloco | referencia | Rec@10 pontual | Rec@10 IC>0 | Rec@10 IC<0 | Rec@20 pontual | Rec@20 IC>0 | Rec@20 IC<0 | decisao |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | AF | arvore | 1 | B1R | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | AF | arvore | 2 | B1R | 2/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | AF | arvore | 3 | B1R | 2/4 | 0/4 | 2/4 | 1/4 | 0/4 | 0/4 | não |
| A | AF | arvore | 4 | B1R | 2/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | AF | ridge | 1 | B1R | 0/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | AF | ridge | 2 | B1R | 1/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | não |
| A | AF | ridge | 3 | B1R | 1/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| A | AF | ridge | 4 | B1R | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 1 | B1R | 1/4 | 0/4 | 1/4 | 1/4 | 0/4 | 1/4 | não |
| A | EM | arvore | 2 | B1R | 0/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 3 | B1R | 0/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 4 | B1R | 0/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | ridge | 1 | B1R | 1/4 | 0/4 | 1/4 | 1/4 | 0/4 | 1/4 | não |
| A | EM | ridge | 2 | B1R | 2/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | ridge | 3 | B1R | 2/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| A | EM | ridge | 4 | B1R | 2/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | não |
| A | AF | arvore | 1 | B1R_lag | 3/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| A | AF | arvore | 2 | B1R_lag | 3/4 | 0/4 | 0/4 | 4/4 | 0/4 | 0/4 | indeterminado |
| A | AF | arvore | 3 | B1R_lag | 2/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| A | AF | arvore | 4 | B1R_lag | 3/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| A | AF | ridge | 1 | B1R_lag | 3/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | indeterminado |
| A | AF | ridge | 2 | B1R_lag | 3/4 | 0/4 | 0/4 | 4/4 | 0/4 | 0/4 | indeterminado |
| A | AF | ridge | 3 | B1R_lag | 4/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | indeterminado |
| A | AF | ridge | 4 | B1R_lag | 3/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 1 | B1R_lag | 1/4 | 1/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 2 | B1R_lag | 1/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| A | EM | arvore | 3 | B1R_lag | 2/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| A | EM | arvore | 4 | B1R_lag | 2/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| A | EM | ridge | 1 | B1R_lag | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | ridge | 2 | B1R_lag | 2/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| A | EM | ridge | 3 | B1R_lag | 2/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| A | EM | ridge | 4 | B1R_lag | 2/4 | 0/4 | 0/4 | 3/4 | 1/4 | 0/4 | não |
| A | AF | arvore | 1 | B2 | 4/4 | 2/4 | 0/4 | 4/4 | 2/4 | 0/4 | indeterminado |
| A | AF | arvore | 2 | B2 | 4/4 | 2/4 | 0/4 | 4/4 | 4/4 | 0/4 | indeterminado |
| A | AF | arvore | 3 | B2 | 4/4 | 1/4 | 0/4 | 4/4 | 2/4 | 0/4 | indeterminado |
| A | AF | arvore | 4 | B2 | 4/4 | 1/4 | 0/4 | 4/4 | 2/4 | 0/4 | indeterminado |
| A | AF | ridge | 1 | B2 | 4/4 | 2/4 | 0/4 | 4/4 | 3/4 | 0/4 | indeterminado |
| A | AF | ridge | 2 | B2 | 4/4 | 2/4 | 0/4 | 4/4 | 3/4 | 0/4 | indeterminado |
| A | AF | ridge | 3 | B2 | 4/4 | 3/4 | 0/4 | 4/4 | 4/4 | 0/4 | supera/adota |
| A | AF | ridge | 4 | B2 | 4/4 | 2/4 | 0/4 | 4/4 | 2/4 | 0/4 | indeterminado |
| A | EM | arvore | 1 | B2 | 3/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 2 | B2 | 2/4 | 1/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| A | EM | arvore | 3 | B2 | 3/4 | 1/4 | 0/4 | 3/4 | 1/4 | 0/4 | indeterminado |
| A | EM | arvore | 4 | B2 | 3/4 | 1/4 | 0/4 | 3/4 | 1/4 | 0/4 | indeterminado |
| A | EM | ridge | 1 | B2 | 4/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | ridge | 2 | B2 | 4/4 | 0/4 | 0/4 | 2/4 | 1/4 | 0/4 | não |
| A | EM | ridge | 3 | B2 | 4/4 | 0/4 | 0/4 | 3/4 | 1/4 | 0/4 | indeterminado |
| A | EM | ridge | 4 | B2 | 4/4 | 0/4 | 0/4 | 4/4 | 1/4 | 0/4 | indeterminado |
| A | AF | arvore | 2 | bloco 1 | 2/4 | 0/4 | 0/4 | 4/4 | 0/4 | 0/4 | não |
| A | AF | ridge | 2 | bloco 1 | 1/4 | 0/4 | 0/4 | 3/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 2 | bloco 1 | 1/4 | 0/4 | 0/4 | 4/4 | 1/4 | 0/4 | não |
| A | EM | ridge | 2 | bloco 1 | 2/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
| A | AF | arvore | 3 | bloco 2 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 1/4 | não |
| A | AF | ridge | 3 | bloco 2 | 2/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 3 | bloco 2 | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | EM | ridge | 3 | bloco 2 | 1/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | AF | arvore | 4 | bloco 3 | 2/4 | 0/4 | 0/4 | 1/4 | 0/4 | 0/4 | não |
| A | AF | ridge | 4 | bloco 3 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | não |
| A | EM | arvore | 4 | bloco 3 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | não |
| A | EM | ridge | 4 | bloco 3 | 1/4 | 0/4 | 0/4 | 2/4 | 0/4 | 0/4 | não |
