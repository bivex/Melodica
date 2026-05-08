# Shorts Audio Library — Mastering Complete

## Pipeline (все три скрипта)
```
Генерация → MixingDesk → MasteringDesk → Export MIDI
   │             │              │
   │             │              ├─ Loudness normalization (RMS→85)
   │             │              ├─ Multiband compression (LOW/MID/HIGH)
   │             │              ├─ Stereo imaging (panning per track)
   │             │              └─ Brickwall limiter (peak ≤120)
   │             ├─ Section faders (Hook/Dynamics/Loop)
   │             ├─ Track gain staging
   │             └─ Loop fade-out automation
   └─ Custom generators (bass, drums, SFX, pad, lead, clicks, fanfare, coins)
```

## Новые модули в `melodica/`
- `melodica/shorts_mixing.py` — `MixingDesk`
- `melodica/shorts_mastering.py` — `MasteringDesk`

Обновлены импорты в генераторах:
```python
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
```

## Настройки MasteringDesk
| Параметр | Значение |
|----------|---------|
| Target RMS velocity | 85 |
| Target peak ceiling | 120 |
| Limiter threshold | 125 (brickwall) |
| Multiband compression | LOW: 0.9, MID: 0.95, HIGH: 1.0 |
| Panning | bass/drums/lead/voice: CENTER, pad: LEFT, sfx/fanfare: RIGHT, coins: LEFT |

## Финальные файлы в `output/shorts_mids/`

### Nutra (6 файлов)
| Файл | Длит. | BPM | Заметки |
|------|-------|-----|--------|
| weight_loss_15s.mid | 14.5s | 165 | motivational |
| supplements_15s.mid | 16.0s | 150 | scientific |
| fitness_15s.mid | 15.1s | 175 | energetic |
| biohacking_15s.mid | 15.5s | 155 | calm_tech |
| detox_15s.mid | 13.7s | 140 | healing |
| fitness_30s.mid | 30.2s | 175 | extended |

### Crypto (4 файла)
| Файл | Длит. | BPM | Заметки |
|------|-------|-----|--------|
| crypto_15s.mid | 15.2s | 158 | техно, synthwave |
| crypto_bull_15s.mid | 14.5s | 165 | aggressive, driving |
| crypto_bear_15s.mid | 14.5s | 132 | pulsing, subdued |
| crypto_bull_30s.mid | 30.5s | 165 | extended |

### Casino (5 файлов)
| Файл | Длит. | BPM | Заметки |
|------|-------|-----|--------|
| casino_slots_15s.mid | 15.5s | 155 | walking bass, bright |
| casino_roulette_15s.mid | 15.0s | 128 | pulsing, dark pad |
| casino_high_roller_15s.mid | 14.3s | 168 | driving, bright |
| casino_highroller_30s.mid | 30.0s | 168 | extended |
| casino_highroller_15s_fanfare.mid | 14.3s | 168 | +fanfare & coins |

**Статистика (после mastering):**
- Общее количество файлов: 15
- Общее количество нот: ~8 900
- Средний RMS: 73–75
- Пиковая скорость: ≤120 (все безопасно)

Все файлы готовы к использованию в YouTube Shorts.
