# サーバー側エンハンス要件: 工場キッティング用 MCP 自動呼出

> **宛先**: classism.net サーバー開発・運用担当
> **依頼元**: xxc@ctoch.jp (本プロジェクト・デバイス側担当)
> **対象バックエンド**: `wss://classism.net/xiaozhi/v1/`
> **最終更新**: 2026-04-18
> **関連ドキュメント**: [../operations/volume-configuration.md](../operations/volume-configuration.md) § NVS 保持でファーム更新する方法 → 方式 2 / [../customization-spec.md](../customization-spec.md)

---

## 🎯 依頼の要約

本プロジェクトで量産する Xiaozhi ベースデバイス（現在 yunliao-s3、waveshare-1.85c 等）に対して、以下の **3 要件**を満たす「工場モード」機能をサーバー側に実装いただきたい。

1. **端末別（Device-Id 単位）に異なる初期設定値**（音量・テーマ等）を出荷前に配布
2. **出荷後も同じ仕組みで遠隔調整**（例: 顧客クレーム対応で特定端末の音量を下げる）
3. **設定履歴をサーバー側 DB に記録**（監査ログ用途、どの端末に何時何を設定したか追跡）

**デバイス側実装は現行ファームのまま変更不要**です。MCP (Model Context Protocol) が既に組込まれているため、サーバーが JSON-RPC メッセージを送れば音量変更が NVS に永続化されます。

---

## 🔧 デバイス側 MCP の既存実装（動作検証済）

