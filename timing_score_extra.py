def timingdiff_extra(data, suffix, output_filename, tolerance=3):
    import pandas as pd
    """
    Calculate timing differences of peaks and jumps between time series.

    Parameters:
    - data: DataFrame containing the time series data.
    - suffix: String suffix representing the time series to compare with the first one
    - tolerance: Integer number of days to consider for matching peaks and jumps.

    Returns:
    - avg_peak_timing_diff: Average timing difference for peaks.
    - avg_jump_timing_diff: Average timing difference for jumps.
    - combined_score: Combined average score of peak and jump timing differences.
    - peak_timing_diff_scores: List of timing differences for peaks.
    - jump_timing_diff_scores: List of timing differences for jumps.
    - peak_matching_dates_1: List of dates for peaks in the first time series.
    - peak_matching_dates_2: List of dates for matching peaks in the other time series.
    - jump_matching_dates_1: List of dates for jumps in the first time series.
    - jump_matching_dates_2: List of dates for matching jumps in the other time series.
    """


    def find_closest_point_with_dates(target_time, potential_points, used_set):
        if potential_points.empty:
            return None, None
        
        potential_points = potential_points.copy()
        potential_points["Time_Diff"] = abs(potential_points["Time"] - target_time)
        closest_point = potential_points.loc[potential_points["Time_Diff"].idxmin()]

        if closest_point.name not in used_set:
            used_set.add(closest_point.name)
            timing_diff = abs((closest_point["Time"] - target_time).days)
            closest_time = closest_point["Time"].strftime("%Y-%m-%d")
            return timing_diff, closest_time
        else:
            return None, None

    def process_points_with_dates(series_1, label_2, used_set, matching_dates_1, matching_dates_2):
        timing_diff_scores = []

        for _, point_1 in series_1.iterrows():
            point_time_1 = point_1["Time"]

            # Define the time window for tolerance
            start_date = point_time_1 - pd.Timedelta(days=tolerance)
            end_date = point_time_1 + pd.Timedelta(days=tolerance)

            # Find matching points in the second time series within the tolerance window
            potential_points_2 = data[
                (data[label_2] == True)
                & (data["Time"] >= start_date)
                & (data["Time"] <= end_date)
            ]

            timing_diff, closest_time = find_closest_point_with_dates(
                point_time_1, potential_points_2, used_set
            )

            if timing_diff is not None:
                matching_dates_1.append(point_time_1.strftime("%Y-%m-%d"))
                matching_dates_2.append(closest_time)
            else:
                # Apply penalty for unmatched points
                timing_diff = tolerance + 1
                matching_dates_1.append(point_time_1.strftime("%Y-%m-%d"))
                matching_dates_2.append(None)

            timing_diff_scores.append(timing_diff)

        return timing_diff_scores
    
    peak_timing_diff_scores = []
    jump_timing_diff_scores = []
    peak_matching_dates_1 = []
    peak_matching_dates_2 = []
    jump_matching_dates_1 = []
    jump_matching_dates_2 = []
    used_peaks_2 = set()
    used_jumps_2 = set()

    # Convert 'Time' to datetime
    data["Time"] = pd.to_datetime(data["Time"])

    # Identify peaks and jump points in the first time series
    peaks_1 = data[data["Local_Max"] == True]
    jumps_1 = data[data["jump_point"] == True]

    # Process peak points
    peak_timing_diff_scores = process_points_with_dates(
        peaks_1,
        f"Local_Max_{suffix}",
        used_peaks_2,
        peak_matching_dates_1,
        peak_matching_dates_2,
    )
    # Process jump points
    jump_timing_diff_scores = process_points_with_dates(
        jumps_1,
        f"jump_point_{suffix}",
        used_jumps_2,
        jump_matching_dates_1,
        jump_matching_dates_2,
    )

    # Apply extra point penalty for unmatched points in the second time series
    def apply_extra_point_penalty(
        label_2, used_set, timing_diff_scores, matching_dates_1, matching_dates_2
    ):
        extra_points = data[data[label_2] & ~data.index.isin(used_set)]
        extra_penalty = tolerance + 1
        for _, point_2 in extra_points.iterrows():
            timing_diff_scores.append(extra_penalty)
            # Append None for matching_dates_1 as there is no corresponding point in the first time series
            matching_dates_1.append(None)
            # Append the date of the extra point in the second time series
            matching_dates_2.append(point_2["Time"].strftime("%Y-%m-%d"))

    # Apply penalties for extra peaks and jumps in the second time series
    apply_extra_point_penalty(
        f"Local_Max_{suffix}",
        used_peaks_2,
        peak_timing_diff_scores,
        peak_matching_dates_1,
        peak_matching_dates_2,
    )
    apply_extra_point_penalty(
        f"jump_point_{suffix}",
        used_jumps_2,
        jump_timing_diff_scores,
        jump_matching_dates_1,
        jump_matching_dates_2,
    )

    # Calculate average timing differences
    avg_peak_timing_diff = (
        sum(peak_timing_diff_scores) / len(peak_timing_diff_scores)
        if peak_timing_diff_scores
        else float("inf")
    )
    avg_jump_timing_diff = (
        sum(jump_timing_diff_scores) / len(jump_timing_diff_scores)
        if jump_timing_diff_scores
        else float("inf")
    )

    # Combined score (weighted by the number of valid timing differences)
    if peak_timing_diff_scores and jump_timing_diff_scores:
        combined_score = (
            sum(peak_timing_diff_scores) + sum(jump_timing_diff_scores)
        ) / (len(peak_timing_diff_scores) + len(jump_timing_diff_scores))
    elif peak_timing_diff_scores:
        combined_score = avg_peak_timing_diff
    elif jump_timing_diff_scores:
        combined_score = avg_jump_timing_diff
    else:
        combined_score = float("inf")

    # Determine the maximum length for alignment
    max_len = max(
        len(peak_timing_diff_scores),
        len(jump_timing_diff_scores),
        len(peak_matching_dates_1),
        len(peak_matching_dates_2),
        len(jump_matching_dates_1),
        len(jump_matching_dates_2)
    )

    # Pad the lists to ensure all columns have the same length
    def pad_list(lst, target_length, pad_value=None):
        return lst + [pad_value] * (target_length - len(lst))

    # Pad peaks and jumps
    peak_matching_dates_1_padded = pad_list(peak_matching_dates_1, max_len)
    peak_matching_dates_2_padded = pad_list(peak_matching_dates_2, max_len)
    peak_timing_diff_scores_padded = pad_list(peak_timing_diff_scores, max_len)
    jump_matching_dates_1_padded = pad_list(jump_matching_dates_1, max_len)
    jump_matching_dates_2_padded = pad_list(jump_matching_dates_2, max_len)
    jump_timing_diff_scores_padded = pad_list(jump_timing_diff_scores, max_len)

    # Tabulate the results with dates
    results_df_timing_with_dates_extra = pd.DataFrame(
        {
            "Matching_Index": list(range(1, max_len + 1)),
            "Date_WL_Peak": peak_matching_dates_1_padded,
            "Date_WL_1_Peak": peak_matching_dates_2_padded,
            "Peak_Timing_Difference": peak_timing_diff_scores_padded,
            "Date_WL_Jump": jump_matching_dates_1_padded,
            "Date_WL_1_Jump": jump_matching_dates_2_padded,
            "Jump_Timing_Difference": jump_timing_diff_scores_padded,
        }
    )

    # Save the results to a CSV file
    results_df_timing_with_dates_extra.to_csv(output_filename, index=False)

    return avg_peak_timing_diff, avg_jump_timing_diff, combined_score
