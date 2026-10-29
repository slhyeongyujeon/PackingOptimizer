import streamlit as st
import pandas as pd

from packing_ep import (
    find_max_set_count,
    get_packing_result,
    create_plotly_figure,
    save_packing_image,
    calculate_utilization
)


st.set_page_config(
    page_title="Optimizing Packing",
    layout="wide"
)

if "result_png" not in st.session_state:
    st.session_state.result_png = None

if "fig" not in st.session_state:
    st.session_state.fig = None

if "max_set" not in st.session_state:
    st.session_state.max_set = None

if "total_weight_g" not in st.session_state:
    st.session_state.total_weight_g = None

if "estimated_box_weight_kg" not in st.session_state:
    st.session_state.estimated_box_weight_kg = None

if "placements" not in st.session_state:
    st.session_state.placements = None

if "bom" not in st.session_state:
    st.session_state.bom = None

if "utilization" not in st.session_state:
    st.session_state.utilization = None


st.title("📦 Optimizing Packing")

st.subheader("박스 크기")

col1, col2, col3 = st.columns(3)

with col1:
    box_length = st.number_input(
        "박스 길이 (mm)",
        min_value=0.0,
        value=None,
        placeholder="길이 입력"
    )

with col2:
    box_width = st.number_input(
        "박스 너비 (mm)",
        min_value=0.0,
        value=None,
        placeholder="너비 입력"
    )

with col3:
    box_height = st.number_input(
        "박스 높이 (mm)",
        min_value=0.0,
        value=None,
        placeholder="높이 입력"
    )

st.divider()

default_bom = pd.DataFrame(
    columns=[
        "name",
        "part_type",
        "qty_per_set",
        "length",
        "width",
        "height",
        "weight",
        "direction"
    ]
)

if "bom_df" not in st.session_state:

    st.session_state.bom_df = default_bom.copy()

bom_col1, bom_col2, bom_col3 = st.columns([6,1,1])

with bom_col1:
    st.subheader("제품 BOM")




bom_df = st.data_editor(
    st.session_state.bom_df,
    key="bom_editor",
    num_rows="fixed",
    use_container_width=True,
    hide_index=True,
    column_config={

        "name": st.column_config.TextColumn(
            "부품 이름"
        ),

        "part_type": st.column_config.SelectboxColumn(
            "부품 종류",
            options=[
                "목업 부품 (+50mm)",
                "사출 부품 (+20mm)"
            ]
        ),
        "qty_per_set": st.column_config.NumberColumn(
            "1 SET당 부품 개수"
        ),
        "length": st.column_config.NumberColumn(
            "가로(mm)"
        ),
        "width": st.column_config.NumberColumn(
            "세로(mm)"
        ),
        "height": st.column_config.NumberColumn(
            "높이(mm)"
        ),
        "weight": st.column_config.NumberColumn(
            "무게(g)"
        ),
        "direction": st.column_config.SelectboxColumn(
            "적재방식",
            options=[
                "눕히기",
                "세우기",
                "자유롭게"
            ]
        )
    }
)

preview_df = bom_df.copy()

def get_packed_size(row):

    try:

        if row["part_type"] == "목업 부품 (+50mm)":
            offset = 50

        elif row["part_type"] == "사출 부품 (+20mm)":
            offset = 20

        else:
            return ""

        if (
            pd.isna(row["length"])
            or
            pd.isna(row["width"])
            or
            pd.isna(row["height"])
        ):
            return ""

        return (
            f"{int(row['length'] + offset)} × "
            f"{int(row['width'] + offset)} × "
            f"{int(row['height'] + offset)}"
        )

    except Exception:
        return ""

preview_df["적재 적용 크기"] = (
    preview_df.apply(
        get_packed_size,
        axis=1
    )
)

st.caption("📦 완충재 반영 후 실제 적재 적용 크기")

st.dataframe(
    preview_df[
        [
            "name",
            "part_type",
            "적재 적용 크기"
        ]
    ],
    hide_index=True,
    use_container_width=True
)

btn_col1, btn_col2 = st.columns([1,1])

with btn_col1:

    add_row = st.button(
        "➕ 행 추가",
        use_container_width=True
    )

with btn_col2:

    delete_row = st.button(
        "➖ 마지막 행 삭제",
        use_container_width=True
    )

