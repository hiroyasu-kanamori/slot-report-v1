import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont
import io
import urllib.request
import os

# --- 修正ポイント：この命令を一番最初に持ってくる ---
st.set_page_config(page_title="スロット優秀台レポート", layout="centered")

# --- 日本語フォントのセットアップ ---
@st.cache_data
def load_font():
    font_path = "NotoSansCJKjp-Regular.otf"
    if not os.path.exists(font_path):
        # より日本語対応が確実なNoto Sans CJK JPをダウンロード
        url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf"
        urllib.request.urlretrieve(url, font_path)
    return font_path

font_p = load_font()
prop = fm.FontProperties(fname=font_p)

st.title("🎰 優秀台レポート作成")

# --- 以下、前回のロジックと同じ ---
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='cp932')
    except:
        df = pd.read_csv(uploaded_file, encoding='utf-8')

    banner_title = st.text_input("看板の文字を入力してください", value="月間おすすめ機種")

    if 'targets' not in st.session_state:
        st.session_state.targets = []

    st.write("---")
    st.subheader(f"{len(st.session_state.targets) + 1}機種目の設定")
    c1, c2, c3 = st.columns(3)
    with c1:
        csv_n = st.text_input("CSV内の正確な名称", key=f"cn_{len(st.session_state.targets)}")
    with c2:
        dis_n = st.text_input("画像での表示名", key=f"dn_{len(st.session_state.targets)}")
    with c3:
        thr = st.number_input("しきい値(枚)", value=1000, step=500, key=f"th_{len(st.session_state.targets)}")

    if st.button("この機種をリストに追加する"):
        if csv_n and dis_n:
            st.session_state.targets.append((csv_n, dis_n, thr))
            st.rerun()

    if st.session_state.targets:
        st.write("### 現在のリスト")
        for i, (cn, dn, t) in enumerate(st.session_state.targets):
            st.write(f"{i+1}. {dn} ({t}枚以上)")
        
        if st.button("リストをクリア"):
            st.session_state.targets = []
            st.rerun()

        st.write("---")
        if st.button("🎨 画像を生成する"):
            
            def get_rows(df, cn, dn, thr):
                m_df = df[(df['機種名（データサイト表記）'] == cn) | (df['機種名（正式名）'] == cn)].copy()
                e_df = m_df[m_df['差枚'] >= thr].copy().sort_values('台番')
                if e_df.empty: return []
                rows = [[""] * 7, ['台番', '機種名', 'ゲーム数', 'BIG', 'REG', 'AT', '差枚数']]
                for _, row in e_df.iterrows():
                    rows.append([str(int(row['台番'])), dn, f"{int(row['G数']):,}G", str(int(row['BB'])), str(int(row['RB'])), str(int(row['ART'])), f"+{int(row['差枚']):,}枚"])
                return rows

            master_rows = [[""] * 7]
            h_idx, m_names = [], []

            for cn, dn, thr in st.session_state.targets:
                res = get_rows(df, cn, dn, thr)
                if res:
                    h_idx.append(len(master_rows))
                    m_names.append(dn)
                    master_rows.extend(res)
                    master_rows.append([""] * 7)

            if len(master_rows) > 1:
                fig, ax = plt.subplots(figsize=(16, len(master_rows) * 0.8))
                ax.axis('off')
                table = ax.table(cellText=master_rows, colWidths=[0.1, 0.2, 0.15, 0.1, 0.1, 0.1, 0.25], loc='center', cellLoc='center')
                table.auto_set_font_size(False)
                table.scale(1.0, 3.8)
                
                for (r, c), cell in table.get_celld().items():
                    cell.get_text().set_fontproperties(prop)
                    if r == 0 or master_rows[r] == [""] * 7:
                        cell.set_height(0.01); cell.visible_edges = ''
                    elif r in h_idx:
                        cell.set_facecolor('#FF4B4B')
                        if c == 3:
                            txt = cell.get_text()
                            txt.set_text(f"{m_names[h_idx.index(r)]} 優秀台")
                            txt.set_fontsize(28); txt.set_weight('bold'); txt.set_color('black')
                        else: cell.get_text().set_text("")
                    elif r-1 in h_idx:
                        cell.set_facecolor('#444444'); cell.get_text().set_color('white'); cell.get_text().set_fontsize(20)
                    else:
                        cell.set_facecolor('#F2F2F2' if r % 2 == 0 else 'white'); cell.get_text().set_fontsize(18)

                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
                t_img = Image.open(buf)

                banner_h = 150
                banner_img = Image.new('RGB', (t_img.width, banner_h), color='#FF0000')
                draw = ImageDraw.Draw(banner_img)
                try:
                    b_font = ImageFont.truetype(font_p, 90)
                except:
                    b_font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), banner_title, font=b_font)
                tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                draw.text(((t_img.width - tw)//2, (banner_h - th)//2 - 10), banner_title, fill="white", font=b_font)

                final_img = Image.new('RGB', (t_img.width, banner_h + t_img.height), color='white')
                final_img.paste(banner_img, (0, 0))
                final_img.paste(t_img, (0, banner_h))
                
                st.image(final_img)
                img_io = io.BytesIO()
                final_img.save(img_io, 'PNG')
                st.download_button("画像をダウンロード", data=img_io.getvalue(), file_name="report.png")
