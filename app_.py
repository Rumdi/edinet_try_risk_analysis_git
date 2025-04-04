import streamlit as st
import pandas as pd
import plotly.express as px

# セッション状態の初期化
if 'selected_risk' not in st.session_state:
    st.session_state.selected_risk = None

# CSVデータの読み込み
@st.cache_data
def load_data():
    df = pd.read_csv("df_all_risk_api_processed__.csv")
    df["提出日"] = pd.to_datetime(df["提出日"], errors="coerce")
    df["提出四半期"] = df["提出日"].dt.to_period("Q").astype(str)
    return df

df = load_data()

# サイドバーのフィルター
st.sidebar.header("🔍 フィルター")
selected_industry = st.sidebar.multiselect("業種を選択", options=df["33業種区分"].unique(), default=df["33業種区分"].unique() if len(df["33業種区分"].unique()) > 0 else ["すべて"])
selected_company = st.sidebar.multiselect("企業を選択", options=df["提出者名"].unique(), default=df["提出者名"].unique() if len(df["提出者名"].unique()) > 0 else ["すべて"])
selected_quarter = st.sidebar.multiselect("提出四半期を選択", options=sorted(df["提出四半期"].dropna().unique()), default=sorted(df["提出四半期"].dropna().unique()) if len(df["提出四半期"].dropna().unique()) > 0 else ["すべて"])
selected_category = st.sidebar.selectbox("リスク大分類を選択", options=["すべて"] + sorted(df["大分類"].dropna().unique().tolist()))

# フィルター適用
filtered_df = df[
    (df["33業種区分"].isin(selected_industry) if selected_industry else True) &
    (df["提出者名"].isin(selected_company) if selected_company else True) &
    (df["提出四半期"].isin(selected_quarter) if selected_quarter else True)
]

# メイン画面タイトル
st.title("📊 リスク分析ダッシュボード")

# 大分類の円グラフ
st.subheader("📈 大分類ごとのリスク分布（件数）")
if not filtered_df.empty:
    risk_df = filtered_df[filtered_df["大分類"] == selected_category] if selected_category != "すべて" else filtered_df.copy()
    category_counts = filtered_df["大分類"].value_counts().reset_index()
    category_counts.columns = ["大分類", "件数"]
    category_counts = category_counts.sort_values("大分類")
    fig_pie = px.pie(category_counts, values="件数", names="大分類", hole=0.4,
                     category_orders={"大分類": sorted(category_counts["大分類"].unique())})
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.warning("該当するデータがありません。")

# 棒グラフ：選択した大分類内のリスク名件数
if selected_category != "すべて":
    st.subheader(f"📊 『{selected_category}』内のリスク名分布")

    unit = st.radio("集計単位を選択", ["企業単位", "業種単位"], index=1, horizontal=True)

    if unit == "企業単位":
        count_df = risk_df.groupby(["提出者名", "リスク名"]).size().reset_index(name="件数")
        x_col = "提出者名"
    else:
        count_df = risk_df.groupby(["33業種区分", "リスク名"]).size().reset_index(name="件数")
        x_col = "33業種区分"

    if not count_df.empty:
        fig_bar = px.bar(count_df, x=x_col, y="件数", color="リスク名", barmode="group")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("この大分類・リスク名に該当するデータがありません。")

# 下段：リスク要約・リスク内容
st.markdown("---")

# 2カラムレイアウト
bottom_left, bottom_right = st.columns(2)

# 左側パネル：リスク要約
with bottom_left:
    st.subheader("📝 リスク要約")
    detail_risk_names = risk_df["リスク名"].dropna().unique()
    selected_detail_risk = st.selectbox("リスク名を選択", options=detail_risk_names)
    
    # リスク要約リストを表示
    detail_candidates = risk_df[risk_df["リスク名"] == selected_detail_risk].reset_index(drop=True)
    
    # スクロール可能なエリアのスタイルを適用
    st.markdown("""
    <style>
    .risk-summary-area {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # スクロール可能なエリアの開始
    st.markdown('<div class="risk-summary-area">', unsafe_allow_html=True)
    
    # 各リスク要約をカード形式で表示
    if not detail_candidates.empty:
        for idx, row in detail_candidates.iterrows():
            with st.container():
                st.markdown(f"""
                <div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px;'>
                    <strong>企業名:</strong> {row['提出者名']}<br>
                    <strong>提出日:</strong> {row['提出日'].strftime('%Y-%m-%d')}<br>
                    <strong>業種:</strong> {row['33業種区分']}<br>
                    <strong>要約:</strong> {row['要約']}
                </div>
                """, unsafe_allow_html=True)
                
                # ボタンが押されたらセッション状態に保存
                if st.button(f"▶ この全文を表示", key=f"btn_{idx}"):
                    st.session_state.selected_risk = row.to_dict()
    
    # スクロール可能なエリアの終了
    st.markdown('</div>', unsafe_allow_html=True)

with bottom_right:
    st.subheader("📄 リスク内容（全文）")
    
    if st.session_state.selected_risk is not None:
        row = st.session_state.selected_risk
        st.markdown(f"**企業名**: {row['提出者名']}")
        st.markdown(f"**提出日**: {pd.to_datetime(row['提出日']).strftime('%Y-%m-%d')}")
        st.markdown(f"**業種**: {row['33業種区分']}")
        st.markdown(f"**リスク名**: {row['リスク名']}")
        
        st.markdown(
            f"""
            <div style='max-height: 500px; overflow-y: auto; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; color: #000000'>
                {row["リスク内容"]}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("👈 左側のリスク要約から「この全文を表示」ボタンをクリックしてください")
