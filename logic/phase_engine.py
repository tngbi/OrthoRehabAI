from datetime import date

def get_phase(surgery_date):

    weeks = (date.today() - surgery_date).days / 7

    if weeks <= 3:
        return "Phase I"
    elif weeks <= 6:
        return "Phase II"
    elif weeks <= 8:
        return "Phase III"
    elif weeks <= 10:
        return "Phase IV"
    elif weeks <= 12:
        return "Phase V"
    elif weeks <= 24:
        return "Phase VI"
    else:
        return "Phase VII"