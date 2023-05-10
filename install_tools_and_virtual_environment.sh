#!/bin/bash

CPU_ONLY=false
UPDATE_UTILITY_BINARIES=false

update_utility_binaries() {
	date="2023/05/06"

	kicadParser_branch=parsing_and_plotting
	SA_PCB_branch=crtYrd_bbox
	pcbRouter_branch=updating_dependencies

	#GIT=https://www.github.com/
	#GIT_USER=lukevassallo
	GIT=git@gitlab.lukevassallo.com:
	GIT_USER=luke

	CLEAN_ONLY=false
	CLEAN_BEFORE_BUILD=false
	RUN_PLACER_TESTS=false
	RUN_ROUTER_TESTS=false

	printf "\n"
	printf "  **** Luke Vassallo M.Sc - 02_update_utility_binaries.sh\n"
	printf "   *** Program to to update kicad parsing utility and place and route tols.\n"
	printf "    ** Last modification time %s\n" $date
	printf "\n"
	sleep 1

	print_help() {
		echo "--clean_only              removes the git repositories and exits."
		echo "--clean_before_build      removes the git repositories then clones and builds binaries."
		echo "--run_placer_tests	    runs automated tests to verify placer."
		echo "--run_router_tests        runs automated tests to verify router."
		echo "--help                    print this help and exit."
	}

    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean_only)
                CLEAN_ONLY=true
                shift   # past argument
                ;;
        --clean_before_build)
            CLEAN_BEFORE_BUILD=true
            shift
            ;;
        --run_placer_tests)
            RUN_PLACER_TESTS=true
            shift
            ;;
        --run_router_tests)
            RUN_ROUTER_TESTS=true
            shift
            ;;
            --help)
                print_help
                exit 0
                ;;
            -*|--*)
                echo "Unknown option $1"
                exit 1
                ;;
            *)
                POSITIONAL_ARGS+=($1)
                shift
                ;;
        esac
    done

    if [ -d "bin" ]; then
        cd bin
    else
        mkdir bin && cd bin
    fi

    if [ "$CLEAN_ONLY" = true ] || [ "$CLEAN_BEFORE_BUILD" = true ]; then
        echo -n "Attempting to clean the KicadParser repository ... "
        if [ ! -d "KicadParser" ]; then
            echo "Not found, therefore nothing to clean.";
        else
            echo "Found, deleting."
            rm -fr KicadParser
        fi

        echo -n "Attempting to clean the SA_PCB repository ... "
        if [ ! -d "SA_PCB" ]; then
            echo "Not found, therefore nothing to clean.";
        else
            echo "Found, deleting."
            rm -fr SA_PCB
        fi

        echo -n "Attempting to clean the pcbRouter repository ... "
        if [ ! -d "pcbRouter" ]; then
            echo "Not found, therefore nothing to clean.";
        else
            echo "Found, deleting."
            rm -fr pcbRouter
        fi

        if [ "$CLEAN_ONLY" = true ]; then
            exit 0
        fi
    fi

    echo -n "Building kicad pcb parsing utility. Checking for repository ... "
    ORIGIN=${GIT}${GIT_USER}/kicadParser
    if [ -d "KicadParser" ]; then
        echo "Found, cleaning"
        cd KicadParser
        make clean
            git pull $ORIGIN ${kicadParser_branch}
        #git submodule update --remote --recursive
    else
        echo "Not found, cloning."
        git clone --branch ${kicadParser_branch} ${ORIGIN} --recurse-submodules KicadParser
        cd KicadParser
    fi
    make -j$(nproc)
    cp -v build/kicadParser_test ../kicadParser
    cd ..

    echo -n "Building simulated annealing pcb placer. Checking for repository ... "
    ORIGIN=${GIT}${GIT_USER}/SA_PCB
    if [ -d "SA_PCB" ]; then
        echo "Found, cleaning"
        cd SA_PCB
        make clean
        git pull ${ORIGIN} ${SA_PCB_branch}
        #git submodule update --remote --recursive
    else
        echo "Not found, cloning."
        git clone --branch ${SA_PCB_branch} ${ORIGIN} --recurse-submodules
        cd SA_PCB
    fi
    make -j$(nproc)
    if [ "$RUN_PLACER_TESTS" = true ]; then
        make test_place_excl_power
        make test_place_incl_power
    fi

    #cp -v ./build/sa_placer_test ../bin/sa_placer
    cp -v ./build/sa_placer_test ../sa
    cd ..

    echo -n "Building pcbRouter binary. Checking for repository ... "
    ORIGIN=${GIT}${GIT_USER}/pcbRouter
    if [ -d "pcbRouter" ]; then
        echo "Found, cleaning"
        cd pcbRouter
        make clean
            git pull ${ORIGIN} ${pcbRouter_branch}
        #git submodule update --remote --recursive
    else
        echo "Not found, cloning."
        git clone --branch ${pcbRouter_branch} ${ORIGIN} --recurse-submodules
        cd pcbRouter
    fi
    make -j$(nproc)
    if [ "$RUN_ROUTER_TESTS" = true ]; then
        make test_route_excl_power
        make test_route_incl_power
    fi

    cp -v build/pcbRouter_test ../pcb_router
    cd ..

    cd ..
}


while [[ $# -gt 0 ]]; do
    case $1 in
        --cpu_only)
            CPU_ONLY=true
            shift
            ;;
        --update_utility_binaries)
            UPDATE_UTILITY_BINARIES=true
            shift
            ;;
    esac
done

if [ "$UPDATE_UTILITY_BINARIES" == true ]; then
	update_utility_binaries --clean_before_build --run_placer_tests --run_router_tests
fi

if [ ! -d "bin" ]; then
	echo "Installing kicad PCB parsing utility and PCB place and route tools."
	update_utility_binaries --run_placer_tests --run_router_tests
fi

#if [ -d "venv" ]; then
#	echo "Virtual environment already exists ... Program terminating."
#fi

if [ ! -d "venv" ]; then
	echo "Creating virtual environment ..."
	python3.8 -m venv venv
else
	echo "Virtual environment already exists ..."
fi
source venv/bin/activate

which python
python -c "import sys; print(sys.path)"
python -V

python -m pip install --upgrade pip
python -m pip install --upgrade setuptools==65.5.0	# See: https://github.com/openai/gym/issues/3176

# Refer to pytorch and update according to your cuda version
if [ "$CPU_ONLY" == true ]; then
	python -m pip install torch==1.13.1+cpu torchvision==0.14.1+cpu torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cpu
else
	python -m pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu117
fi

python -m pip install matplotlib numpy==1.23.3 opencv-python gym pyglet optuna tensorboard reportlab py-cpuinfo psutil pandas seaborn pynvml plotly moviepy

python -m pip install -U kaleido

python -m pip install ./lib/pcb_netlist_graph-0.0.1-py3-none-any.whl
python -m pip install ./lib/pcb_file_io-0.0.1-py3-none-any.whl

python tests/00_verify_machine_setup/test_setup.py