if add_row:

    st.session_state.bom_df = bom_df.copy()

    new_row = pd.DataFrame([{
        "name": "",
        "part_type": None,
        "qty_per_set": None,
        "length": None,
        "width": None,
        "height": None,
        "weight": None,
        "direction": None
    }])


    st.session_state.bom_df = pd.concat(
        [
            st.session_state.bom_df,
            new_row
        ],
        ignore_index=True
    )

    st.rerun()


if delete_row:

    st.session_state.bom_df = bom_df.copy()

    if len(st.session_state.bom_df) > 0:

        st.session_state.bom_df = (
            st.session_state.bom_df
            .iloc[:-1]
            .reset_index(drop=True)
        )

    st.rerun()

st.divider()

if st.button(
    "계산하기",
    type="primary",
    use_container_width=True
):

    st.session_state.result_png = None

    bom_df = bom_df.dropna(
    subset=[
        "name",
        "part_type",
        "qty_per_set",
        "length",
        "width",
        "height"
    ]
)

    bom = bom_df.to_dict(
    orient="records"
    )

    for item in bom:

        if item["part_type"] == "목업 부품":

            offset = 50

        else:

            offset = 20

        item["length"] += offset
        item["width"] += offset
        item["height"] += offset

    st.session_state.bom = bom

   
    max_set = find_max_set_count(
    box_length,
    box_width,
    box_height,
    bom,
    max_set=800
)

    placements = get_packing_result(
        box_length,
        box_width,
        box_height,
        bom,
        max_set
    )

    _, _, utilization = (
    calculate_utilization(
        box_length,
        box_width,
        box_height,
        placements
    )
)

    total_weight_g = 0

    for item in bom:

        total_weight_g += (
            float(item["qty_per_set"])
            * float(item["weight"])
            * max_set
        )

    # 박스 무게 추정

    # CBM 계산

    cbm = (
            box_length
            * box_width
            * box_height
        ) / 1_000_000_000

    # 박스 중량 적용

    if cbm < 0.1575:

        estimated_box_weight_kg = 1.5

    elif cbm < 0.2:

        estimated_box_weight_kg = 2

    else:

        estimated_box_weight_kg = 3

    # 총 출하 무게 반영

    total_weight_g += (
        estimated_box_weight_kg * 1000
    )

    fig = create_plotly_figure(
    box_length,
    box_width,
    box_height,
    placements,
    bom
    )

    st.session_state.fig = fig
    st.session_state.max_set = max_set
    st.session_state.total_weight_g = total_weight_g
    
    st.session_state.estimated_box_weight_kg = (
    estimated_box_weight_kg
    )
    st.session_state.utilization = utilization
    st.session_state.placements = placements

if st.session_state.placements is not None:

    if st.button(
        "📷 등각 적재도 생성",
        use_container_width=True
    ):

        with st.spinner(
            "등각 적재도 생성 중..."
        ):

            st.session_state.result_png = (
                save_packing_image(
                box_length,
                box_width,
                box_height,
                st.session_state.placements,
                st.session_state.bom
                )
            )

if st.session_state.result_png:

        st.download_button(
        label="📷 등각 적재도 다운로드",
        data=st.session_state.result_png,
        file_name="packing_result_sheet.png",
        mime="image/png"
    )

if st.session_state.fig is not None:

    result_col1, result_col2, result_col3, result_col4 = st.columns(4)

    result_col3.metric(
    "추정 박스 무게",
    f"{st.session_state.estimated_box_weight_kg:.0f} kg"
)

    if st.session_state.utilization is not None:

        result_col4.metric(
            "적재율",
            f"{st.session_state.utilization:.1f}%"
        )


    result_col1.metric(
        "1박스 당 최대 SET",
        int(st.session_state.max_set)
    )

    if st.session_state.total_weight_g >= 1000:

        result_col2.metric(
            "총 출하 무게",
            f"{st.session_state.total_weight_g / 1000:.2f} kg"
        )

    else:

        result_col2.metric(
            "총 출하 무게",
            f"{st.session_state.total_weight_g:.0f} g"
        )

    st.divider()

    st.subheader("운임비 계산 사이트(FedEx)")

    st.link_button(
        "✈️ 운임비 계산 바로가기",
        "https://www.fedex.com/ko-kr/online/rating.html",
        use_container_width=True
    )

    st.divider()

    st.subheader("적재 결과")

    st.plotly_chart(
        st.session_state.fig,
        use_container_width=True
    )