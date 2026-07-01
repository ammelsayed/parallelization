import os
import subprocess
from ROOT import gInterpreter, gSystem
from ROOT import __version__ as rootVersion
from pathlib import Path
DELPHES_PATH = os.environ.get("DELPHES_HOME", "/home/ammelsayed/softwares/MG5_aMC_v3_7_1/Delphes")
gInterpreter.AddIncludePath(DELPHES_PATH)
gInterpreter.AddIncludePath(f"{DELPHES_PATH}/classes")
gInterpreter.AddIncludePath(f"{DELPHES_PATH}/external")
gSystem.Load("libDelphes")
gInterpreter.Declare('#include "classes/DelphesClasses.h"')
gInterpreter.Declare('#include "classes/SortableObject.h"')
gInterpreter.Declare('#include "external/ExRootAnalysis/ExRootTreeReader.h"')
print("Using ROOT version:", rootVersion)
print("Using Delphes libraries found at:", DELPHES_PATH)

# Only avaliable for python 3.12+
def find_files_new(directory, ends_with=".root", max_depth=2):
    directory = Path(directory).resolve()
    found = set()
    for root, dirs, files in directory.walk():
        depth = len(root.relative_to(directory).parts)
        if depth >= max_depth:
            dirs[:] = []  # don't descend further
        for f in files:
            if f.endswith(ends_with):
                found.add(root / f)
    return sorted(found)

# Works for all python versions
def find_files(directory, ends_with=".root", max_depth=2):
    directory = os.path.abspath(directory)
    found = set()
    for root, dirs, files in os.walk(directory):
        depth = root[len(directory):].count(os.sep)
        if depth >= max_depth:
            dirs[:] = []  # don't descend further
        for f in files:
            if f.endswith(ends_with):
                found.add(os.path.join(root, f))  
    return sorted(found)

def check_hepmc(path):
    p = Path(path)
    return p.is_file() and p.stat().st_size > 0

def get_custom_name(path):
    p = Path(path)
    return f"{p.parents[2].name}_{p.parent.name}"

def run_delphes(hepmc_path, delphes_card, output_dir, exe, overwrite=True, auto_remove_hepmc = True):
    out = Path(output_dir)
    name = get_custom_name(hepmc_path)
    root_out = out / f"{name}.root"   
    log_out = out / f"{name}.log"
    if root_out.exists() and not overwrite:
        return 0

    cmd = [exe, str(delphes_card), str(root_out), str(hepmc_path)]
    with open(log_out, "w") as log:

        result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    
        # Delete HEPMC file only if Delphes succeeded
        if result.returncode == 0 and auto_remove_hepmc:
            try:
                os.remove(hepmc_path)
            except OSError as e:
                log.write(f"Warning: Could not delete {hepmc_path}: {e}\n")

        return result.returncode


if __name__ == "__main__":

    exe = os.path.join(DELPHES_PATH, "DelphesHepMC2")
    card = "/data/ammelsayed/stuff/Cards/delphes_card_ATLAS_FatJets_v1.tcl"
    outdir = "./root_files"
    nb_cores_delphes = 15

    from parallelization import parallel_runs

    os.makedirs(outdir,exist_ok=True)
    files = [f for f in find_files("/data/ammelsayed/stuff/tW012j_MLM/Events/run_01_02", ends_with=".hepmc", max_depth=3) if check_hepmc(f)]
    args_list = [(f,card,outdir,exe) for f in files]
    parallel_runs(run_delphes, args_list, max_workers=nb_cores_delphes, info="Delphes jobs")