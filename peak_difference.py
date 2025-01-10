import pandas as pd


# Calculate percentage differences with the matching dates included
def peakdiff(data, suffix, tolerance=3):
    """
    Calculate percentage differences of peaks between time series.

    Parameters:
    - data: DataFrame containing the time series data.
    - suffix: String suffix representing the time series to compare with the first one.
    - tolerance: Integer number of days to consider for matching peaks.

    Returns:
    - total_matching_peaks: Number of matching peaks found.
    - percentage_diff_scores: List of percentage differences between matching peaks.
    - avg_percentage_diff: Average percentage difference.
    - matching_dates_1: List of dates for peaks in the first time series.
    - matching_dates_2: List of dates for matching peaks in the other time series.
    """
    peak_diff_scores = []
    percentage_diff_scores = []
    matching_dates_1 = []
    matching_dates_2 = []
    used_peaks_2 = set()
    # Convert 'Time' to datetime
    data["Time"] = pd.to_datetime(data["Time"])

    # Identify peaks in the first time series
    peaks_ob = data[data["Local_Max"]]
    total_matching_peaks = 0

    for _, peak_1 in peaks_ob.iterrows():
        peak_time_1 = peak_1["Time"]
        wl_1 = peak_1["WL"]

        # Define the time window for tolerance
        start_date = peak_time_1 - pd.Timedelta(days=tolerance)
        end_date = peak_time_1 + pd.Timedelta(days=tolerance)

        # Find matching peaks in the second time series within the tolerance window
        potential_peaks_2 = data[
            (data[f"Local_Max_{suffix}"] == True)
            & (pd.to_datetime(data["Time"]) >= start_date)
            & (pd.to_datetime(data["Time"]) <= end_date)
        ]

        if not potential_peaks_2.empty:
            # Find the closest peak in time
            potential_peaks_2 = potential_peaks_2.copy()
            potential_peaks_2["Time_Diff"] = abs(
                potential_peaks_2["Time"] - peak_time_1
            )
            closest_peak_2 = potential_peaks_2.loc[
                potential_peaks_2["Time_Diff"].idxmin()
            ]

            # Ensure the peak from series 2 is not used more than once
            if closest_peak_2.name not in used_peaks_2:
                peak_diff = abs(wl_1 - closest_peak_2[f"WL_{suffix}"])
                percentage_diff = (peak_diff / wl_1) * 100
                peak_diff_scores.append(peak_diff)
                percentage_diff_scores.append(percentage_diff)
                matching_dates_1.append(peak_time_1.strftime("%Y-%m-%d"))
                matching_dates_2.append(closest_peak_2["Time"].strftime("%Y-%m-%d"))
                used_peaks_2.add(closest_peak_2.name)
                total_matching_peaks += 1

    # Calculate the average percentage difference
    avg_percentage_diff = (
        sum(percentage_diff_scores) / len(percentage_diff_scores)
        if percentage_diff_scores
        else None
    )

    return (
        total_matching_peaks,
        percentage_diff_scores,
        avg_percentage_diff,
        matching_dates_1,
        matching_dates_2,
    )
