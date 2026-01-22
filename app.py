import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont
import io
import os

# 日本語フォント設定（Streamlit Cloud環境で標準的に使えるフォント）
font_path = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'

st.set_page_config(page_title="スロット優秀台レポート作成", layout="centered")
st.title("🎰 優秀台レポート作成アプリ")

# --- 1. CSVのアップロード ---
uploaded_file = st.file_uploader("解析するCSVファイルをアップロードしてください", type=['csv'])

if uploaded_file:
    # エンコーディング対応
    try:
        df = pd.read_csv(uploaded_file, encoding='cp932')
    except:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    st.success("CSVを読み込みました！")

    # --- 2. 看板タイトルの設定 ---
    st.subheader("1. 看板タイトルの設定")
    banner_title = st.text_input("看板内の文字（メインタイトル）", value="週間おススメ機種！")

    # --- 3. 対象機種の設定 ---
    st.subheader("2. 対象機種の設定")
    
    # 複数機種に対応できるようセッション状態で管理
    if 'targets' not in st.session_state:
        st.session_state.targets = []

    with st.form("machine_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            csv_name = st.text_input("CSV内の正確な名称", value="L北斗 転生の章2")
        with col2:
            display_name = st.text_input("画像での表示名", value="北斗転生")
        with col3:
            threshold = st.number_input("しきい値（枚数）", value=1000, step=500)
        
        add_button = st.form_submit_button("リストに追加")
        if add_button and csv_name and display_name:
            st.session_state.targets.append((csv_name, display_name, threshold))

    if st.session_state.targets:
        st.write("---")
        for i, (cn, dn, thr) in enumerate(st.session_state.targets):
            st.write(f"【{i+1}】 {dn} (CSV名:{cn}) / {thr}枚以上")
        
        if st.button("機種リストをクリア"):
            st.session_state.targets = []
            rerun()

        # --- 4. 画像生成 ---
        if st.button("🚀 レポート画像を生成する"):
            
            def get_rows(df, cn, dn, thr):
                m_df = df[(df['機種名（データサイト表記）'] == cn) | (df['機種名（正式名）'] == cn)].copy()
                e_df = m_df[m_df['差枚'] >= thr].copy().sort_values('台番')
                if e_df.empty: return []
                rows = [[""] * 7]
                rows.append(['台番', '機種名', 'ゲーム数', 'BIG', 'REG', 'AT', '差枚数'])
                for _, row in e_df.iterrows():
                    rows.append([str(int(row['台番'])), dn, f"{int(row['G数']):,}G", str(int(row['BB'])), str(int(row['RB'])), str(int(row['ART'])), f"+{int(row['差枚']):,}枚"])
                return rows

            master_rows = [[""] * 7]
            headline_idx, header_idx, machine_names = [], [], []

            for i, (cn, dn, thr) in enumerate(st.session_state.targets):
                res = get_rows(df, cn, dn, thr)
                if res:
                    h_idx = len(master_rows)
                    headline_idx.append(h_idx)
                    header_idx.append(h_idx + 1)
                    machine_names.append(dn)
                    master_rows.extend(res)
                    master_rows.append([""] * 7) # セパレーター

            if len(master_rows) > 1:
                fig, ax = plt.subplots(figsize=(16, len(master_rows) * 0.8))
                ax.axis('off')
                table = ax.table(cellText=master_rows, colWidths=[0.1, 0.2, 0.15, 0.1, 0.1, 0.1, 0.25], loc='center', cellLoc='center')
                table.auto_set_font_size(False)
                table.scale(1.0, 3.8)

                for (r, c), cell in table.get_celld().items():
                    if r == 0 or master_rows[r] == [""] * 7:
                        cell.set_height(0.01); cell.visible_edges = ''
                    elif r in headline_idx:
                        cell.set_facecolor('#FF4B4B')
                        if c == 3:
                            txt = cell.get_text()
                            txt.set_text(f"{machine_names[headline_idx.index(r)]} 優秀台")
                            txt.set_fontsize(28); txt.set_weight('bold')
                        else: cell.get_text().set_text("")
                    elif r in header_idx:
                        cell.set_facecolor('#444444'); cell.get_text().set_color('white')
                    else:
                        cell.set_facecolor('#F2F2F2' if r % 2 == 0 else 'white')

                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
                table_img = Image.open(buf)
                
                # 看板結合
                final_img = Image.new('RGB', (table_img.width, 150 + table_img.height), color='#FF0000')
                draw = ImageDraw.Draw(final_img)
                # 看板テキスト描画
                draw.text((table_img.width//2 - 150, 50), banner_title, fill="white")
                final_img.paste(table_img, (0, 150))
                
                st.image(final_img)
                
                # ダウンロードボタン
                img_io = io.BytesIO()
                final_img.save(img_io, 'PNG')
                st.download_button("画像を保存", data=img_io.getvalue(), file_name="report.png")
            else:
                st.warning("該当データがありませんでした。")
