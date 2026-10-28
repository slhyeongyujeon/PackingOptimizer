from itertools import permutations
from dataclasses import dataclass
from PIL import Image as PILImage
from PIL import ImageDraw
from PIL import ImageFont
from functools import lru_cache

from io import BytesIO

import os
import plotly.graph_objects as go



# ==========================
# Rotation
# ==========================


@lru_cache(maxsize=None)
def get_rotations(
    length,
    width,
    height,
    direction="자유롭게"
):



    dimensions = (
        float(length),
        float(width),
        float(height)
    )



    all_rotations = list(
        set(
            permutations(
                dimensions,
                3
            )
        )
    )



    if direction == "자유롭게":
        return sorted(all_rotations)



    if direction == "눕히기":



        min_dim = min(dimensions)



        return sorted(
            [
                r
                for r in all_rotations
                if r[2] == min_dim
            ]
        )



    if direction == "세우기":



        max_dim = max(dimensions)



        return sorted(
            [
                r
                for r in all_rotations
                if r[2] == max_dim
            ]
        )



    raise ValueError(
        f"Unknown direction: {direction}"
    )




# ==========================
# Dataclass
# ==========================



@dataclass
class Placement:



    name: str



    x: float
    y: float
    z: float



    length: float
    width: float
    height: float




# ==========================
# Overlap Check
# ==========================



def boxes_overlap(
    ax, ay, az,
    al, aw, ah,
    bx, by, bz,
    bl, bw, bh
):
    return not (
        ax + al <= bx
        or
        bx + bl <= ax
        or
        ay + aw <= by
        or
        by + bw <= ay
        or
        az + ah <= bz
        or
        bz + bh <= az
    )



# ==========================
# Extreme Points
# ==========================



def generate_candidate_points(
    placements
):

    points = {
        (0, 0, 0)
    }

    for p in placements:

        # 기존 3개
        points.add(
            (
                p.x + p.length,
                p.y,
                p.z
            )
        )

        points.add(
            (
                p.x,
                p.y + p.width,
                p.z
            )
        )

        points.add(
            (
                p.x,
                p.y,
                p.z + p.height
            )
        )


    return sorted(
        points,
        key=lambda p:
        (
            round(p[2], 4),
            round(p[0], 4),
            round(p[1], 4)
        )
    )




# ==========================
# Placement Validity
# ==========================



def is_supported(
    x,
    y,
    z,
    length,
    width,
    height,
    placements,
    tolerance=1.0
):



    if z == 0:
        return True



    required_support_ratio = 0.5



    for p in placements:



        top_z = p.z + p.height



        if abs(top_z - z) > tolerance:
            continue



        support_x = (



            min(
                x + length,
                p.x + p.length
            )



            -



            max(
                x,
                p.x
            )



        )



        support_y = (



            min(
                y + width,
                p.y + p.width
            )



            -



            max(
                y,
                p.y
            )



        )



        if support_x <= 0:
            continue



        if support_y <= 0:
            continue



        support_area = (
            support_x
            *
            support_y
        )



        bottom_area = (
            length
            *
            width
        )



        support_ratio = (
            support_area
            /
            bottom_area
        )



        if support_ratio >= required_support_ratio:
            return True



    return False



def can_place_at(
    x,
    y,
    z,
    length,
    width,
    height,
    placements,
    box_length,
    box_width,
    box_height
):



    if (
        x + length > box_length
        or
        y + width > box_width
        or
        z + height > box_height
    ):
        return False

    if not placements:
        return True

    for p in placements:

        if boxes_overlap(

            x,
            y,
            z,

            length,
            width,
            height,

            p.x,
            p.y,
            p.z,

            p.length,
            p.width,
            p.height

        ):
            return False



    return is_supported(
        x,
        y,
        z,
        length,
        width,
        height,
        placements
    )




# ==========================
# Extreme Point Placement
# ==========================



def place_part_ep(
    placements,
    box_length,
    box_width,
    box_height,
    part_name,
    length,
    width,
    height,
    direction
):



    points = generate_candidate_points(
        placements
    )



    rotations = get_rotations(
        length,
        width,
        height,
        direction
    )



    for point in points:



        px, py, pz = point



        for rotation in rotations:



            l, w, h = rotation



            if can_place_at(
                px,
                py,
                pz,
                l,
                w,
                h,
                placements,
                box_length,
                box_width,
                box_height
            ):



                return Placement(
                    part_name,
                    px,
                    py,
                    pz,
                    l,
                    w,
                    h
                )



    return None




# ==========================
# Parts Builder
# ==========================



def build_parts_for_set(
    bom,
    set_count
):

    parts = []

    for item in bom:

        total_qty = (
            int(item["qty_per_set"])
            * set_count
        )

        parts.extend(
            [item] * total_qty
        )

    parts.sort(
        key=lambda p:
        (
            p["length"]
            * p["width"]
            * p["height"],

            max(
                p["length"],
                p["width"],
                p["height"]
            )
        ),
        reverse=True
    )

    return parts

# ==========================
# Packing Engine
# ==========================

