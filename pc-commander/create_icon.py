from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        margin = max(2, size // 16)
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=size // 6,
            fill="#1a1a2e"
        )

        inner_margin = size // 8
        draw.rounded_rectangle(
            [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
            radius=size // 8,
            outline="#4fc3f7",
            width=max(1, size // 20)
        )

        screen_x1 = size // 5
        screen_y1 = size // 4
        screen_x2 = 4 * size // 5
        screen_y2 = 3 * size // 5

        draw.rounded_rectangle(
            [screen_x1, screen_y1, screen_x2, screen_y2],
            radius=max(1, size // 16),
            fill="#4fc3f7"
        )

        dot_y = screen_y2 + (size - screen_y2) // 2
        dot_r = max(1, size // 16)
        draw.ellipse(
            [size // 2 - dot_r, dot_y - dot_r, size // 2 + dot_r, dot_y + dot_r],
            fill="#4fc3f7"
        )

        images.append(img)

    os.makedirs("assets", exist_ok=True)
    images[0].save(
        "assets/icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    images[-1].save("assets/logo.png")
    print("Icon created: assets/icon.ico")


if __name__ == "__main__":
    create_icon()
