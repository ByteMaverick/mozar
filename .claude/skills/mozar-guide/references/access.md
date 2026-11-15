# Getting onto the cluster

The project runs on the SJSU College of Engineering HPC (`coe-hpc2.sjsu.edu`), which uses Slurm.
Walk the person through these steps in order and check each one before moving on.

## 1. Connect to the SJSU VPN

Off campus, the cluster is reachable only through the SJSU VPN. Use the VPN client SJSU IT provides and sign
in with the SJSU account. On campus wifi this step may not be needed. If `ssh` later hangs or says
"could not resolve hostname", the VPN is the first thing to check.

## 2. First login with a password

```bash
ssh <SJSU ID>@coe-hpc2.sjsu.edu
```

The user name is the 9-digit SJSU ID. The password is the one given for the CoE HPC (usually the SJSU password).
Once in, run `id`. The output must include the group **`nsf-jg`** (Prof. JG's group). If it does not, the person
cannot open the shared project folder; they need to ask Prof. JG or the HPC admins to add them.

## 3. Set up a key so `ssh hpc` works without typing a password

On the laptop (macOS or Linux; on Windows use the same commands in PowerShell with OpenSSH):

```bash
ssh-keygen -t ed25519 -C "coe-hpc"            # press Enter to accept the default file; a passphrase is optional
ssh-copy-id <SJSU ID>@coe-hpc2.sjsu.edu        # asks for the HPC password once
```

On Windows without `ssh-copy-id`, append the contents of `~/.ssh/id_ed25519.pub` to `~/.ssh/authorized_keys`
on the cluster by hand.

Then add this to `~/.ssh/config` on the laptop:

```
Host hpc
  HostName coe-hpc2.sjsu.edu
  User <SJSU ID>
  ServerAliveInterval 30
  ServerAliveCountMax 4
```

Test with `ssh hpc`. It should log in with no password. Mohammed's setup also adds `BatchMode yes` and
`ConnectTimeout 20`, which make scripted commands fail fast instead of waiting at a password prompt; add those
only after the key works.

## 4. Open the shared project folder

```bash
ssh hpc
cd /data/nsf-jg/mozar
ls
```

The folder holds the code (a git checkout), the shared Python environment in `.venv`, and `data/` with a copy
of the finished data. Everything in it belongs to the group `nsf-jg`, so any member can read and write.
Keep it that way: before creating files there, run `umask 002` (or add it to `~/.bashrc`) so new files stay
group-writable.

Use the shared environment rather than making a new one:

```bash
/data/nsf-jg/mozar/.venv/bin/python -c "import sklearn, xgboost; print('ok')"
```

**Where the live data is.** The collection that is running now writes to Mohammed's home folder
(`~/mozar` under his account), which other users cannot open. When that run ends, its data moves to
`/data/nsf-jg/mozar/data`. Until then, the shared `data/` folder holds a copy of the finished one-month data
(dataset table, labels, pairs, histories, features), which is enough for all modeling work.

## 5. How the cluster works

| Thing | What to know |
|---|---|
| Login node | The machine `ssh hpc` lands on. It has internet. Use it for downloads, editing, git, and light work only. |
| Compute nodes | Run jobs through Slurm. **They have no internet.** Anything a job needs (code, data, model weights) must be downloaded on the login node first. |
| GPUs | H100 (about 94 GB) in partition `nsfq` (group partition, 1-day limit) and `gpuqs`/`gpuqm`/`gpuql`. A100 40 GB nodes in `gpuqs` are often free. |
| CPUs | Partitions `defq` (6 hours), `cpuqs` (5 days), `cpuqm`, `cpuql`. |
| Budget | Keep to one GPU and 2 to 3 CPUs per job unless agreed otherwise; the group shares these machines. |
| Disk | Home folders are on a shared disk that is about 95% full. Put big files in `/data/nsf-jg/mozar`, not in home. `/fs/sfs/scratch` is not writable for this group. |

Common commands:

```bash
squeue -u $USER                                     # your jobs
sinfo -p nsfq,gpuqs                                 # what is free
sbatch jobs/judge.sbatch                            # submit a batch job (see jobs/ for examples)
srun -p cpuqs --cpus-per-task=2 --mem=8G --time=2:00:00 --pty bash     # an interactive CPU shell
scancel <job id>                                    # stop a job
```

## 6. Where to run the notebook

The modeling data is small (one row per post, a few hundred rows), so the simplest place is the laptop:

```bash
git clone git@github.com:ByteMaverick/mozar.git && cd mozar
python -m venv .venv && .venv/bin/pip install -r requirements.txt
scp -r hpc:/data/nsf-jg/mozar/data/{features.csv,index.csv,labels} data/   # small files only
.venv/bin/jupyter lab modeling.ipynb
```

To run it on the cluster instead, start Jupyter on a compute node and tunnel to it:

```bash
srun -p cpuqs --cpus-per-task=2 --mem=8G --time=3:00:00 --pty bash
cd /data/nsf-jg/mozar && .venv/bin/jupyter lab --no-browser --ip=$(hostname) --port=8899
# on the laptop, in a second terminal (use the node name Jupyter printed):
ssh -N -L 8899:<node>:8899 hpc            # then open the link Jupyter printed, with localhost in place of the node
```

Do not copy images to the laptop; there are hundreds of thousands of them.

## 7. Keeping the shared copy and the laptop in step

The shared folder is a git checkout. To update it after pulling on GitHub, either set up git credentials on
the cluster (a GitHub deploy key or a personal access token) and run `git pull` there, or copy from the laptop:

```bash
rsync -a --exclude data/ --exclude models/ --exclude .venv/ --exclude logs/ ./ hpc:/data/nsf-jg/mozar/
```
