# 撤回された patch 一覧

## 0001-es8311-pa_voltage-3.3.WITHDRAWN.patch (2026-05-30)

### 状態: ❌ WITHDRAWN

### 撤回理由

User 提供の **Movecall Moji 2.0 公式回路図 (Schematic_Moji2 V1.0、嘉立创EDA、2026-01-24)** で HW 構成を確認した結果、本 patch の前提が **回路図と矛盾**することが判明。

| ブロック | 部品 | **回路図での電源** | patch の前提 |
|---|---|---|---|
| Audio CODEC (U1) | **ES8311** | **+3V3** (3.3V) ✓ | 3.3V (一致) |
| Audio SPK (U2) | スピーカ PA chip | **VBUS (~5V)** | 3.3V (**❌ HW と矛盾**) |

→ 本家 hardcode `pa_voltage=5.0, codec_dac_voltage=3.3` は **Moji2.0 の HW と一致した正しい設定**。
   `hw_gain = 20*log10(5.0/3.3) ≈ +3.6dB` は意図された電圧変換補正であり bug ではない。

### User 提供の決定的証拠
1. 回路図 (2 枚): Audio CODEC ブロック (ES8311+3V3) と Audio SPK ブロック (PA+VBUS) を明示
2. BOM (5 行): U1 = ES8311 (WQFN-20, LCSC C962342, Everest-semi 顺芯) 確定

### 真因の再評価 (Engineer 並列 audit より)
User の症状「音量 70% 固定、音声指示で 100%/20% にしても反映されない」は codec hw_gain とは無関係:
- **Firmware MCP audit (Engineer #1)**: `self.audio_speaker.set_volume` tool は無条件登録、設計通り。70% は `audio_codec.h:54` の hardcoded default。**`SetOutputVolume()` が一度も呼ばれていない**ことが症状の説明。
- **Server audit (Engineer #2)**: xiaozhi-interpreter (Go) の `device_volume.go` + dispatcher + `tool_usage_directive.go` で正しく LLM に exposed、wire format も正しい。

→ 真因は **MCP path の上流 (LLM が tool call を発行しない) か NVS persistence のいずれか**。
   serial log (`AudioCodec: Set output volume to N`) の有無で 1 行判定可能。

### 教訓
- HW 関連 patch を当てる前に **必ず回路図 / BOM / datasheet で物理電源を確認**
- 一般化された patch (「hw_gain hardcode は罠」) を board 個別に適用するのは危険
- 同一ファイル `es8311_audio_codec.cc` を共有する複数 board (Moji1/Moji2/VoCat/...) は **board 個別に電源仕様が異なる可能性**があり、共有ファイル side-effect なしの修正は board.cc 経由で voltage を渡す改造が望ましい (将来 PR 候補)
