from python.full_reimbursement import define_table

# Configuration dictionary for easy switching between modes
reimbursement_config = {
    'default': {
        'rows': [(2, 44.5), (10, 69), (19, 94.35), (31, 128), (37, 144.2)],
        'columns': [20, 51, 96, 140],
        'font_size': [2, 2.5],
        'student_signature': [25, 30, 6]
    },
    'custom': {
        'rows': [(2, 175), (10, 265), (13,289), (17, 340), (31, 490), (37, 553)],
        'columns': [22, 140, 320, 487],
        'font_size': [8, 10],
        'student_signature': [17, 120, 24]
    }
}

def define_reimbursement_table(mode):
    config = reimbursement_config.get(mode, reimbursement_config['default'])
    return (define_table(*config['rows']),
            config['columns'],
            config['font_size'],
            config['student_signature'])

