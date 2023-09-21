"""
Script to plot the scaling relationship betwen the sizes of reshare and exposure cascades. 
"""

import ijson
import gzip
import os
import glob
import sys
import numpy as np

import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as stats
import scipy.optimize as optimization

## Config
bot_color = "#F18447"  # orange
human_color = "#550F6B"  # purple
# Make sure "stylesheet.mplstyle" exists, or comment out this line
plt.style.use("stylesheet.mplstyle")


def read_ijson_compressed(fpath):
    """
    Read data using ijson to avoid memory error for large json files 
    Data is a list containing message information 
    """
    fin = gzip.open(fpath, "r")
    json_bytes = fin.read()
    # Return the message information of the first run
    objects = ijson.items(json_bytes, "all_messages.item")
    data = [i for i in objects]  # convert ijson item obj into list
    return data


def linear_func(x, a, b):
    return a * x + b


def exp_func(x, a, b):
    return np.exp(a * np.log(x)) * np.exp(b)


def plot_cascade_scaling_with_fitted_line(
    data,
    ax,
    min_x=None,
    max_x=None,
    annotate=False,
    x_label=False,
    y_label=False,
    fitline_color="black",
    fitline_shift=0.4,
    point_color="orange",
    alpha=1,
    label="",
):
    """
    Plots log reshare cascade size vs log exposure cascade size. Fit a linear line for scaling reference 
    - data (pd DataFrame): df of at least 2 columns seen_by_agents (exposure), spread_via_agents (reshare). Returned by data_reshare_vs_exposure()
    - ax: matplotlib axis to plot on
    - min_x, max_x (int): respectively the minimum and maximum range of x to fit the linear reference
    Other formatting options:
    - annotate (bool): if True, annotate the plot with the slope of linear line
    - fitline_shift (float): shift the line a bit so it's not overlap with scatter data points
    - x_label, y_label (bool): if True, label the axis
    """
    # plot actual data
    ax.scatter(
        x=data["spread_via_agents"],
        y=data["seen_by_agents"],
        s=9,
        color=point_color,
        alpha=alpha,
        label=label,
    )

    # Subset data within range
    short = data
    if min_x is not None:
        short = short[short.spread_via_agents >= min_x]

    if max_x is not None:
        short = short[short.spread_via_agents <= max_x]

    # Make sure data is of correct type so fitting works properly
    short = short.astype(
        {"seen_by_agents": np.float64, "spread_via_agents": np.float64}
    )
    x = np.log(short["spread_via_agents"])
    y = np.log([val if val > 0 else 1 for val in short["seen_by_agents"]])

    # Fit a linear line —- equivalent to stats.linregress()
    popt, pcov = optimization.curve_fit(linear_func, x, y)
    perr = np.sqrt(np.diag(pcov))
    print(f"a: {popt[0]}, b: {popt[1]}", flush=True)
    print(f"std err of params: {perr}", flush=True)

    # plot size of reshare cascades vs exposure cascades
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.5, 15000)

    # plot fitted line, shift the line a bit so it's easier to see
    x_ = short["spread_via_agents"]
    ax.plot(x_, exp_func(x_, *popt) * fitline_shift, c=fitline_color, linewidth=1)
    if annotate is True:
        ax.text(
            0.6,
            0.7,
            f"$\\nu$= {popt[0]:.2f} $\pm$ {perr[0]:.2f}",
            transform=ax.transAxes,
            fontsize=12,
        )

    ## plot diagonal line
    ax.plot([1, 10000], [1, 10000], color="black", linestyle="dashed", linewidth=1)

    # formatting
    if x_label is True:
        ax.set_xlabel("Reshare cascade size")
    if y_label is True:
        ax.set_ylabel("Avg. exposure cascade size")
    ax.legend(fontsize=13)

    return