def pack_parts_ep(
    box_length,
    box_width,
    box_height,
    parts
):

    placements = []

    for part in parts:

        result = place_part_ep(
            placements,
            box_length,
            box_width,
            box_height,
            part["name"],
            part["length"],
            part["width"],
            part["height"],
            part["direction"]
        )

        if result is None:

            return placements

        placements.append(
            result
        )

    return placements




# ==========================
# SET Check
# ==========================



def can_pack_set(
    box_length,
    box_width,
    box_height,
    bom,
    set_count
):



    parts = build_parts_for_set(
        bom,
        set_count
    )



    placements = pack_parts_ep(
        box_length,
        box_width,
        box_height,
        parts
    )






    return (
        len(parts)
        ==
        len(placements)
    )



def get_packing_result(
    box_length,
    box_width,
    box_height,
    bom,
    set_count
):



    parts = build_parts_for_set(
        bom,
        set_count
    )



    placements = pack_parts_ep(
        box_length,
        box_width,
        box_height,
        parts
    )



    return placements
# ==========================
# Max SET
# ==========================

def find_max_set_count(
    box_length,
    box_width,
    box_height,
    bom,
    max_set=20
):

    low = 0
    high = max_set

    while low < high:

        mid = (low + high + 1) // 2

        if can_pack_set(
            box_length,
            box_width,
            box_height,
            bom,
            mid
        ):
            low = mid
        else:
            high = mid - 1

    return low


def calculate_utilization(
    box_length,
    box_width,
    box_height,
    placements
):



    box_volume = (
        box_length
        * box_width
        * box_height
    )



    used_volume = sum(



        p.length
        * p.width
        * p.height



        for p in placements
    )



    utilization = (
        used_volume
        / box_volume
        * 100
    )



    return (
        box_volume,
        used_volume,
        utilization
    )



def plot_packing(
    box_length,
    box_width,
    box_height,
    placements
):





    for i, p in enumerate(
        placements,
        start=1
    ):



        print(



            f"{i:02d}"



            f" | {p.name}"



            f" | X={p.x:.1f}"



            f" Y={p.y:.1f}"



            f" Z={p.z:.1f}"



            f" | "



            f"{p.length:.1f}"



            f"x"



            f"{p.width:.1f}"



            f"x"



            f"{p.height:.1f}"
        )



    print(
        "\n(Box Size)"
    )



    print(
        f"{box_length}"
        f"x"
        f"{box_width}"
        f"x"
        f"{box_height}"
    )



def print_placements(
    placements
):




    for i, p in enumerate(
        placements,
        start=1
    ):



        print(



            f"{i:02d}"



            f" {p.name}"



            f" | X={p.x:.1f}"



            f" Y={p.y:.1f}"



            f" Z={p.z:.1f}"



            f" | "



            f"{p.length:.1f}"



            f"x"



            f"{p.width:.1f}"



            f"x"



            f"{p.height:.1f}"



        )



def print_summary(
    box_length,
    box_width,
    box_height,
    placements
):



    box_volume, used_volume, utilization = (
        calculate_utilization(
            box_length,
            box_width,
            box_height,
            placements
        )
    )



    print(
        f"Placement Count : {len(placements)}"
    )



    print(
        f"Box Volume : {box_volume:,.0f}"
    )



    print(
        f"Used Volume : {used_volume:,.0f}"
    )



    print(
        f"Utilization : {utilization:.2f}%"
    )

