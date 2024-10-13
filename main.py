from xml.dom import minidom
from svg.path import parse_path
import math


def calculate_arc_bbox(rx, ry, rotation, large_arc_flag, sweep_flag, x1, y1,
                       x2, y2):
    dx = (x1 - x2) / 2
    dy = (y1 - y2) / 2

    rotation_rad = math.radians(rotation)

    x1p = math.cos(rotation_rad) * dx + math.sin(rotation_rad) * dy
    y1p = -math.sin(rotation_rad) * dx + math.cos(rotation_rad) * dy

    rx_sq = rx**2
    ry_sq = ry**2
    x1p_sq = x1p**2
    y1p_sq = y1p**2

    radius_check = x1p_sq / rx_sq + y1p_sq / ry_sq
    if radius_check > 1:
        rx *= math.sqrt(radius_check)
        ry *= math.sqrt(radius_check)
        rx_sq = rx**2
        ry_sq = ry**2

    sign = -1 if large_arc_flag == sweep_flag else 1
    sqrt_term = math.sqrt(
        abs((rx_sq * ry_sq - rx_sq * y1p_sq - ry_sq * x1p_sq) /
            (rx_sq * y1p_sq + ry_sq * x1p_sq)))
    cxp = sign * sqrt_term * (rx * y1p / ry)
    cyp = sign * sqrt_term * (-ry * x1p / rx)

    cx = math.cos(rotation_rad) * cxp - math.sin(rotation_rad) * cyp + (x1 +
                                                                        x2) / 2
    cy = math.sin(rotation_rad) * cxp + math.cos(rotation_rad) * cyp + (y1 +
                                                                        y2) / 2

    top_left_x = cx - rx
    top_left_y = cy - ry
    bottom_right_x = cx + rx
    bottom_right_y = cy + ry

    return (top_left_x, top_left_y), (bottom_right_x, bottom_right_y)

