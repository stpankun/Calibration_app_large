import tkinter as tk
from tkinter import filedialog
import traceback

print("--- テスト開始 ---")
print("Tkinterの初期化を試みます...")

try:
    # 1. Tkinterのメインウィンドウを作成
    root = tk.Tk()
    root.withdraw()  # ウィンドウは非表示にする
    print("ステップ1: Tkinterの初期化に成功しました。")

    # 2. ファイル選択ダイアログを開く
    print("ステップ2: ファイル選択ダイアログを開きます...")
    filepath = filedialog.askopenfilename(
        parent=root,
        title="テスト用のファイル選択ダイアログ"
    )
    
    # 3. ダイアログが閉じた後の処理
    print("ステップ3: ファイル選択ダイアログが閉じられました。")
    if filepath:
        print(f"  -> 結果: ファイルが選択されました。パス: {filepath}")
    else:
        print("  -> 結果: ファイルは選択されませんでした（キャンセルされました）。")

    root.destroy()
    print("ステップ4: 正常に終了しました。")

except Exception as e:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"エラーが発生しました: {e}")
    print("詳細なエラー情報:")
    traceback.print_exc()
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

print("--- テスト終了 ---")
# Windowsの場合、すぐにウィンドウが閉じないように入力待ちを追加
input("何かキーを押してウィンドウを閉じてください...")