### プロトコル規格
- **ベース**: MCP (Model Context Protocol) over WebSocket
- **トランスポート層**: Xiaozhi 独自 JSON メッセージの `payload` に JSON-RPC 2.0 を埋込む形
- **仕様バージョン**: `protocolVersion: "2024-11-05"`（デバイスが `initialize` 応答で通知）
- **実装箇所**: [main/mcp_server.cc](https://github.com/78/xiaozhi-esp32/blob/v2.2.4/main/mcp_server.cc)（本家 78/xiaozhi-esp32）

### メッセージ構造（サーバー → デバイス 方向）

デバイスの `OnIncomingJson` が受信する JSON:

```json
{
  "type": "mcp",
  "payload": {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "self.audio_speaker.set_volume",
      "arguments": { "volume": 50 }
    },
    "id": 1
  }
}
```

- `type: "mcp"` で振分け
- `payload` に MCP JSON-RPC メッセージそのまま格納
- `id` は JSON-RPC 規約通り、応答と対応付け用（整数必須）

### 利用可能なツール一覧

現行ファームが実機起動時に登録している MCP ツール（シリアルログで確認済）:

| ツール名 | 引数 | 説明 | 用途 |
|---|---|---|---|
| `self.get_device_status` | なし | 現在の音量/画面/バッテリ/ネット状態を JSON で返却 | **キッティング前の状態確認・検証** |
| `self.audio_speaker.set_volume` | `volume: int 0-100` | 音量を NVS に永続化 | **★ 本要件の主機能** |
| `self.screen.set_brightness` | `brightness: int 0-100` | 画面輝度 | 将来展開用 |
| `self.screen.set_theme` | `theme: "light"\|"dark"` | テーマ切替 | 将来展開用 |
| `self.reboot` (user) | なし | デバイス再起動 | キッティング後の再起動確認 |
| `self.get_system_info` (user) | なし | システム情報取得 | 監査ログ記録 |
| `self.system.set_aec` | — | AEC 設定（yunliao-s3 固有） | オプション |
| `self.system.switch_TFT` | — | TFT 切替（yunliao-s3 固有） | オプション |

### デバイス応答の形式

`set_volume` 成功時にデバイスから送信される JSON-RPC 応答:

```json
{
  "type": "mcp",
  "payload": {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "content": [{"type": "text", "text": "true"}],
      "isError": false
    }
  }
}
```

エラー時:
```json
{
  "type": "mcp",
  "payload": {
    "jsonrpc": "2.0",
    "id": 1,
    "error": {"code": -32603, "message": "..."}
  }
}
```

---

## 📋 サーバー側に実装いただきたい機能

### 必須機能

#### F-1. キッティング対象の管理 DB

| 項目 | 型 | 説明 |
|---|---|---|
| `device_id` | string (MAC形式: XX:XX:XX:XX:XX:XX) | デバイスの一意識別子 |
| `target_volume` | int 0-100 | 出荷時に設定したい音量 |
| `target_brightness` | int 0-100 | （オプション）画面輝度 |
| `target_theme` | "light" \| "dark" | （オプション）テーマ |
| `shipment_batch` | string | 納入先識別（OEM-A-2026Q2 等） |
| `kitted_at` | timestamp nullable | キッティング完了日時（NULL = 未完了） |
| `kitted_values` | json | 実際に書込まれた値の記録 |

#### F-2. WebSocket 接続時の自動キッティング

既存の WebSocket `hello` 交換完了（`session_id` 送信後）に続けて、以下の判定フローを実装:

```
[WebSocket 接続成立 + hello 交換完了]
    ↓
[Device-Id をヘッダ "Device-Id" から取得]
    ↓
[F-1 の DB に該当レコードあり かつ kitted_at IS NULL ?]
    ├─ YES → 「工場モード」実行
    │   ├─ MCP initialize 送信 (protocolVersion 合意)
    │   ├─ MCP tools/list で set_volume 等が存在することを検証 (任意)
    │   ├─ MCP tools/call で self.audio_speaker.set_volume(target_volume) 送信
    │   ├─ デバイス応答の isError=false を確認
    │   ├─ 必要に応じて self.screen.set_brightness, set_theme も連続実行
    │   ├─ self.get_device_status で反映確認
    │   ├─ F-1 の DB に kitted_at と kitted_values を書込
    │   └─ 通常の会話モードへ
    │
    └─ NO → 通常の会話モード
```

#### F-3. 遠隔調整 API（出荷後運用用）

カスタマーサポート等から、既にキッティング済の端末に対して再調整できる管理 API:

```
POST /admin/devices/{device_id}/settings
Body: {"volume": 40, "reason": "customer complaint #12345"}

→ サーバーが該当デバイスの現在の WebSocket セッション（または次回接続時）に
  MCP tools/call を自動送信し、設定適用 + 監査ログ記録
```

#### F-4. 監査ログ

全ての MCP 設定変更を永続化。最低限のフィールド:

| カラム | 内容 |
|---|---|
| `device_id` | 対象端末 |
| `timestamp` | 送信日時 |
| `method` | "tools/call" |
| `tool_name` | "self.audio_speaker.set_volume" 等 |
| `arguments` | `{"volume":50}` |
| `result` | success / error |
| `operator` | factory_auto / admin_manual / customer_support 等 |
| `reason` | 任意の理由文字列 |

### オプション機能（将来拡張）

- **F-5**: Wi-Fi プロビジョニング連携（工場専用 SSID に接続した端末のみ工場モード発動）
- **F-6**: キッティング失敗時の自動リトライ（次回接続時に再試行）
- **F-7**: 設定テンプレート機能（OEM-A 用セット、OEM-B 用セット等をプリセット化）

---

## 🔬 現在の classism.net 実装との差分確認が必要な項目

以下はシリアルログから読取った現状挙動です。**サーバー担当に確認いただきたい項目**:

### Q-1. `{"type":"status", ...}` メッセージの仕様

シリアルログで以下の警告が多数発火:
```
W (31139) Application: Unknown message type: status
W (31249) Application: Unknown message type: status
W (40139) Application: Unknown message type: status
```

- `status` 型はサーバーから送信されているが、デバイス側（本家 v2.2.4）は未対応
- → 送信意図・含まれるフィールド・デバイス側で何をして欲しいかを共有いただきたい
- もしクライアント側対応が必要なら、本家へのフィードバック or ローカルパッチで対応可能

### Q-2. MCP `tools/call` 送信の実装状況

- 現状の classism.net WebSocket 実装は MCP メッセージを送信しているか？
- `{"type":"mcp","payload":{"method":"tools/call",...}}` を送るコードが既に存在するか、ゼロから実装するか
- 実装済の場合、どのタイミングで何を送っているか

### Q-3. `{"type":"mcp","payload":{"method":"initialize"}}` 送信の有無

- 正式な MCP 仕様では `initialize` → `tools/list` → `tools/call` の順で呼ぶのが標準
- デバイス側は `initialize` を受けていなくても `tools/call` 単独で動作するが、MCP プロトコル準拠の観点では `initialize` 必須
- キッティング前の `initialize` 送信は実装されているか

### Q-4. キッティング用 Device-Id 判定ロジック

- 現状、どの Device-Id が「工場モードで設定送信する対象」かをサーバーはどう判別しているか？
- 未実装の場合、F-1 の DB スキーマを新規作成いただく必要あり

---

## ✅ 受入試験基準

サーバー側実装完了後、本プロジェクトで以下を実施して合否判定:

### T-1. 単体機能テスト
- [ ] DB に Device-Id + target_volume=50 を登録
- [ ] デバイスを工場リセット状態（NVS 空）でフラッシュ
- [ ] 起動 → WebSocket 接続 → シリアルログに MCP `tools/call` 受信ログが出る
- [ ] `ESP_LOGI(TAG, "Set output volume to 50")` がシリアルに出力される
- [ ] デバイス再起動後も 50% が保持される（NVS 永続化確認）
- [ ] DB の `kitted_at` に完了日時が記録される

### T-2. バッチ処理テスト
- [ ] 複数 Device-Id × 異なる target_volume を DB 登録
- [ ] 複数端末を順次起動し、それぞれ正しい値が NVS に書込まれる
- [ ] 全端末で `kitted_at` が記録され、重複実行されない（冪等性）

### T-3. 監査ログテスト
- [ ] 全てのキッティング実行が F-4 の監査ログに記録される
- [ ] `tool_name`, `arguments`, `result`, `operator`, `reason` が全て埋まっている

### T-4. 遠隔調整テスト
- [ ] 既存端末（kitted_at あり）が起動中に F-3 の API 経由で音量変更
- [ ] リアルタイムにデバイス音量が変わる or 次回起動時に変わる
- [ ] 監査ログに記録される

---

## 🗓 想定スケジュール（要調整）

| マイルストーン | 内容 | 想定工数 |
|---|---|---|
| M-1 | F-1 DB スキーマ設計 + 初期データ投入ツール | 2 日 |
| M-2 | F-2 自動キッティングロジック実装 | 3 日 |
| M-3 | F-4 監査ログ実装 | 1 日 |
| M-4 | F-3 遠隔調整 API 実装 | 2 日 |
| M-5 | 本プロジェクトと連携して受入試験 T-1〜T-4 | 2 日 |
| **合計** | | **約 10 営業日** |

---

## 📎 参考資料

- [MCP 公式仕様](https://modelcontextprotocol.io/specification) — JSON-RPC 2.0 ベースのプロトコル仕様
- [Xiaozhi MCP 実装](https://github.com/78/xiaozhi-esp32/blob/v2.2.4/main/mcp_server.cc) — デバイス側 MCP サーバー実装（参考）
- [本プロジェクト volume-configuration.md](../operations/volume-configuration.md) § NVS 保持でファーム更新する方法 → 方式 2
- [本プロジェクト customization-spec.md](../customization-spec.md) — 4 軸カスタマイズ要件
- [本プロジェクト WebSocket サーバー仕様（前回共有分）](chat-server-spec.md) — ※未作成の場合、本ファイルを起点に別途整理

---

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-04-18 | 1.0 | 初版。工場キッティング用 MCP 自動呼出要件、MCP プロトコル詳細、現状確認事項 Q-1〜Q-4、受入試験 T-1〜T-4 を整理 | xxc@ctoch.jp |
