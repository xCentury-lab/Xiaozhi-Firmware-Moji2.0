# Movecall Moji 2.0 電源ツリー & Audio HW 構成

> **出典**: User 提供の公式回路図 (Schematic_Moji2 V1.0、嘉立创EDA、Movecall、2026-01-24 更新)
> **BOM**: U1 = ES8311 (WQFN-20, LCSC C962342) 公式リスト確認済

## 重要原則

**audio codec の `pa_voltage` / `codec_dac_voltage` は board 個別の物理電源で決まる**。
他 board の patch / 一般論 / hardcode 値を盲目的に適用しない。

## Moji 2.0 Audio HW

```
+3V3 ────┬───────────────────────────────────┐
         │                                   │
         ▼                                   ▼
   ┌─────────────┐                    ┌─────────────┐
   │  ES8311     │   I2S (3.3V)       │  ZTS6216    │
   │  (Audio     │◄──────────────────▶│  (Audio MIC │
   │   CODEC U1) │                    │   preamp)   │
   │  AVDD/DVDD/ │                    └─────────────┘
   │  IOVDD=3.3V │
   └─────┬───────┘
         │ DAC OUTP/OUTN (line out)
         ▼
   ┌─────────────┐    VBUS (~5V)
   │  PA chip    │◄──────────── USB-C 5V or VSYS
   │  (Audio SPK │
   │   U2)       │
   │  VCC=~5V    │──▶ FPC1 (Speaker)
   └─────────────┘
```

## es8311_audio_codec.cc の正しい設定

```cpp
// Movecall Moji 2.0 HW-correct values (per Schematic_Moji2 V1.0):
es8311_cfg.hw_gain.pa_voltage = 5.0;          // U2 PA chip is VBUS-powered (~5V)
es8311_cfg.hw_gain.codec_dac_voltage = 3.3;   // U1 ES8311 is +3V3
```

→ `hw_gain = 20 * log10(5.0 / 3.3) ≈ +3.6 dB` は意図された HW 補正値。

## 主要 GPIO ピン (BOM + 回路図より)

| 機能 | GPIO | 備考 |
|---|---|---|
| ES8311 I2C SDA | GPIO_NUM_26 | |
| ES8311 I2C SCL | GPIO_NUM_27 | |
| ES8311 PA pin | GPIO_NUM_5 | mute/unmute (binary GPIO、音量制御に不関与) |
| I2S MCLK | GPIO_NUM_25 | |
| I2S BCLK | GPIO_NUM_11 | |
| I2S WS (LRCK) | GPIO_NUM_24 | |
| I2S DIN | GPIO_NUM_12 | |
| I2S DOUT | GPIO_NUM_23 | |

## ESP32-C5-WROOM-1-N16R8

- Flash: 16 MB (N16)
- PSRAM: 8 MB QSPI (R8)
- Wi-Fi 6 デュアル (2.4G + 5G)
- BLE 5.0
- bootloader offset: **0x2000** (★ S3 系 0x0 と異なる、`CONFIG_BOOTLOADER_OFFSET_IN_FLASH=0x2000`)

## 主要 BOM (User 提供)

| ID | 部品 | Designator | Footprint | Manufacturer | LCSC |
|---|---|---|---|---|---|
| 1 | **ES8311** | U1 | WQFN-20_L3.0-W3.0-P0.40-BL-EP1.7 | Everest-semi (顺芯) | C962342 |
| 2 | 1uF (C0402) × 11 | C3,C7,C8,C15,C16,C17,C18,C19,C4,C11,C38 | C0402 | SAMSUNG | C52923 |
| 3 | 100nF (C0402) × 11 | C23,C5,C1,C2,C10,C36,C30,C21,C26,C27,C22 | C0402 | FH (风华) | C41851 |
| 4 | BLM15PX121SN1D (チップビーズ) × 4 | L3,L4,L2,L1 | L0402 | muRata (村田) | C88970 |
| 5 | 10uF (C0402) × 10 | C24,C6,C12,C37,C29,C25,C20,C32,C33,C31 | C0402 | SAMSUNG | C15525 |

## 関連リンク

- Movecall 公式 hw: https://oshwhub.com/movecall/moji2
- 3D モデル: https://makerworld.com.cn/zh/@MoveCall
- ES8311 datasheet (LCSC C962342)
