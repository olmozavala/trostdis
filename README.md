# Tropical Storm Discoverer (TROSDIS)

This software contains a deep learning algorithm to detect and classify tropical storms.


## Install

To clone the web labeler [ANUMOGET](https://github.com/olmozavala/AwesomeGeoTagger) use:

`
git submodule update --init --recursive
`

To download the test data you need to install **Git LFS**. 
In Ubuntu it is done with:

```
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
sudo apt-get install git-lfs
```
Then download the test folder with `git lfs fetch`.

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

### GOES

#### main.py
Reproyecta un y agrupa las variables del satelite GOES
en un solo netcdf.

#### Selenium_class.py
Llena el formulario para hacer la solicitud del GOES.
