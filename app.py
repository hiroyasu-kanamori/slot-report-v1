import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==========================================
# 1. 初期設定（フォント・デザイン）
# ==========================================
font_path = '/usr/share/fonts/NotoSansCJK-Regular.ttc'  # 環境に合わせて変更してください
if font_path and os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()

def get_machine_rows(df, csv_name, display_name, threshold):
    """CSVから指定機種の優秀台データを抽出する"""
    # 機種名（データサイト表記）または 機種名（正式名）で検索
    m_df = df[(df['機種名（データサイト表記）'] == csv_name) | (df['機種名（正式名）'] == csv_name)].copy()
    e_df = m_df[m_df['差枚'] >= threshold].copy().sort_values('台番')
    
    if e_df.empty:
        return []
    
    rows = [[""] * 7]  # 見出し用の空行
    rows.append(['台番', '機種名', 'ゲーム数', 'BIG', 'REG', 'AT', '差枚数'])
    for _, row in e_df.iterrows():
        rows.append([
            str(int(row['台番'])),
            display_name,
            f"{int(row['G数']):,}G",
            str(int(row['BB'])),
            str(int(row['RB'])),
            str(int(row['ART'])),
            f"+{int(row['差枚']):,}枚"
        ])
    return rows

# ==========================================
# 2. STEP対話フロー
# ==========================================
print("--- STEP 2: CSVの読み込み ---")
csv_file = input("CSVファイル名を入力してください: ")
df = pd.read_csv(csv_file)

print("\n--- STEP 3 & 4: 看板の設定 ---")
banner_title = input("看板内の文字（メインタイトル）を何にしますか？: ")

targets = []
while True:
    print(f"\n--- STEP 5 & 6: 機種の設定 ({len(targets)+1}機種目) ---")
    csv_name = input("CSV内の正確な機種名を入力してください: ")
    display_name = input("画像の見出しに表示する名前を入力してください: ")
    
    print("\n--- STEP 7: 枚数の設定 ---")
    threshold = int(input(f"「{display_name}」は何枚以上の台を取得しますか？(数値のみ): "))
    
    targets.append((csv_name, display_name, threshold))
    
    print("\n--- STEP 8: 次の機種 ---")
    cont = input("次の機種はありますか？ (y/n): ").lower()
    if cont != 'y':
        break

# ==========================================
# 3. 画像生成ロジック
# ==========================================
master_rows = [[""] * 7]  # 最上部の余白
headline_indices = []
header_indices = []
separator_indices = []
machine_display_names = []

for i, (cn, dn, thr) in enumerate(targets):
    res = get_machine_rows(df, cn, dn, thr)
    if res:
        h_idx = len(master_rows)
        headline_indices.append(h_idx)
        header_indices.append(h_idx + 1)
        machine_display_names.append(dn)
        master_rows.extend(res)
        if i < len(targets) - 1:
            separator_indices.append(len(master_rows))
            master_rows.append([""] * 7)

# --- テーブル部分のレンダリング (Matplotlib) ---
fig, ax = plt.subplots(figsize=(16, len(master_rows) * 0.8))
ax.axis('off')
table = ax.table(cellText=master_rows, colWidths=[0.1, 0.2, 0.15, 0.1, 0.1, 0.1, 0.25], loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.scale(1.0, 3.8)

cells = table.get_celld()
for (r, c), cell in cells.items():
    if r == 0:  # 最上部セパレート
        cell.set_facecolor('white')
        cell.set_height(0.01)
        cell.visible_edges = ''
    elif r in headline_indices:  # 機種見出し（赤帯）
        cell.set_facecolor('#FF4B4B')
        cell.set_edgecolor('#FF4B4B')
        if c == 3:
            txt = cell.get_text()
            txt.set_text(f"{machine_display_names[headline_indices.index(r)]} 優秀台")
            txt.set_fontsize(28)
            txt.set_weight('bold')
            txt.set_color('black')  # 指示通り「黒文字」
            txt.set_clip_on(False)
        else:
            cell.get_text().set_text("")
        if c == 0: cell.visible_edges = 'TLB'
        elif c == 6: cell.visible_edges = 'TRB'
        else: cell.visible_edges = 'TB'
    elif r in header_indices:  # ヘッダー（黒帯）
        cell.set_facecolor('#444444')
        cell.get_text().set_color('white')
        cell.get_text().set_weight('bold')
        cell.get_text().set_fontsize(20)
    elif r in separator_indices:  # 機種間セパレート
        cell.set_facecolor('white')
        cell.set_height(0.01)  # 指示通り「0.01」
        cell.visible_edges = ''
    else:  # データ行
        cell.set_facecolor('#F2F2F2' if r % 2 == 0 else 'white')
        cell.get_text().set_fontsize(18)

# バッファに保存
buf = io.BytesIO()
plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
buf.seek(0)
table_img = Image.open(buf)

# --- 看板部分の作成 (Pillow) ---
banner_h = 150
banner_img = Image.new('RGB', (table_img.width, banner_h), color='#FF0000') # 四角い看板
draw = ImageDraw.Draw(banner_img)
try:
    font = ImageFont.truetype(font_path, 90) # 指示通り「サイズ90」
except:
    font = ImageFont.load_default()

bbox = draw.textbbox((0, 0), banner_title, font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((table_img.width - w) // 2, (banner_h - h) // 2 - 10), banner_title, fill="white", font=font)

# --- 最終結合 ---
final_img = Image.new('RGB', (table_img.width, banner_img.height + table_img.height), color='white')
final_img.paste(banner_img, (0, 0))
final_img.paste(table_img, (0, banner_img.height))

# 保存
output_name = "final_report.png"
final_img.save(output_name)
print(f"\n画像が保存されました: {output_name}")
