# Tropical Storm Discoverer (TROSDIS)

This software contains a deep learning algorithm to detect and classify tropical storms.


## Install

To clone the web labeler [ANUMOGET](https://github.com/olmozavala/AwesomeGeoTagger) use:

`
git submodule update --init --recursive
`
## PyCharm
In order to run/debug each module separated you need
to set each of the subfolders root as a `source folder`.
Just right-click on the folder then `Mark Directory as` and 
select `Sources Root`.

## Anaconda
Create an environment with the proper dependencies:

```
conda env create -f yourfile.yml
activate trostdis
```

## Run

Each subproject should have an `ExampleMainConfig.py`
file in the `config` folder. Copy that file to `MainConfig.py`
and update the parameters. Then simpy run each of the
`main.py` or corresponding file.
