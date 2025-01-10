from scipy.signal import find_peaks
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Function to load observed and predicted data
def load_time_series(data, test_dates, name):
    return pd.DataFrame(
        {"Time": pd.to_datetime(test_dates), "WL": pd.Series(data.flatten(), name=name)}
    )


# Function to identify the base groundwater level.
def calculate_stable_mean(data, column_name, threshold=0.05, min_stable_length=6):
    # Calculate the differences between consecutive values
    diffs = data[column_name].diff().abs()
    # Identify periods where the diff is below the threshold
    stable_periods = diffs < threshold
    # Find indices where the stable periods are long enough
    stable_indices = []
    current_stable_start = None
    for i in range(len(stable_periods)):
        if stable_periods.iloc[i]:
            if current_stable_start is None:
                current_stable_start = i
        else:
            if (
                current_stable_start is not None
                and (i - current_stable_start) >= min_stable_length
            ):
                stable_indices.extend(range(current_stable_start, i))
            current_stable_start = None

    # If the stable period extends to the end of the series, check the last stable period
    if (
        current_stable_start is not None
        and (len(stable_periods) - current_stable_start) >= min_stable_length
    ):
        stable_indices.extend(range(current_stable_start, len(stable_periods)))

    # Get the stable values based on the identified indices
    stable_values = data[column_name].iloc[stable_indices]

    # Calculate the mean of the stable values or handle the case where no stable period is found
    if not stable_values.empty:
        stable_mean_value = stable_values.mean()
    else:
        stable_mean_value = data[column_name].min()  # Use the lowest point
        print("Caution! No stable period detected, lowest point used.")

    return stable_mean_value


# Function to identify peaks and jump points
def identify_points(data, column_name, thresholdmp):
    # Calculate the local maxima
    peaks, _ = find_peaks(data[column_name])
    local_maxima = data[column_name].iloc[peaks]
    # Calculate the base groundwater level
    stable_mean = calculate_stable_mean(
        data, column_name, threshold=0.05, min_stable_length=6
    )
    print(f"The mean value during stable periods is: {stable_mean}")
    # Calculate the threshold_diff
    threshold_diff = (local_maxima - stable_mean).mean() / thresholdmp
    print("Threshold:", threshold_diff)
    # Identify points where WL starts to rise and fall
    data["WL_diff"] = data[column_name].diff()
    data["Rise"] = (data["WL_diff"] > threshold_diff).shift(-1).fillna(False)
    # Initialize an empty list to store the local maxima indices
    local_max_indices = []
    # Scan through the points after start rise, once start to fall mark as local max
    for i in range(len(data)):
        if data["Rise"].iloc[i]:
            for j in range(i + 1, len(data)):
                if data["WL_diff"].iloc[j] < 0:
                    local_max_indices.append(j)
                    break
    # Mark the local maxima in the dataframe
    data["Local_Max"] = data.index.isin(local_max_indices)
    data["Local_Max"] = data["Local_Max"].shift(-1).fillna(False)

    return data


# Function to plot the observed and predicted time series with identified points
def plot_observed_predicted_points(
    test_dates, data_observed, observedpoints, data_predicted, predictedpoints
):
    plt.figure(figsize=(12, 8))
    plt.plot(
        test_dates, data_observed["WL"], marker="o", linestyle="-", label="Observed WL"
    )
    plt.plot(
        test_dates,
        data_predicted["WL"],
        marker="o",
        linestyle="-",
        label="Predicted WL",
    )
    plt.scatter(
        test_dates[observedpoints["Rise"]],
        observedpoints["WL"][observedpoints["Rise"]],
        color="green",
        label="Rise Points (Observed)",
        zorder=5,
    )
    plt.scatter(
        test_dates[observedpoints["Local_Max"]],
        observedpoints["WL"][observedpoints["Local_Max"]],
        color="red",
        label="Peak Points (Observed)",
        zorder=5,
    )
    plt.scatter(
        test_dates[predictedpoints["Rise"]],
        predictedpoints["WL"][predictedpoints["Rise"]],
        color="blue",
        label="Rise Points (Predicted)",
        zorder=5,
    )
    plt.scatter(
        test_dates[predictedpoints["Local_Max"]],
        predictedpoints["WL"][predictedpoints["Local_Max"]],
        color="purple",
        label="Peak Points (Predicted)",
        zorder=5,
    )
    plt.xlabel("Date")
    plt.ylabel("WL")
    plt.title(
        "Observed and Predicted WL over Time with Start Rise and Local Max Points"
    )
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.xticks([test_dates.index[i] for i in np.arange(0, len(test_dates) - 2, 10)])
    plt.tight_layout()
    plt.show()


