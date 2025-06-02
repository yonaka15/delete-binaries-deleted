# Delete Binaries Deleted

PostgreSQLの`Binaries_deleted`テーブルから全レコードを削除するツールです。

## 特徴

- 🔄 **バッチ処理**: 400レコードずつ安全に削除
- 🛡️ **安全性**: 削除前の確認プロンプトとドライランモード
- 📊 **進捗表示**: リアルタイムの削除進捗と統計情報
- 🔍 **ドライラン**: 実際の削除前に影響を確認
- 📝 **詳細ログ**: 操作の詳細な記録
- ⚡ **高速処理**: 効率的なバッチ削除

## インストール

### uvを使用（推奨）

```bash
# プロジェクトのクローン/移動
cd delete-binaries-deleted

# 依存関係のインストール
uv sync

# 開発依存関係も含める場合
uv sync --extra dev
```

## 設定

`.env`ファイルに以下の環境変数を設定してください：

```env
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=your-database-name
DB_USER=your-username
DB_PASSWORD=your-password
```

⚠️ **重要**: `.env`ファイルは`.gitignore`に含まれているため、Gitにコミットされません。

## 使用方法

### 基本的な使用

```bash
# uvの仮想環境で実行
uv run delete-binaries

# または仮想環境をアクティベートして実行
uv shell
delete-binaries
```

### オプション

```bash
# ドライラン（実際には削除しない）
uv run delete-binaries --dry-run

# バッチサイズを変更
uv run delete-binaries --batch-size 200

# 確認プロンプトをスキップ
uv run delete-binaries --force

# 詳細ログを有効化
uv run delete-binaries --verbose

# 全オプションの組み合わせ
uv run delete-binaries --batch-size 500 --verbose --force
```

### ヘルプ

```bash
uv run delete-binaries --help
```

## 安全機能

1. **データベース接続の検証**: 実行前に接続をテスト
2. **削除前確認**: デフォルトで削除前に確認プロンプト
3. **ドライランモード**: `--dry-run`で削除内容を事前確認
4. **バッチ処理**: メモリ効率的な400件ずつの処理
5. **トランザクション管理**: エラー時の自動ロールバック
6. **詳細ログ**: 全操作の記録

## 出力例

```
Delete Binaries Deleted Tool
Safely delete all records from Binaries_deleted table

🔍 Validating database connection...
✅ Database connection validated

📊 Analyzing data...
                     Deletion Statistics
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric            ┃ Value                                           ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total Records     │ 1,500                                           │
│ Batch Size        │ 400                                             │
│ Estimated Batches │ 4                                               │
│ Estimated Time    │ 0.4 minutes                                     │
└───────────────────┴─────────────────────────────────────────────────┘

⚠️  WARNING: This will permanently delete ALL records from Binaries_deleted table!
Are you sure you want to delete 1,500 records? [y/N]:
```

## 開発

### 開発環境のセットアップ

```bash
# 開発依存関係のインストール
uv sync --extra dev

# pre-commitフックのインストール
uv run pre-commit install
```

### テスト実行

```bash
# テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=delete_binaries_deleted
```

### コード品質チェック

```bash
# フォーマット
uv run black src/ tests/

# リント
uv run flake8 src/ tests/

# 型チェック
uv run mypy src/
```

## トラブルシューティング

### データベース接続エラー

1. `.env`ファイルの設定を確認
2. データベースサーバーが稼働中か確認
3. ネットワーク接続を確認
4. 認証情報が正しいか確認

### メモリ不足

バッチサイズを小さくしてください：

```bash
uv run delete-binaries --batch-size 100
```

### 権限エラー

データベースユーザーに`DELETE`権限があることを確認してください。

## 注意事項

⚠️ **このツールは永続的にデータを削除します。**
