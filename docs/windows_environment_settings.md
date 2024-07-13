Windows can quickly set up environments through WSL.

**Setup WSL** 

```shell
# https://learn.microsoft.com/en-us/windows/wsl/install
```

> All the following operations will be conducted in WSL.

**Install miniconda** 

```shell
wget https://repo.anaconda.com/miniconda/Miniconda3-py312_24.5.0-0-Linux-x86_64.sh
bash Miniconda3-py312_24.5.0-0-Linux-x86_64.sh
```

**Setup Python Environment via miniconda**

```shell
conda create -n halatrans python=3.11
conda activate halatrans
```

**Install asdf and reopen Terminal**

```shell
# https://asdf-vm.com/guide/getting-started.html
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
# Add the following to ~/.bashrc
# . "$HOME/.asdf/asdf.sh"
# . "$HOME/.asdf/completions/asdf.bash"
```

**Install poetry via asdf**

```shell
asdf plugin add poetry
asdf install poetry
```

> TODO: The currently dependent PyAudio does not have a precompiled WHL version available for installation in WSL, so a development environment is required for compilation. We will address this issue by reviewing and resolving the dependencies later. 
> https://files.portaudio.com/docs/v19-doxydocs/compile_linux.html

**Setup PortAudio Build Environemnt**

```shell
# install build toolchain
sudo apt-get install make build-essential
# install dependent libs
sudo apt-get install libasound2-dev
# get the code
git clone https://github.com/PortAudio/portaudio.git --branch v19.7.0
# configure and build
./configure && make
sudo make install
```

**Environment is ready, install all the deps via poetry**

```shell
poetry install
```

**Run**

```shell
# Since libasound2.so.2 is installed in /usr/local/lib, it may not be found at runtime. You need to set the library search path.
export LD_LIBRARY_PATH=/usr/local/lib 
# Need to set OPENAI_API_KEY
export OPENAI_API_KEY="xxx"
make runDev
```

