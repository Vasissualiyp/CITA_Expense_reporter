row1=2
y1=44.5
row2=10
y2=69
row3=19
y3=94.35
row4=31
y4=128
row5=37
y5=144.2


def define_table(*points):
    """
    A function that defines a piecewise-linear connection between the row of the table and
    its y-coordinate, based on coordinates of multiple cells.
    Parameters:
        *points (tuple) - an arbitrary number of tuples (row, y-coordinate)
    Returns:
        segments (list) - list of tuples, each containing (k, b, start_row, end_row)
    """
    segments = []
    for i in range(len(points) - 1):
        row1, y1 = points[i]
        row2, y2 = points[i + 1]
        dx = row2 - row1
        dy = y2 - y1
        k = dy / dx
        b = y1 - k * row1
        segments.append((k, b, row1, row2))
    return segments

def getrow(rowno, segments):
    """
    A function to obtain the y coordinate of a row of evenly-spaced table
    from the piecewise-linear coefficients, passed to it.
    Parameters:
        rowno (int) - number of a row of interest
        segments (list) - list of tuples, each containing (k, b, start_row, end_row)
    Returns:
        y (float) - the y coordinate of the row of interest
    """
    if rowno < segments[0][2]:  # Before the first segment
        k, b, _, _ = segments[0]
        y = k * rowno + b
    elif rowno > segments[-1][3]:  # After the last segment
        k, b, _, _ = segments[-1]
        y = k * rowno + b
    else:  # Within the defined segments
        for k, b, start_row, end_row in segments:
            if start_row <= rowno <= end_row:
                y = k * rowno + b
                break
    return y

def generate_texts(font, table_params):
    texts = []
    for i in range(1, 38):
        x = 140
        y = getrow(i, table_params)
        string = f"row {i}"
        size = 2
        print(f'For {string}, y={y}')
        texts.append((x, y, string, font, size))
    return texts

table_params = define_table((row1, y1), (row2, y2), (row3, y3), (row4, y4), (row5, y5))

#print(getrow(30, table_params))
