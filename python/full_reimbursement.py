import sys
import csv

# Define the mapping of categories to row numbers
category_to_row = {
    "Travel within Canada (Economy)": 1,
    "Travel to USA from Ontario (Economy)": 2,
    "All other Airfare (Economy)": 3,
    "Travel within Canada (Above-Economy)": 4,
    "Travel to USA from Ontario (Above-Economy)": 5,
    "All other Airfare (Above-Economy)": 6,
    "ON (13%HST)": 7,
    "PEI, NS, NF, NB (15%HST)": 8,
    "All other provinces / territories": 9,
    "USA / International": 10,
    "Per Diem: Canada": 11,
    "Per Diem: USA / International": 12,
    "KMS x 57 cents/km": 13,
    "Travel within Canada (Rail/Bus)": 14,
    "Travel outside Canada (Rail/Bus)": 15,
    "Travel within or outside Canada (Public Transit)": 16,
    "ON (13%HST) (Car Rental)": 17,
    "PEI, NS, NF, NB (15%HST) (Car Rental)": 18,
    "All other provinces / territories (Car Rental)": 19,
    "USA / International (Car Rental)": 20,
    "ON (13%HST) (Meals)": 21,
    "PEI, NS, NF, NB (15%HST) (Meals)": 22,
    "All other provinces / territories (Meals)": 23,
    "USA / International (Meals)": 24,
    "ON (13%HST) (Taxi)": 25,
    "PEI, NS, NF, NB (15%HST) (Taxi)": 26,
    "All other provinces / territories (Taxi)": 27,
    "USA / International (Taxi)": 28,
    "OTHER": 29
}

def define_categories(table_params):
    categories = [
        ExpenseCategory("AIRFARE: ECONOMY", ["Travel within Canada (Economy)", "Travel to USA from Ontario (Economy)", "All other Airfare (Economy)"], table_params),
        ExpenseCategory("AIRFARE: ABOVE-ECONOMY", ["Travel within Canada (Above-Economy)", "Travel to USA from Ontario (Above-Economy)", "All other Airfare (Above-Economy)"], table_params),
        ExpenseCategory("ACCOMMODATION", ["ON (13%HST)", "PEI, NS, NF, NB (15%HST)", "All other provinces / territories", "USA / International"], table_params),
        ExpenseCategory("ALLOWANCE", ["Per Diem: Canada", "Per Diem: USA / International", "KMS x 57 cents/km"], table_params),
        ExpenseCategory("RAIL/BUS", ["Travel within Canada (Rail/Bus)", "Travel outside Canada (Rail/Bus)"], table_params),
        ExpenseCategory("PUBLIC TRANSIT", ["Travel within or outside Canada (Public Transit)"], table_params),
        ExpenseCategory("CAR RENTAL", ["ON (13%HST) (Car Rental)", "PEI, NS, NF, NB (15%HST) (Car Rental)", "All other provinces / territories (Car Rental)", "USA / International (Car Rental)"], table_params),
        ExpenseCategory("MEALS", ["ON (13%HST) (Meals)", "PEI, NS, NF, NB (15%HST) (Meals)", "All other provinces / territories (Meals)", "USA / International (Meals)"], table_params),
        ExpenseCategory("TAXI", ["ON (13%HST) (Taxi)", "PEI, NS, NF, NB (15%HST) (Taxi)", "All other provinces / territories (Taxi)", "USA / International (Taxi)"], table_params),
    ]
    return categories

