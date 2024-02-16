def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    assert len(rgb) == 3, "Invalid hex color"
    return rgb


def rgb_to_hex(rgb_color: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb_color).upper()


def lighten_color(hex_color: str, factor: float) -> str:
    rgb_color = hex_to_rgb(hex_color)
    new_rgb_color = tuple(
        int(min(255, max(0, c + 255 * factor))) for c in rgb_color
    )
    assert len(new_rgb_color) == 3, "Invalid RGB color"
    return rgb_to_hex(new_rgb_color)


def darken_color(hex_color, factor):
    rgb_color = hex_to_rgb(hex_color)
    new_rgb_color = tuple(
        int(min(255, max(0, c - 255 * factor))) for c in rgb_color
    )
    assert len(new_rgb_color) == 3, "Invalid RGB color"
    return rgb_to_hex(new_rgb_color)


def get_contrasting_fontcolor_for_fillcolor(color):
    # Convert hex color to RGB
    color = color.lstrip("#")
    r, g, b = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    # Calculate relative luminance (per ITU-R BT.709)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Choose black or white text based on luminance
    if luminance > 128:
        return "black"
    else:
        return "white"


if __name__ == "__main__":
    # Example usage:
    hex_code = "#336699"
    brighter_shade = lighten_color(
        hex_code, 0.2
    )  # Adjust the factor to control brightness
    darker_shade = darken_color(
        hex_code, 0.2
    )  # Adjust the factor to control darkness

    print("Original color:", hex_code)
    print("Brighter shade:", brighter_shade)
    print("Darker shade:", darker_shade)
