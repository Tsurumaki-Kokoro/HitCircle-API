def rating_to_wn8_hex(rating: float, win_rate: float) -> tuple[float, str]:
    # Assuming the rating 2.5 maps linearly to 2900 WN8, create a conversion factor
    rating_to_wn8_factor = 2900 / 2

    # Convert the rating to WN8 using the factor and weight for rating
    wn8_rating = rating * rating_to_wn8_factor * 0.6

    # Add the weighted win rate component (assuming max win rate is 100% equivalent to WN8 2900+)
    wn8_rating += (win_rate / 100) * 2900 * 0.4

    # Define the WN8 ranges and corresponding hex colors from the image
    wn8_ranges_hex_colors = [
        (0, 300, '#871F17'),  # Very Bad
        (300, 449, '#BD413A'),  # Bad
        (450, 649, '#C17E2B'),  # Below Average
        (650, 899, '#C9B93C'),  # Average
        (900, 1199, '#899B3B'),  # Above Average
        (1200, 1599, '#557232'),  # Good
        (1600, 1999, '#5998BC'),  # Very Good
        (2000, 2449, '#4871C1'),  # Great
        (2450, 2899, '#7141AF'),  # Unicum
        (2900, float('inf'), '#3A136B')  # Super Unicum
    ]

    # Determine the hex color based on the WN8 rating
    for lower_bound, upper_bound, hex_color in wn8_ranges_hex_colors:
        if lower_bound <= int(wn8_rating) <= upper_bound:
            return wn8_rating, hex_color
    return wn8_rating, "#FFFFFF"  # Default color (white) if not found


def score_to_3digit(score: int) -> str:
    if score > 1000000:
        short_score = score / 1000000
        return f"{short_score:.2f}M"
    elif score > 1000:
        short_score = score / 1000
        return f"{short_score:.2f}K"
    return str(score)