def data_reshare_vs_exposure(data, message_type="all", data_type="list"):
    # return data to plot
    # data: df or list of messages (dicts) having at least 3 attributes: id_str, is_by_bot, seen_by_agents, spread_via_agents
    # Note: message identifier is now "id_str" instead of "id"

    if data_type != "df":
        messages = pd.DataFrame.from_records(data)
    else:
        messages = data
    try:
        if message_type == "bot":
            messages = messages[messages.is_by_bot == 1]
        if message_type == "hum":
            messages = messages[messages.is_by_bot == 0]

        exposure = messages.explode("seen_by_agents")
        exposure = exposure.drop_duplicates(subset=["id_str", "seen_by_agents"])
        exp_size = exposure.groupby(["id_str"]).seen_by_agents.count()

        reshare = messages.explode("spread_via_agents")
        reshare = reshare.drop_duplicates(subset=["id_str", "spread_via_agents"])
        reshare_size = reshare.groupby(["id_str"]).spread_via_agents.count()

        sizes = pd.merge(exp_size, reshare_size, on="id_str").reset_index()
        # take the average size of exposure cascade for same-size diffusion cascade
        avg = sizes.groupby(["spread_via_agents"]).seen_by_agents.mean().reset_index()
    except Exception as e:
        print(
            "Error reading data. File might be corrupted or missing an attribute. Required: [id_str, is_by_bot, seen_by_agents, spread_via_agents]"
        )
        print(e, flush=True)
    return avg


if __name__ == "__main__":
    # Prep data & plot

    file_dir = sys.argv[1]
    file_pattern = sys.argv[2]
    plot_dir = sys.argv[3]

    ## PREP DATA ##
    print("-- Start plotting cascade size scaling between reshares and exposure")

    dfout_path = os.path.join(file_dir, f"{file_pattern}.parquet")
    if not os.path.exists(dfout_path):
        FILE_PATHS = glob.glob(os.path.join(file_dir, f"{file_pattern}*.json.gz"))
        if len(FILE_PATHS) == 0:
            print("No file match this name pattern. Exiting..")
            sys.exit()

        print(
            "-- Finish inferring fnames.. Combining cascade data from multiple runs.."
        )
        print(FILE_PATHS)
        all_data = []
        for idx, fpath in enumerate(FILE_PATHS):
            print(f"Reading {idx}/{len(FILE_PATHS)}", flush=True)
            try:
                path = os.path.dirname(fpath)
                fname = os.path.basename(fpath).replace(".json.gz", "")
                data = read_ijson_compressed(fpath)
                # reindex message ids (make sure message ids are unique, since original message ids are int)
                for message_info in data:
                    message_info["id_str"] = str(message_info["id"]) + str(idx)
                all_data += data

            except Exception as e:
                print(f"Error reading file {fpath}", flush=True)
                print(e, flush=True)
                continue

        cleaned = []
        # Make sure attribute is of correct type (since ijson changes float to Decimal)
        attributes = ["id_str", "spread_via_agents", "seen_by_agents"]
        for message_info in all_data:
            message = {"is_by_bot": float(message_info["is_by_bot"])}
            for attrib in attributes:
                message[attrib] = message_info[attrib]
            cleaned += [message]
        del all_data

        df = pd.DataFrame.from_records(cleaned)
        print("-- Saving intermediate df..", flush=True)

        df.to_parquet(dfout_path, engine="pyarrow")
        print(
            f"Finish saving all files matching {file_pattern} to .parquet!", flush=True,
        )
        cleaned = df

    else:
        cleaned = pd.read_parquet(dfout_path)
        message_data_type = "df"

    ## PLOT ##
    fig_path = os.path.join(plot_dir, "scaling")
    print(f"--Start plotting..")

    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    fig, axs = plt.subplots(2, 1, sharex=True, sharey=True, figsize=(6, 12))
    min_reshare_size = 10
    max_reshare_size = 1000
    try:
        print("1/2. Bot message panel:", flush=True)
        botdata = data_reshare_vs_exposure(cleaned, message_type="bot", data_type="df")
        plot_cascade_scaling_with_fitted_line(
            botdata,
            axs[0],
            min_x=min_reshare_size,
            max_x=max_reshare_size,
            annotate=False,
            label="low-q",
            x_label=False,
            y_label=True,
            point_color=bot_color,
            alpha=1,
        )

        print("2/2. Authentic agent message panel: ", flush=True)
        humdata = data_reshare_vs_exposure(cleaned, message_type="hum", data_type="df")
        plot_cascade_scaling_with_fitted_line(
            humdata,
            axs[1],
            min_x=min_reshare_size,
            max_x=max_reshare_size,
            label="high-q",
            x_label=True,
            y_label=True,
            annotate=False,
            point_color=human_color,
            alpha=1,
        )

        plt.subplots_adjust(
            left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.1
        )
        if fig_path is not None:
            plt.savefig(f"{fig_path}.pdf")
            plt.savefig(f"{fig_path}.png")
        else:
            plt.show()
    except Exception as e:
        print("Error while plotting", flush=True)
        print(e)

    print(f"--Finished plotting! Saved to {fig_path}.pdf")

