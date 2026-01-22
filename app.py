import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont
import io
import os

# 日本語フォント設定（環境に合わせて代替フォントを使用）
font_path = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'

st.set_page_config(page_title="スロット優秀台レポート作成", layout="centered")
st.title("🎰 優秀台レポート作成アプリ")

# --- STEP 2: CSVのアップロード ---
uploaded_file = st.file_uploader("解析するCSVファイルをアップロードしてください", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSVを読み込みました！")

    # --- STEP 3 & 4: 看板の設定 ---
    st.subheader("1. 看板タイトルの設定")
    banner_title = st.text_input("看板内の文字（メインタイトル）", value="週間おススメ機種！")

    # --- STEP 5 ~ 8: 機種の設定 ---
    st.subheader("2. 対象機種の設定")
    
    # 複数機種に対応できるようリストで管理
    if 'targets' not in st.session_state:
        st.session_state.targets = []

    with st.form("machine_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            csv_name = st.text_input("CSV内の正確な名称", placeholder="L北斗 転生の章2")
        with col2:
            display_name = st.text_input("画像での表示名", placeholder="北斗転生")
        with col3:
            threshold = st.number_input("しきい値（枚数）", value=1000, step=500)
        
        add_button = st.form_submit_button("機種を追加する")
        if add_button and csv_name and display_name:
            st.session_state.targets.append((csv_name, display_name, threshold))

    # 追加された機種の表示
    if st.session_state.targets:
        st.write("### 現在の対象機種:")
        for i, (cn, dn, thr) in enumerate(st.session_state.targets):
            st.write(f"{i+1}. {dn} ({cn}) : {thr}枚以上")
        
        if st.button("設定をリセット"):
            st.session_state.targets = []
            st.experimental_rerun()

    # --- 画像生成 ---
    if st.button("🚀 レポート画像を生成する") and st.session_state.targets:
        
        def get_machine_rows(df, csv_name, display_name, threshold):
            m_df = df[(df['機種名（データサイト表記）'] == csv_name) | (df['機種名（正式名）'] == csv_name)].copy()
            e_df = m_df[m_df['差枚'] >= threshold].copy().sort_values('台番')
            if e_df.empty: return []
            rows = [[""] * 7]
            rows.append(['台番', '機種名', 'ゲーム数', 'BIG', 'REG', 'AT', '差枚数'])
            for _, row in e_df.iterrows():
                rows.append([str(int(row['台番'])), display_name, f"{int(row['G数']):,}G", str(int(row['BB'])), str(int(row['RB'])), str(int(row['ART'])), f"+{int(row['差枚']):,}枚"])
            return rows

        master_rows = [[""] * 7]
        headline_indices, header_indices, separator_indices, machine_names = [], [], [], []

        for i, (cn, dn, thr) in enumerate(st.session_state.targets):
            res = get_machine_rows(df, cn, dn, thr)
            if res:
                h_idx = len(master_rows)
                headline_indices.append(h_idx)
                header_indices.append(h_idx + 1)
                machine_names.append(dn)
                master_rows.extend(res)
                if i < len(st.session_state.targets) - 1:
                    separator_indices.append(len(master_rows))
                    master_rows.append([""] * 7)

        if len(master_rows) > 1:
            # テーブル描画
            fig, ax = plt.subplots(figsize=(16, len(master_rows) * 0.8))
            ax.axis('off')
            table = ax.table(cellText=master_rows, colWidths=[0.1, 0.2, 0.15, 0.1, 0.1, 0.1, 0.25], loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.scale(1.0, 3.8)

            for (r, c), cell in table.get_celld().items():
                if r == 0: cell.set_height(0.01); cell.visible_edges = ''
                elif r in headline_indices:
                    cell.set_facecolor('#FF4B4B')
                    if c == 3:
                        txt = cell.get_text()
                        txt.set_text(f"{machine_names[headline_indices.index(r)]} 優秀台")
                        txt.set_fontsize(28); txt.set_weight('bold'); txt.set_color('black')
                    else: cell.get_text().set_text("")
                elif r in header_indices:
                    cell.set_facecolor('#444444'); cell.get_text().set_color('white'); cell.get_text().set_fontsize(20)
                elif r in separator_indices:
                    cell.set_height(0.01); cell.visible_edges = ''
                else:
                    cell.set_facecolor('#F2F2F2' if r % 2 == 0 else 'white'); cell.get_text().set_fontsize(18)

            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            table_img = Image.open(buf)

            # 看板作成
            banner_img = Image.new('RGB', (table_img.width, 150), color='#FF0000')
            draw = ImageDraw.Draw(banner_img)
            draw.text((table_img.width//2 - 100, 50), banner_title, fill="white")

            # 合体
            final_img = Image.new('RGB', (table_img.width, 150 + table_img.height), color='white')
            final_img.paste(banner_img, (0, 0))
            final_img.paste(table_img, (0, 150))

            st.image(final_img, caption="生成されたレポート")
            
            # ダウンロード
            img_io = io.BytesIO()
            final_img.save(img_io, 'PNG')
            st.download_button("画像を保存する", data=img_io.getvalue(), file_name="report.png", mime="image/png")
        else:
            st.warning("条件に合うデータがありませんでした。")
