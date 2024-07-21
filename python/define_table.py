from python.full_reimbursement import define_table
def define_reimbursement_table():

    # Define reimbursement table here, by passing (row_number,row_ycoord0 tuples 
    table_params = define_table((2, 44.5),  # i.e. 2nd row has y-coordinate of 44.5
                                (10,69), 
                                (19,94.35), 
                                (31,128), 
                                (37,144.2))
    return table_params
