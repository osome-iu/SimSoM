import sys
import datetime

try:
    from simsom.model import SimSom
    from simsom.graphutils import *
    from simsom.utils import *
except ModuleNotFoundError:
    print(
        "Unable to import simsom package. \n"
        "Change to root directory of this project and run `pip install -e ./libs/`"
    )
# ABS_PATH = "experiments/10092023_comparev2"
ABS_PATH = "/N/project/simsom/simsom_v3/10092023_compare_v2"
RESULT_DIR = os.path.join(ABS_PATH, "results/v3")
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

DATA_PATH = os.path.join(ABS_PATH, "data")
network_fpath = os.path.join(DATA_PATH, "infosys_network_10k.gml")


def run_sim(simulation_specs, no_runs=1):
    start = datetime.datetime.now()
    # Run the simulation
    no_runs = no_runs
    # Create a list to store results across runs
    quality = []

    # NOTE: simulation_specs has at least one key "alpha"
    alpha = simulation_specs["alpha"]

    reshare_fpath = os.path.join(RESULT_DIR, f"reshare__alpha{alpha}.csv")
    exposure_fpath = os.path.join(RESULT_DIR, f"exposure__alpha{alpha}.csv")
    message_info_fpath = os.path.join(RESULT_DIR, f"message_info__alpha{alpha}.json.gz")

    logger.info("*** Start simulation ***")
    for run in range(no_runs):
        logger.info(f"-- Run {run+1}/{no_runs}: \n Create SimSom instance..")
        # Create a SimSom instance
        follower_sys = SimSom(network_fpath, **simulation_specs)

        if no_runs == 0:
            logger.info(follower_sys)
        if run % 10 == 0:
            logger.info(f" - {run} ..")

        # Run simulation
        if simulation_specs["output_cascades"] is False:
            results = follower_sys.simulation()
        else:
            results = follower_sys.simulation(
                reshare_fpath=reshare_fpath.replace(".csv", f"_{run}.csv"),
                exposure_fpath=exposure_fpath.replace(".csv", f"_{run}.csv"),
            )
        logger.info(
            f" - Simulation finished. Quality: {np.round(results['quality'],3)}"
        )

        # Update the quality list
        quality += [results["quality"]]

        # Save verbose results (with simulation specs)
        if simulation_specs["save_message_info"] is True:
            specs = deepcopy(simulation_specs)
            specs.update(results)
            fpath = message_info_fpath.replace(".json.gz", f"_{run}.json.gz")
            fout = gzip.open(fpath, "w")
            write_json_compressed(fout, specs)

    # Save short results (with simulation specs)
    short_results = deepcopy(simulation_specs)
    short_results.update({"quality": quality})
    json.dump(
        short_results,
        open(os.path.join(RESULT_DIR, f"results__alpha{alpha}.json"), "w"),
    )
    logger.info("*** Time taken (s): ", datetime.datetime.now() - start)
    logger.info(
        f"*** Average quality across {no_runs} runs: {np.round(np.mean(quality),3)} ***"
    )


if __name__ == "__main__":
    try:
        no_runs = int(sys.argv[1])
        alpha = int(sys.argv[2])
    except Exception as e:
        print(e)
        print("Cannot convert no_runs and alpha to ints")

    log_dir = os.path.join(ABS_PATH, "logs")
    logger = get_file_logger(
        log_dir=log_dir,
        log_fpath=os.path.join(log_dir, f"run_v3__alpha{alpha}.log"),
        also_print=True,
    )

    simulation_specs = {
        "verbose": True,
        "tracktimestep": True,
        "save_message_info": False,
        "output_cascades": False,
        "epsilon": 0.0001,
        "n_threads": 12,
        "mu": 0.5,
        "phi": 1,
    }

    simulation_specs["alpha"] = alpha

    run_sim(simulation_specs, no_runs=no_runs)
