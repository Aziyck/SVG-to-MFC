from xml.dom import minidom
from svg.path import parse_path

# Add this before OnDraw function
# -------------------------------------
# enum ShapeType 
# { 
# 	BEZIER, 
# 	LINE 
# };

# struct Shape
# {
# 	ShapeType type;
# 	std::vector<CPoint> points;

# 	Shape(ShapeType t, std::vector<CPoint> pts) : type(t), points(pts) {}
# };
# -------------------------------------


with open('output.txt', 'w') as file:
    doc = minidom.parse('lineart.svg')
    paths = doc.getElementsByTagName('path')

    # Header
    file.write("CPen pen(PS_SOLID, 1, RGB(0, 0, 0));\n")
    file.write("pDC->SelectObject(&pen);\n\n")
    file.write("CBrush brush;\n")
    file.write("brush.CreateStockObject(NULL_BRUSH);\n")
    file.write("pDC->SelectObject(&brush);\n")
    file.write('\n//'+ '-' * 30 + '\n\n')

    file.write('std::vector<std::vector<Shape>> paths = {\n')
    first_printed_pair = True
    for ipath, path in enumerate(paths):
        d = path.getAttribute('d')
        parsed = parse_path(d)

        # file.write('Objects:\n' + str(parsed) +'\n')

        if (first_printed_pair):
            file.write('\t/* Path {} */\n\t{{\n'.format(ipath))

        last_end_coords = None
        bracket_open = False
        first_printed_title = True
        for i, obj in enumerate(parsed):
            obj_type = type(obj).__name__

            start_coords = f'( {obj.start.real:<2.0f}, {obj.start.imag:<2.0f} )'
            end_coords = f'( {obj.end.real:<2.0f}, {obj.end.imag:<2.0f} )'

            if obj_type == 'Line' or obj_type == 'Move' or obj_type == 'Arc':
                last_end_coords = end_coords
                if obj_type == 'Line':

                    if (first_printed_pair):
                        first_printed_pair = False
                        first_printed_title = False
                    else:
                        if (first_printed_title):
                            file.write(',\n\n')
                            file.write('\t}},\n\t/* Path {} */\n\t{{\n'.format(ipath))
                            first_printed_title = False
                        else:
                            file.write(',\n')
                    file.write(
                        f'\tShape(LINE, {{ \n\t\tCPoint{start_coords}, \n\t\tCPoint{end_coords} \n\t}})',
                        )

            if obj_type == 'CubicBezier':
                if (first_printed_pair):
                    first_printed_pair = False
                    first_printed_title = False
                else:
                    if (not bracket_open):
                        if (first_printed_title):
                            file.write(',\n\n')
                            file.write('\t}},\n\t/* Path {} */\n\t{{\n'.format(ipath))
                            first_printed_title = False
                        else:
                            file.write(',\n')

                if last_end_coords is not None:
                    file.write(f'\tShape(BEZIER, {{\n \t\tCPoint{last_end_coords},\n')
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
                    file.write('\n\t})',)
                else:
                    file.write(',')
        if(ipath == len(paths) - 1):   
             file.write('\n\n\t}',)
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
    
    file.write("""if (!paths.empty()) 
	for (const auto& path : paths) {  
		for (const auto& shape : path) {  
			if (shape.type == BEZIER) {
				if (!shape.points.empty()) {
					pDC->PolyBezier(&shape.points[0], shape.points.size());
				}
			}
			else if (shape.type == LINE) {
				if (shape.points.size() >= 2) {
					pDC->MoveTo(shape.points[0].x, shape.points[0].y);
					pDC->LineTo(shape.points[1].x, shape.points[1].y);
				}
			}
		}
	}\n\n""")

    file.write("""if(elipses.size() > 0)
    for (const auto& points : elipses) {
        pDC->Ellipse(points[0].x, points[0].y, points[1].x, points[1].y);
    }\n\n""")


    doc.unlink()
