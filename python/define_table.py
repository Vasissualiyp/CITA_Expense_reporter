from python.full_reimbursement import define_table

# Configuration dictionary for easy switching between modes
reimbursement_config = {
    'default': {
        'rows': [(2, 44.5), (10, 69), (19, 94.35), (31, 128), (37, 144.2)],
        'columns': [20, 51, 140],
        'font_size': [2, 2.5]
    },
    'custom': {
        'rows': [(20, 445.0), (100, 690.0), (190, 943.5), (310, 1280.0), (370, 1442.0)],
        'columns': [30, 200, 560],
        'font_size': [8, 10]
    }
}

def define_reimbursement_table(mode):
    config = reimbursement_config.get(mode, reimbursement_config['default'])
    return (define_table(*config['rows']),
            config['columns'],
            config['font_size'])