class ExpenseCategory:
    def __init__(self, name, options, table_params):
        self.name = name
        self.options = options
        self.table_params = table_params
        self.selected_options = {}
        self.selected_indices = []

    def select_options(self):
        print()
        print(f"Please select the options you want to fill in for {self.name}:")
        for i, option in enumerate(self.options, 1):
            print(f"{i}. {option}")
        selected_string = input("Select the options (as a single string of numbers, e.g., 134) or press Enter to skip: ").strip()
        
        if selected_string.lower() == 'u':
            return 'undo'
        
        if selected_string == '':
            self.selected_indices = []
        else:
            self.selected_indices = [int(char) for char in selected_string if char.isdigit() and 1 <= int(char) <= len(self.options)]
        
        return 'continue'

    def fill_values(self):
        for index in self.selected_indices:
            print()
            value = input(f"Enter the value for {self.options[index - 1]}: ")
            self.selected_options[self.options[index - 1]] = value

    def get_pdf_array(self, font, size):
        pdf_array = []
        for option, value in self.selected_options.items():
            x = 140  # Assuming a fixed x position for now
            y = getrow(category_to_row[option], self.table_params)
            pdf_array.append((x, y, '$' + str(float(value)), font, size))
        return pdf_array

class OtherExpenses:
    def __init__(self, table_params):
        self.table_params = table_params
        self.expenses = []

    def ask_other_expenses(self):
        max_other_expenses = 6
        count = 0

        while count < max_other_expenses:
            remaining = max_other_expenses - count
            print()
            expense_name = input(f"Please insert the name for the other expense ({remaining} left) or press Enter to finish: ").strip()
            
            if expense_name == '':
                break
            
            if expense_name.lower() == 'u' and self.expenses:
                self.expenses.pop()
                count -= 1
                print("Last entry undone.")
                continue

            expense_amount = input(f"Enter the monetary amount for the expense '{expense_name}': ").strip()
            self.expenses.append((expense_name, expense_amount))
            count += 1

    def add_expense(self, name, amount):
        self.expenses.append((name, amount))

    def get_pdf_array(self, font, size):
        pdf_array = []
        base_x = 140  # Base x position for the monetary amount
        name_x = 96   # x position for the expense name
        start_row = 29  # Starting row number for other expenses

        for index, (name, amount) in enumerate(self.expenses):
            y = getrow(start_row + index, self.table_params)
            pdf_array.append((name_x, y, name, font, size))
            pdf_array.append((base_x, y, '$' + str(float(amount)), font, size))
        
        return pdf_array

def fill_expenses_from_csv(table_params, font, size, csv_file):
    def get_sum_for_subcategory(subcategory, csv_data):
        summed_expenses = sum(float(row['amount']) for row in csv_data if row['subcategory'] == subcategory)
        formatted_sum = round(summed_expenses, 2)
        return formatted_sum

    # Load CSV data
    csv_data = []
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            csv_data.append(row)

    # Define categories
    categories = define_categories(table_params)
    other_expenses = OtherExpenses(table_params)

    # Fill in the values from the CSV data
    for category in categories:
        for subcategory in category.options:
            subcategory_number = category_to_row.get(subcategory)
            if subcategory_number is not None:
                total_amount = get_sum_for_subcategory(str(subcategory_number), csv_data)
                if total_amount > 0:
                    category.selected_options[subcategory] = total_amount

    # Handle "OTHER" expenses separately
    for row in csv_data:
        subcategory = row['subcategory']
        try:
            int_subcategory = int(subcategory)
            if int_subcategory not in category_to_row.values():
                other_expenses.add_expense(subcategory, row['amount'])
        except ValueError:
            other_expenses.add_expense(subcategory, row['amount'])

    # Generate the PDF array
    pdf_array = []
    for category in categories:
        pdf_array.extend(category.get_pdf_array(font, size))

    # Add other expenses to the PDF array
    pdf_array.extend(other_expenses.get_pdf_array(font, size))
    
    return pdf_array

def manual_spending_insert(table_params, font, size):
    
    categories = define_categories(table_params)

    current_category = 0
    while current_category < len(categories):
        action = categories[current_category].select_options()
        if action == 'undo':
            if current_category > 0:
                current_category -= 1
            else:
                print("Already at the first category, cannot undo further.")
        else:
            current_category += 1

    for category in categories:
        category.fill_values()
    
    pdf_array = []
    for category in categories:
        pdf_array.extend(category.get_pdf_array(font, size))
    
    other_expenses = OtherExpenses(table_params)
    other_expenses.ask_other_expenses()
    pdf_array.extend(other_expenses.get_pdf_array(font, size))    
    return pdf_array

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