# Function to find jump points after each local max
def find_jump_points(start_rise_series, local_max_series):
    jump_points = pd.Series(False, index=start_rise_series.index)
    modified_start_rise = start_rise_series.copy()

    # Find the very first start rise point
    first_start_rise_index = (
        modified_start_rise.idxmax()
    )  # idxmax returns the first occurrence of the maximum value (True)
    if first_start_rise_index:
        jump_points.iloc[first_start_rise_index] = True
        modified_start_rise.iloc[first_start_rise_index] = False

    for i in range(len(local_max_series)):
        if local_max_series.iloc[i]:  # If this is a local max point
            # Find the next start rise point after the local max
            for j in range(i + 1, len(start_rise_series)):
                if start_rise_series.iloc[j]:  # If this is a start rise point
                    jump_points.iloc[j] = True  # Mark as a jump point
                    modified_start_rise.iloc[j] = False  # Remove it from start rise
                    break

    return jump_points, modified_start_rise


# Function to plot all the critical points (including jump points) identified in both series
def plot_criticalpoints(
    test_dates,
    combined_df,
    wl_column="WL_1",
    title="Observed and Predicted WL over Time with Start Rise and Local Max Points",
):
    plt.figure(figsize=(12, 6), dpi=200)
    plt.plot(
        test_dates,
        combined_df["WL"],
        linestyle="dotted",
        label="Observed GWL",
        linewidth=3,
    )
    plt.plot(
        test_dates,
        combined_df[wl_column],
        linestyle="-",
        label="Predicted GWL",
        linewidth=3,
    )

    # plt.scatter(
    #     test_dates[combined_df["Rise"]],
    #     combined_df["WL"][combined_df["Rise"]],
    #     color="green",
    #     label="Rising Points (Observed)",
    #     s=100,
    #     zorder=5,
    # )
    plt.scatter(
        test_dates[combined_df["Local_Max"]],
        combined_df["WL"][combined_df["Local_Max"]],
        color="#1f77b4",
        label="Peak Points (Observed)",
        s=100,
        zorder=5,
        marker="^",
    )
    plt.scatter(
        test_dates[combined_df["jump_point"]],
        combined_df["WL"][combined_df["jump_point"]],
        color="#1f77b4",
        label="Jump Points (Observed)",
        s=100,
        zorder=5,
    )

    # plt.scatter(
    #     test_dates[combined_df[f'Rise_{wl_column.split("_")[1]}']],
    #     combined_df[wl_column][combined_df[f'Rise_{wl_column.split("_")[1]}']],
    #     color="green",
    #     label="Rising Points (Predicted)",
    #     marker="^",
    #     s=100,
    #     zorder=5,
    # )
    plt.scatter(
        test_dates[combined_df[f'Local_Max_{wl_column.split("_")[1]}']],
        combined_df[wl_column][combined_df[f'Local_Max_{wl_column.split("_")[1]}']],
        color="#ff7f0e",
        label="Peak Points (Predicted)",
        marker="^",
        s=100,
        zorder=5,
    )
    plt.scatter(
        test_dates[combined_df[f'jump_point_{wl_column.split("_")[1]}']],
        combined_df[wl_column][combined_df[f'jump_point_{wl_column.split("_")[1]}']],
        color="#ff7f0e",
        label="Jump Points (Predicted)",
        s=100,
        zorder=5,
    )

    plt.xlabel("Date", fontsize=16)
    plt.ylabel("Groundwater Level (m)", fontsize=16)
    plt.ylim(0, 2.2)
    plt.yticks(fontsize=16)
    plt.grid(False)
    plt.xticks(rotation=0, fontsize=16)
    plt.xticks(
        [test_dates.index[i] for i in np.arange(0, len(test_dates), 10)], fontsize=12
    )
    plt.title(title, fontsize=16)
    plt.legend(fontsize=16)
    plt.tight_layout()