with open('output.txt', 'w') as file:
    doc = minidom.parse('owl.svg')

    paths = doc.getElementsByTagName('path')

    file.write("CPen pen(PS_SOLID, 1, RGB(0, 0, 0));\n")
    file.write("pDC->SelectObject(&pen);\n\n")

    file.write("CBrush brush;\n")
    file.write("brush.CreateStockObject(NULL_BRUSH);\n")
    file.write("pDC->SelectObject(&brush);\n")

    file.write('\n//'+ '-' * 30 + '\n\n')

    file.write('std::vector<std::vector<CPoint>> beziers = {\n')
    first_printed_pair = True
    for ipath, path in enumerate(paths):
        d = path.getAttribute('d')
        parsed = parse_path(d)

        # file.write('Objects:\n' + str(parsed) +'\n')

        if not any(type(obj).__name__ == 'CubicBezier' for obj in parsed):
            continue

        if (first_printed_pair):
            file.write('\t/* Path {} */\n'.format(ipath))

        last_end_coords = None
        bracket_open = False
        first_printed_title = True
        for i, obj in enumerate(parsed):
            obj_type = type(obj).__name__

            start_coords = f'( {obj.start.real:<2.0f}, {obj.start.imag:<2.0f} )'
            end_coords = f'( {obj.end.real:<2.0f}, {obj.end.imag:<2.0f} )'

            # file.write(f'{type(obj).__name__.ljust(15)} {start_coords} -> {end_coords:}\n')

            if obj_type == 'Line' or obj_type == 'Move' or obj_type == 'Arc':
                last_end_coords = end_coords

            if obj_type == 'CubicBezier':
                if (first_printed_pair):
                    first_printed_pair = False
                    first_printed_title = False
                else:
                    if (not bracket_open):
                        if (first_printed_title):
                            file.write(',\n\n')
                            file.write('\t/* Path {} */\n'.format(ipath))
                            first_printed_title = False
                        else:
                            file.write(',\n')

                if last_end_coords is not None:
                    file.write(f'\t{{\n \t\tCPoint{last_end_coords},\n')
                    last_end_coords = None
                    bracket_open = True

                control1_coords = f'( {obj.control1.real:<2.0f}, {obj.control1.imag:<2.0f} )'
                control2_coords = f'( {obj.control2.real:<2.0f}, {obj.control2.imag:<2.0f} )'

                file.write(
                    f'\n\t\tCPoint{control1_coords}, \n\t\tCPoint{control2_coords}, \n\t\tCPoint{end_coords}',
                    )

                if (i + 1 >= len(parsed) or type(parsed[i + 1]).__name__ == 'Line'
                        or type(parsed[i + 1]).__name__ == 'Close'
                        or type(parsed[i + 1]).__name__ == 'Arc') and bracket_open:
                    bracket_open = False
                    file.write('\n\t}',)
                else:
                    file.write(',')
    file.write('\n};\n')

    file.write('\n//'+ '-' * 30 + '\n\n')

    file.write('std::vector<std::vector<CPoint>> lines = {\n')
    first_printed_pair = True
    for ipath, path in enumerate(paths):
        d = path.getAttribute('d')
        parsed = parse_path(d)

        if not any(type(obj).__name__ == 'Line' for obj in parsed):
            continue

        if (first_printed_pair):
            file.write('\t/* Path {} */\n'.format(ipath))

        first_printed_title = True
        for i, obj in enumerate(parsed):

            obj_type = type(obj).__name__

            if obj_type == 'Line':

                start_coords = f'( {obj.start.real:<2.0f}, {obj.start.imag:<2.0f} )'
                end_coords = f'( {obj.end.real:<2.0f}, {obj.end.imag:<2.0f} )'

                if (first_printed_pair):
                    first_printed_pair = False
                    first_printed_title = False
                else:
                    if (first_printed_title):
                        file.write(',\n\n')
                        file.write('\t/* Path {} */\n'.format(ipath))
                        first_printed_title = False
                    else:
                        file.write(',\n')
                file.write(
                    f'\t{{ \n\t\tCPoint{start_coords}, \n\t\tCPoint{end_coords} \n\t}}',
                    )
    file.write('\n};\n')

    file.write('\n//'+ '-' * 30 + '\n\n')

    file.write("std::vector<std::vector<CPoint>> elipses = {\n")
    circles = doc.getElementsByTagName('circle')
    ellipses = doc.getElementsByTagName('ellipse')
    for iellipse, ellipse in enumerate(ellipses):
        cx = float(ellipse.getAttribute('cx'))
        cy = float(ellipse.getAttribute('cy'))
        rx = float(ellipse.getAttribute('rx'))
        ry = float(ellipse.getAttribute('ry'))
        file.write('\n\t/* Ellipse {} */\n'.format(iellipse))
        file.write(
            f'\t{{ \n\t\tCPoint( {cx-rx:<2.0f}, {cy-ry:<2.0f} ), \n\t\tCPoint( {cx+rx:<2.0f}, {cy+ry:<2.0f} ) \n\t}}',
            )
        if (iellipse + 1 < len(ellipses)):
            file.write(',\n')
        else:
            if (len(circles) <= 0):
                file.write('\n')
            else:
                file.write(',\n')

    for icircle, circle in enumerate(circles):
        cx = float(circle.getAttribute('cx'))
        cy = float(circle.getAttribute('cy'))
        rx = float(circle.getAttribute('r'))
        ry = rx
        file.write('\n\t/* Circle {} */\n'.format(icircle))
        file.write(
            f'\t{{ \n\t\tCPoint( {cx-rx:<2.0f}, {cy-ry:<2.0f} ), \n\t\tCPoint( {cx+rx:<2.0f}, {cy+ry:<2.0f} ) \n\t}}',
            )
        if (icircle + 1 < len(circles)):
            file.write(',\n')
    file.write('\n};\n')

    file.write('\n//'+ '-' * 30 + '\n\n')

    file.write("std::vector<std::vector<CPoint>> arcs = {\n")
    first_printed_pair = True
    for ipath, path in enumerate(paths):
        d = path.getAttribute('d')
        parsed = parse_path(d)

        if not any(type(obj).__name__ == 'Arc' for obj in parsed):
            continue

        if (first_printed_pair):
            file.write('\t/* Path {} */\n'.format(ipath))

        first_printed_title = True
        for i, obj in enumerate(parsed):
            obj_type = type(obj).__name__

            if obj_type == 'Arc':

                start_coords = f'( {obj.start.real:<2.0f}, {obj.start.imag:<2.0f} )'
                end_coords = f'( {obj.end.real:<2.0f}, {obj.end.imag:<2.0f} )'

                rx = obj.radius.real
                ry = obj.radius.imag
                rotation = obj.rotation
                large_arc_flag = obj.arc
                sweep_flag = obj.sweep
                x1, y1 = obj.start.real, obj.start.imag
                x2, y2 = obj.end.real, obj.end.imag

                top_left, bottom_right = calculate_arc_bbox(
                    rx, ry, rotation, large_arc_flag, sweep_flag, x1, y1, x2, y2)

                top_left_coords = f'( {top_left[0]:<2.0f}, {top_left[1]:<2.0f} )'
                bottom_right_coords = f'( {bottom_right[0]:<2.0f}, {bottom_right[1]:<2.0f} )'

                rotation = f'( {sweep_flag:<2.0f}, 0 )'

                if (first_printed_pair):
                    first_printed_pair = False
                    first_printed_title = False
                else:
                    if (first_printed_title):
                        file.write(',\n')
                        file.write('\t/* Path {} */\n'.format(ipath))
                        first_printed_title = False
                    else:
                        file.write(',')
                file.write(
                    f'\t{{ \n\t\tCPoint{top_left_coords}, \n\t\tCPoint{bottom_right_coords}, \n\t\tCPoint{start_coords}, \n\t\tCPoint{end_coords},  \n\t\tCPoint{rotation} \n\t}}',
                    )
    file.write('\n};\n')

    file.write('\n//'+ '-' * 30 + '\n\n')

    file.write("""if(beziers.size() > 0)
        for (const auto& vec : beziers) {
            pDC->PolyBezier(&vec[0], vec.size());
        }\n\n""")

    file.write("""if(lines.size() > 0)
        for (const auto& points : lines) {
            pDC->MoveTo(points[0].x, points[0].y);
            pDC->LineTo(points[1].x, points[1].y);
        }\n\n""")

    file.write("""if(elipses.size() > 0)
        for (const auto& points : elipses) {
            pDC->Ellipse(points[0].x, points[0].y, points[1].x, points[1].y);
        }\n\n""")

    file.write("""if (arcs.size() > 0)
        for (const auto& points : arcs) {
            if(points[4].x == 1 )
                pDC->SetArcDirection(AD_CLOCKWISE);
            else
                pDC->SetArcDirection(AD_COUNTERCLOCKWISE);
            pDC->Arc(points[0].x, points[0].y, points[1].x, points[1].y, points[2].x, points[2].y, points[3].x, points[3].y);
        }\n\n""")

    doc.unlink()
