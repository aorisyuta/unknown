import json
import time
import sys

# 先ほど作成したクラスをインポートする想定
# (ファイル名が def-list.py の場合はリネームするか、同じファイル内に記述してください)
from def_list import HulaController, S 

def main():
    print("=== プログラム開始 ===")
    
    # 1. 競技マップ設定の読み込み
    # 当日15分の調整時間では、このJSONファイルだけを書き換えます。
    try:
        with open('setting.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except FileNotFoundError:
        print("エラー: setting.json が見つかりません。")
        sys.exit(1)

    # 2. コントローラーの初期化
    # ※ 実機で動かす場合はここに pyhula API のインスタンスを渡します
    # 例: api = pyhula.HulaApi(); controller = HulaController(api)
    controller = HulaController(api_instance=None) 

    # 競技全体の制限時間 (レポート 1.1 本質的な制約より)
    TOTAL_TIME_LIMIT_S = 120 
    start_time = time.time()

    # 3. 最初の離陸
    print("\n--- 離陸 ---")
    controller._api_call("single_fly_takeoff")
    controller.wait_after_takeoff() # 離陸直後のフリーズ回避 (教訓9)

    # 4. JSONで指定された順番(order)通りにターゲットを巡回
    for target_name in settings["order"]:
        # ターゲット情報を検索
        target = next((p for p in settings["points"] if p["name"] == target_name), None)
        if not target:
            continue

        print(f"\n>>> ターゲット [{target_name}] に向かいます")
        
        # 残り時間の確認 (帰還や着陸の予算を残すため、残り15秒なら中断などのロジック)
        remaining_time = TOTAL_TIME_LIMIT_S - (time.time() - start_time)
        if remaining_time < 20:
            print("残り時間が少ないため、次のターゲットへの移動を中止します。")
            break

        # [動作1] 移動 (move)
        print(f"  [1/3] 移動中... 座標({target['x']}, {target['y']})")
        controller.move(qr=target['qr'], target_x=target['x'], target_y=target['y'])

        # [動作2] クリップ (clip)
        print(f"  [2/3] クリップ開始 (制限時間: {target['clip_timeout_s']}秒)")
        clip_success = controller.clip(
            qr=target['qr'], 
            target_alt=target['clip_alt_cm'], 
            timeout=target['clip_timeout_s']
        )
        
        if clip_success:
            print("  -> クリップ成功！正確な位置に静止しました。")
        else:
            print("  -> クリップタイムアウト。可能な範囲で着陸へ移行します。")

        # [動作3] 着陸と得点確保 (land)
        # ルール: ヘリポート上で10秒間静止する必要がある
        print(f"  [3/3] 着陸し、得点を確保します...")
        controller.land(timeout=15) # 10秒待機＋降下時間

        # 次のターゲットがある場合は再離陸
        if target_name != settings["order"][-1]:
            print("\n--- 次のポイントへ向けて再離陸 ---")
            controller._api_call("single_fly_takeoff")
            controller.wait_after_takeoff()

    # 5. 競技終了 (ホームへ帰還)
    print("\n>>> 全ターゲット巡回完了。ホームへ帰還します。")
    # 必要であれば controller.home() を呼び出して原点に戻る
    # controller.home()
    
    # 最終的な安全着陸 (念のため)
    controller.land(timeout=15)
    print("=== 競技終了 ===")

if __name__ == "__main__":
    # もし手書きメモの「TODO 2: 20秒静止テスト」を行いたい場合は
    # 以下のコメントアウトを外して単体テストを実行できます。
    
    # controller = HulaController(api_instance=None)
    # controller.test_hover_20s()
    
    main()