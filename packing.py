from itertools import permutations
from dataclasses import dataclass


# ==========================
# 회전 엔진
# ==========================

def get_rotations(
    length,
    width,
    height,
    direction="Free"
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

    if direction == "Free":
        return sorted(all_rotations)

    if direction == "Lay":

        min_dim = min(dimensions)

        return sorted(
            [
                r
                for r in all_rotations
                if r[2] == min_dim
            ]
        )

    if direction == "Stand":

        max_dim = max(dimensions)

        return sorted(
            [
                r
                for r in all_rotations
                if r[2] == max_dim
            ]
        )

    raise ValueError(
        f"Unknown direction : {direction}"
    )


# ==========================
# Data Class
# ==========================

@dataclass
class Space:

    x: float
    y: float
    z: float

    length: float
    width: float
    height: float


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
# 체적 / 중량 계산
# ==========================

def calculate_set_volume(
    bom_list
):

    total_volume = 0

    for item in bom_list:

        total_volume += (
            item["length"]
            * item["width"]
            * item["height"]
            * item["qty_per_set"]
        )

    return total_volume


def calculate_set_weight(
    bom_list
):

    total_weight = 0

    for item in bom_list:

        total_weight += (
            item["weight"]
            * item["qty_per_set"]
        )

    return total_weight


def estimate_max_set(
    box_length,
    box_width,
    box_height,
    bom_list
):

    box_volume = (
        box_length
        * box_width
        * box_height
    )

    set_volume = calculate_set_volume(
        bom_list
    )

    if set_volume == 0:
        return 0

    return int(
        box_volume / set_volume
    )


# ==========================
# 배치 가능 여부
# ==========================

def can_place(
    space,
    length,
    width,
    height
):

    return (

        length <= space.length

        and

        width <= space.width

        and

        height <= space.height

    )


# ==========================
# 공간 분할
# ==========================

def split_space(
    space,
    length,
    width,
    height
):

    spaces = []

    # X 방향

    if space.length > length:

        spaces.append(

            Space(
                x=space.x + length,
                y=space.y,
                z=space.z,

                length=space.length - length,
                width=space.width,
                height=space.height
            )

        )

    # Y 방향

    if space.width > width:

        spaces.append(

            Space(
                x=space.x,
                y=space.y + width,
                z=space.z,

                length=length,
                width=space.width - width,
                height=space.height
            )

        )

    # Z 방향

    if space.height > height:

        spaces.append(

            Space(
                x=space.x,
                y=space.y,
                z=space.z + height,

                length=length,
                width=width,
                height=space.height - height
            )

        )

    return spaces


# ==========================
# Part 배치
# ==========================

def place_part(
    spaces,
    part_name,
    length,
    width,
    height,
    direction
):

    rotations = get_rotations(
        length,
        width,
        height,
        direction
    )

    for space_idx, space in enumerate(spaces):

        for rotation in rotations:

            l, w, h = rotation

            if can_place(
                space,
                l,
                w,
                h
            ):

                placement = Placement(
                    name=part_name,

                    x=space.x,
                    y=space.y,
                    z=space.z,

                    length=l,
                    width=w,
                    height=h
                )

                new_spaces = split_space(
                    space,
                    l,
                    w,
                    h
                )

                spaces.pop(space_idx)

                spaces.extend(
                    new_spaces
                )

                spaces.sort(
                    key=lambda s:
                    s.length
                    * s.width
                    * s.height,
                    reverse=True
                )

                return placement

    return None


# ==========================
# 실제 부품 생성
# ==========================

def build_parts_for_set(
    bom,
    set_count
):
    """
    SET 단위 순서 유지

    예)

    Part1
    Part2
    Part3
    Part4

    Part1
    Part2
    Part3
    Part4
    """

    parts = []

    for _ in range(set_count):

        for item in bom:

            for _ in range(
                item["qty_per_set"]
            ):

                parts.append(

                    {
                        "name": item["name"],
                        "qty": 1,

                        "length":
                        item["length"],

                        "width":
                        item["width"],

                        "height":
                        item["height"],

                        "direction":
                        item["direction"]
                    }

                )

    return parts


# ==========================
# 패킹
# ==========================

def pack_parts(
    box_length,
    box_width,
    box_height,
    parts
):

    spaces = [

        Space(
            0,
            0,
            0,
            box_length,
            box_width,
            box_height
        )

    ]

    placements = []

    for part in parts:

        result = place_part(
            spaces,
            part["name"],
            part["length"],
            part["width"],
            part["height"],
            part["direction"]
        )

        if result is None:

            print()

            print(
                f"FAILED : {part['name']}"
            )

            print()

            print(
                "=== REMAINING SPACES ==="
            )

            for s in spaces:

                print(
                    f"({s.x:.1f}, "
                    f"{s.y:.1f}, "
                    f"{s.z:.1f})"
                    f" -> "
                    f"{s.length:.1f}"
                    f"x"
                    f"{s.width:.1f}"
                    f"x"
                    f"{s.height:.1f}"
                )

            return placements

        placements.append(
            result
        )

    return placements

# ==========================
# SET 적재 가능 여부
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

    placements = pack_parts(
        box_length,
        box_width,
        box_height,
        parts
    )

    required_count = len(parts)

    print(
        f"\nRequired={required_count}, "
        f"Placed={len(placements)}"
    )

    print(
        "\n=== PLACEMENTS ==="
    )

    for p in placements:

        print(
            f"{p.name}"
            f" | ({p.x:.1f}, "
            f"{p.y:.1f}, "
            f"{p.z:.1f})"
            f" | "
            f"{p.length:.1f}"
            f"x"
            f"{p.width:.1f}"
            f"x"
            f"{p.height:.1f}"
        )

    return (
        len(placements)
        ==
        required_count
    )

# ==========================
# 최대 SET 탐색
# ==========================

def find_max_set_count(
    box_length,
    box_width,
    box_height,
    bom,
    max_set=20
):

    max_found = 0

    for set_count in range(
        1,
        max_set + 1
    ):

        result = can_pack_set(
            box_length,
            box_width,
            box_height,
            bom,
            set_count
        )

        print(
            f"SET {set_count} : {result}"
        )

        if result:

            max_found = set_count

        else:

            break

    return max_found


# ==========================
# TEST
# ==========================

if __name__ == "__main__":

    bom = [

        {
            "name": "Part1",
            "qty_per_set": 4,
            "length": 461,
            "width": 355.7,
            "height": 77.1,
            "weight": 678.25,
            "direction": "Lay"
        },

        {
            "name": "Part2",
            "qty_per_set": 2,
            "length": 487.5,
            "width": 90.4,
            "height": 64.4,
            "weight": 775.58,
            "direction": "Lay"
        },

        {
            "name": "Part3",
            "qty_per_set": 2,
            "length": 140,
            "width": 107,
            "height": 73.5,
            "weight": 208.60,
            "direction": "Lay"
        },

        {
            "name": "Part4",
            "qty_per_set": 1,
            "length": 168,
            "width": 168,
            "height": 140,
            "weight": 135.70,
            "direction": "Free"
        }

    ]

    print("\n=== SET INFO ===")

    volume = calculate_set_volume(
        bom
    )

    weight = calculate_set_weight(
        bom
    )

    print(
        f"SET Volume : {volume:,.0f} mm³"
    )

    print(
        f"SET Weight : {weight/1000:.3f} kg"
    )

    estimate = estimate_max_set(
        900,
        500,
        400,
        bom
    )

    print(
        f"Estimated Max SET : {estimate}"
    )

    print(
        "\n=== PACKING TEST ==="
    )

    max_set = find_max_set_count(
        900,
        500,
        400,
        bom,
        max_set=10
    )

    print(
        "\n====================="
    )

    print(
        f"MAX SET : {max_set}"
    )