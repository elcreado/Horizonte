# Evaluación emparejada de intervalos temporales

Dataset sintético: 100 empresas; semilla 20261004; paso 30 días.
Ambos métodos comparten cortes y resultados futuros; cobertura nominal 0,8.

| Días | Perfil | Método | Ventanas | Cobertura | Amplitud COP | Interval score COP |
|---|---|---|---:|---:|---:|---:|
| 30 | all | empirical | 1300 | 0.7742 | 1814872.21 | 12007407.93 |
| 30 | all | corrected | 1300 | 0.8269 | 2096583.54 | 12008436.69 |
| 30 | declining | empirical | 260 | 0.7894 | 1006029.50 | 1491013.80 |
| 30 | declining | corrected | 260 | 0.8338 | 1147234.27 | 1507243.68 |
| 30 | retail | empirical | 260 | 0.7919 | 935340.91 | 1304416.16 |
| 30 | retail | corrected | 260 | 0.8373 | 1057183.47 | 1313246.07 |
| 30 | seasonal | empirical | 260 | 0.7418 | 1263091.08 | 1984758.78 |
| 30 | seasonal | corrected | 260 | 0.8124 | 1499826.22 | 1977841.57 |
| 30 | services | empirical | 260 | 0.7917 | 946106.93 | 1357138.61 |
| 30 | services | corrected | 260 | 0.8405 | 1090734.94 | 1372615.61 |
| 30 | volatile | empirical | 260 | 0.7564 | 4923792.61 | 53899712.30 |
| 30 | volatile | corrected | 260 | 0.8103 | 5687938.77 | 53871236.52 |
| 60 | all | empirical | 1000 | 0.7705 | 3435638.62 | 27254928.81 |
| 60 | all | corrected | 1000 | 0.8296 | 3964831.12 | 27163629.34 |
| 60 | declining | empirical | 200 | 0.7752 | 1791648.82 | 2763747.82 |
| 60 | declining | corrected | 200 | 0.8205 | 2046047.32 | 2806873.48 |
| 60 | retail | empirical | 200 | 0.7640 | 1682434.43 | 2450400.52 |
| 60 | retail | corrected | 200 | 0.8179 | 1881309.55 | 2466869.91 |
| 60 | seasonal | empirical | 200 | 0.7824 | 3211659.56 | 4501623.80 |
| 60 | seasonal | corrected | 200 | 0.8788 | 3799144.00 | 4209418.45 |
| 60 | services | empirical | 200 | 0.8081 | 1714024.31 | 2400674.95 |
| 60 | services | corrected | 200 | 0.8596 | 1978870.38 | 2433285.94 |
| 60 | volatile | empirical | 200 | 0.7228 | 8778425.96 | 124158196.96 |
| 60 | volatile | corrected | 200 | 0.7712 | 10118784.35 | 123901698.90 |
| 90 | all | empirical | 700 | 0.7413 | 5251544.88 | 53347784.69 |
| 90 | all | corrected | 700 | 0.8101 | 6067846.07 | 52775766.56 |
| 90 | declining | empirical | 140 | 0.7568 | 2584663.25 | 4184208.51 |
| 90 | declining | corrected | 140 | 0.8025 | 2954293.84 | 4104943.99 |
| 90 | retail | empirical | 140 | 0.7502 | 2424539.18 | 3572175.87 |
| 90 | retail | corrected | 140 | 0.8105 | 2699773.99 | 3518025.17 |
| 90 | seasonal | empirical | 140 | 0.7657 | 6069395.09 | 8173097.28 |
| 90 | seasonal | corrected | 140 | 0.9025 | 7146210.42 | 7561423.23 |
| 90 | services | empirical | 140 | 0.8031 | 2469117.54 | 3485229.52 |
| 90 | services | corrected | 140 | 0.8648 | 2892737.30 | 3510258.39 |
| 90 | volatile | empirical | 140 | 0.6305 | 12710009.35 | 247324212.26 |
| 90 | volatile | corrected | 140 | 0.6701 | 14646214.79 | 245184182.01 |

Menor interval score es mejor: penaliza amplitud y observaciones fuera del intervalo.
No es una probabilidad de déficit ni prueba de cobertura conjunta de la trayectoria.
El método corregido reserva historia y puede empeorar ante cambios de régimen.
Ventanas solapadas, clasificación/revisión perfectas y compromisos puntuales sintéticos:
no demuestran calibración en empresas reales ni intercambiabilidad.
