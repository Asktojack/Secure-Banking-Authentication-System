def calculate_risk(amount, new_device=False, different_city=False):

    risk = 0

    # Amount Risk
    if amount >= 1000000:
        risk += 60

    elif amount >= 100000:
        risk += 40

    elif amount >= 50000:
        risk += 20

    # Device Risk
    if new_device:
        risk += 20

    # Location Risk
    if different_city:
        risk += 20

    if risk > 100:
        risk = 100

    return risk