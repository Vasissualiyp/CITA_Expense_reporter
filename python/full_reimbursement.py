row1=2
y1=44.5
row2=38
y2=144.2

def define_table(row1, y1, row2, y2):
    """
    A function that defines a connection between the row of the table and 
    its y-coordinate, based on coordinates of 2 cells.
    Parameters:
        row1 (int) - index of the first row
        y1 (float) - coordinate of the first row
        row2 (int) - index of the second row
        y2 (float) - coordinate of the second row
    Returns:
        (k, b) (tuple) - parameters of the linear funciton that connects the row id with
                 its coordinate
    """
    dx = row2 - row1
    dy = y2 - y1
    k = dy / dx
    b = y2 - row2 * k
    return (k, b)

def getrow(rowno, table_definitions):
    """
    A function to obtain the y coordinate of a row of evenly-spaced table
    from the linear coefficients, passed to it.
    Parameters:
        rowno (int) - number of a row of interest
        table_definitions (tuple) - (k, b), linear coefficients
    Returns:
        y (float) - the y coordinate of the row of interest
    """
    k, b = table_definitions
    y = k * rowno + b
    return y

def generate_texts(font, table_params):
    texts = []
    for i in range(1, 38):
        x = 140
        y = getrow(i, table_params)
        string = f"row {i}"
        size = 2
        texts.append((x, y, string, font, size))
    return texts

table_params = define_table(row1, y1, row2, y2)

#print(getrow(30, table_params))