def create_plotly_figure(
    box_length,
    box_width,
    box_height,
    placements,
    bom
):

    fig = go.Figure()

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#d62728",
        "#2ca02c",
        "#9467bd"
    ]

    part_names = [
    item["name"]
    for item in bom
    ]

    color_map = {
            name: colors[i % len(colors)]
            for i, name in enumerate(part_names)
        }

    legend_added = set()

    ordered_placements = []

    for part_name in part_names:

        ordered_placements.extend(
            [
                p
                for p in placements
                if p.name == part_name
            ]
        )

    for p in ordered_placements:

        color = color_map[p.name]

        showlegend = (
            p.name not in legend_added
        )

        legend_added.add(
            p.name
        )

        x0 = p.x
        x1 = p.x + p.length

        y0 = p.y
        y1 = p.y + p.width

        z0 = p.z
        z1 = p.z + p.height

        vertices_x = [
            x0, x1, x1, x0,
            x0, x1, x1, x0
        ]

        vertices_y = [
            y0, y0, y1, y1,
            y0, y0, y1, y1
        ]

        vertices_z = [
            z0, z0, z0, z0,
            z1, z1, z1, z1
        ]

        fig.add_trace(

            go.Mesh3d(

                x=vertices_x,
                y=vertices_y,
                z=vertices_z,

                i=[0,0,0,4,4,5,2,3,1,6,0,2],
                j=[1,2,3,5,6,6,3,7,5,7,4,6],
                k=[2,3,1,6,7,2,7,4,6,3,5,7],

                color=color,

                opacity=0.25,

                name=p.name,

                showlegend=showlegend
            )
        )

        edges = [

            (0,1),(1,2),(2,3),(3,0),

            (4,5),(5,6),(6,7),(7,4),

            (0,4),(1,5),(2,6),(3,7)

        ]

        for start, end in edges:

            fig.add_trace(

                go.Scatter3d(

                    x=[
                        vertices_x[start],
                        vertices_x[end]
                    ],

                    y=[
                        vertices_y[start],
                        vertices_y[end]
                    ],

                    z=[
                        vertices_z[start],
                        vertices_z[end]
                    ],

                    mode="lines",

                    line=dict(
                        color="#EEEEEE",
                        width=1
                    ),

                    showlegend=False,

                    hoverinfo="skip"
                )
            )

    box_edges = [

        [(0,0,0), (box_length,0,0)],
        [(box_length,0,0), (box_length,box_width,0)],
        [(box_length,box_width,0), (0,box_width,0)],
        [(0,box_width,0), (0,0,0)],

        [(0,0,box_height), (box_length,0,box_height)],
        [(box_length,0,box_height), (box_length,box_width,box_height)],
        [(box_length,box_width,box_height), (0,box_width,box_height)],
        [(0,box_width,box_height), (0,0,box_height)],

        [(0,0,0), (0,0,box_height)],
        [(box_length,0,0), (box_length,0,box_height)],
        [(box_length,box_width,0), (box_length,box_width,box_height)],
        [(0,box_width,0), (0,box_width,box_height)]

    ]

    first_box_trace = True

    for edge in box_edges:

        fig.add_trace(

            go.Scatter3d(

                x=[
                    edge[0][0],
                    edge[1][0]
                ],

                y=[
                    edge[0][1],
                    edge[1][1]
                ],

                z=[
                    edge[0][2],
                    edge[1][2]
                ],

                mode="lines",

                line=dict(
                    color="white",
                    width=8
                ),

                name="BOX",

                showlegend=first_box_trace,

                hoverinfo="skip"
            )
        )

        first_box_trace = False

    fig.update_layout(

        width=1400,
        height=900,

        paper_bgcolor="#111111",

        plot_bgcolor="#111111",

        showlegend=True,

        scene=dict(

            bgcolor="#111111",

            xaxis=dict(
                title="길이(mm)",
                range=[0, box_length]
            ),

            yaxis=dict(
                title="너비(mm)",
                range=[0, box_width]
            ),

            zaxis=dict(
                title="높이(mm)",
                range=[0, box_height]
            ),

            aspectmode="data"
        ),

        margin=dict(
            l=0,
            r=0,
            t=20,
            b=0
        )
    )

    return fig

def save_packing_image(
    box_length,
    box_width,
    box_height,
    placements,
    bom
):

    views = {

        "등각도1": dict(
            x=1.8,
            y=1.8,
            z=1.2
        ),

        "등각도2": dict(
            x=-1.8,
            y=1.8,
            z=1.2
        )

    }

    image_files = []

    for title, eye in views.items():

        fig = create_plotly_figure(
            box_length,
            box_width,
            box_height,
            placements,
            bom
        )

        fig.update_layout(

            showlegend=False,

            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False)
            ),

            scene_camera=dict(
                projection=dict(
                    type="orthographic"
                ),
                eye=eye
            )
        )

        buffer = BytesIO()

        fig.write_image(
            buffer,
            format="png",
            scale=3
        )

        buffer.seek(0)

        image_files.append(
            (
                PILImage.open(buffer),
                title
            )
        )

    width = image_files[0][0].width
    height = image_files[0][0].height

    print(width)
    print(height)

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#d62728",
        "#2ca02c",
        "#9467bd"
    ]

    part_names = [
    item["name"]
    for item in bom
    ]

    color_map = {
        name: colors[i % len(colors)]
        for i, name in enumerate(part_names)
    }

    legend_height = max(
        800,
        len(part_names) * 220 + 200
    )

    canvas = PILImage.new(
        "RGB",
        (
            width * 2,
            height + legend_height
        ),
        (20, 20, 20)
    )

    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype(
            "fonts/NotoSansKR-VariableFont_wght.ttf",
            180
        )
        print("FONT SUCCESS")
    except Exception as e:
        print(e)
        print("FONT FAIL")
        font = ImageFont.load_default()

    positions = [
        (0, 0),
        (width, 0)
    ]

    for (img, title), pos in zip(
        image_files,
        positions
    ):

        canvas.paste(
            img,
            pos
        )

        draw.text(
            (
                pos[0] + 100,
                pos[1] + 80
            ),
            title,
            fill="white",
            font=font
        )

    # ==========================
    # 부품 색상표
    # ==========================

    legend_y = height + 20

    draw.text(
        (40, legend_y),
        "부품 색상표",
        fill="white",
        font=font
    )

    for i, name in enumerate(part_names):

        y = legend_y + 180 + (i * 180)

        draw.rectangle(
            (
                50,
                y,
                180,
                y + 130
            ),
            fill=color_map[name]
        )

        draw.text(
            (
                200,
                y
            ),
            name,
            fill="white",
            font=font
        )

    buffer = BytesIO()

    canvas.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer.getvalue()

