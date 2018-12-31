from dioturell import *


def test_printing_escape_colors():
    color_1 = (0, 255, 0)
    color_2 = (255, 0, 255)

    print(f'testing escape characters {color_1} to {color_2}')

    NUM_STEPS = 10

    for step in range(NUM_STEPS + 1):
        ratio = step / NUM_STEPS

        color = interpolate_colors(color_1, color_2, ratio)
        escape_code = get_escape_code_for_color(color)
        print(escape_code)


if __name__ == '__main__':
    test_printing_escape_colors()
