# gnuradio-3.8

Docker build of gnuradio-3.8, from source, on Ubuntu 18.04.

Build locally using the build instructions, if you want.

Or, this image is also pushed to [Theseus Cores Docker Hub](https://hub.docker.com/r/theseuscores/gnuradio),
so you can jump straight to the "running" section without doing a local build.

## Install dependencies:
#### Running IoT-Scan
To install Docker see: https://docs.docker.com/engine/install/ubuntu/
#### Data analysis
To generate some of the graphs below you may have to install matplotlib and pandas within docker container (not baked in Dockerfile yet):

sudo apt install python3-matplotlib # currently installs matplotlib.__version__ '2.1.1'

pip3 install pandas

## Build instructions

`docker build -t <docker-image-name> .`

There's also a number of override-able parameters in the Dockerfile that
can be used to specify Gnuradio and UHD configuration.

## Running

Run the docker image, with volume mounts for running gnuradio-companion
and a data directory:

```
./run-over-network <docker-image-name>
```

For an additional shell run:

```
docker exec -it <docker-image-name> bash
```


