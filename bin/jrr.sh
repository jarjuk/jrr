#!/bin/bash
# Järviradioradion management script

# ------------------------------------------------------------------
# Default confits
VERSION=0.2
DEBUG=1                     # log verbosity
# JRR_LOG=                  # default daemon output not save to log file
JRR_DEBUG=""                # default WARNING, more -v's --> more output
# JRR_DEBUG="-v -v"  
ALL_LINES=""                # default - only one console line per time tick
# ALL_LINES="--all-lines"

# Firmware update configs
LOCAL_REPO=$HOME/jrr
PENDING_LINK=$LOCAL_REPO/src.next
CURRENT_LINK=$LOCAL_REPO/src
PREV_LINK=$LOCAL_REPO/src.prev


# ------------------------------------------------------------------
# Subrus
usage() {
    echo 
    echo usage: $(basename $0)
    echo $0 - $VERSION
    echo ""
    echo "Järviradioradio controller script"
    echo ""
    echo "Usage:"
    echo "$0 [options]  -- <commands>"
    echo "options:"
    echo "--sh_trace"
    echo "--version             : print out version number && exit 0"
    echo "--debug|-v            : increment DEBUG='$DEBUG' level (in script $0)"
    echo "--jrr-debug           : increment JRR_DEBUG='$JRR_DEBUG' level "
    echo "--all-lines           : output all lines in console mode "
# echo "--jrr-log FILE        : daemon output JRR_LOG='$JRR_LOG'"
    echo "-?|--help             : usage"
    echo ""
    echo "commands:"
    echo "daemon                : Run jrr -application (as systemd service)"
    echo "daemon-kill           : Kill jrr -application (from systemd service \$MAINPID)"
    echo "kill                  : Stop jrr -service and finish also console output"
    echo "daemon-stop           : SIGTERM to jrr -application (from systemd service \$MAINPID)"
    echo "stop                  : Stop jrr -service"
    echo "start                 : start jrr -service"    
    echo "status                : Show process ids for jrr.py and ffmpeg streamer process"
    echo "kill-ffmpeg           : Kill ffmpeg streamer process"
    echo "activate-pending      : Activate  PENDING_LINK if it valid"    
    echo ""
    echo "Examples:"
    echo ""
    echo ""

}

log() {
    local LEVEL=$1
    local MSG=$2
    if [ $DEBUG -ge $LEVEL ]; then
       	# echo $(date $TS_FORMAT): $0'|'$MSG 1>&2
       	echo "$MSG" 1>&2
    fi
}

error_msg() {
    local MSG=$1
    logger "$MSG"
    log 1 "$MSG"
}

kill_streamer() {
    killall ffmpeg
}


shutdown() {
    log 1 "Shutdown called - send SIGTERM to CHILD_PID=$CHILD_PID"
    kill -SIGTERM $CHILD_PID
    exit 0
}

do_stop() {
    if [ ! -z "$MAINPID" ]; then
        log 1 "do_stop: send SIGTERM to MAINPID=$MAINPID"                
        kill -SIGTERM $MAINPID
    else
        JRR_PID=$(pgrep -f jrr.py)
        if [ ! -z "$JRR_PID" ]; then
            log 1 "do_stop - send SIGTERM to JRR_PID=$JRR_PID"
            kill -SIGTERM $JRR_PID
        else
            log 1 "do_stop: no jrr.py process found"
        fi
    fi
}

do_kill() {
    JRR_PID=$(pgrep -f jrr.py)
    if [ ! -z "$JRR_PID" ]; then
        log 1 "do_kill: $JRR_ID still running - SIGKILL (-9)"
        kill -9 $JRR_PID
    else
        log 1 "do_kill: no jrr.py process found"
    fi
}

activate_pendig() {

    log 2 "activate_pendig: check $PENDING_LINK"
    if [ -L $PENDING_LINK ]; then
        log 1 "activate_pendig: $PENDING_LINK exists "
        log 2 "activate_pending: pre $(ls -ltr $CURRENT_LINK $PENDING_LINK)"
        rm -f $PREV_LINK
        mv $CURRENT_LINK $PREV_LINK
        mv $PENDING_LINK $CURRENT_LINK
        log 2 "activate_pending: post $(ls -ltr $CURRENT_LINK $PENDING_LINK $PREV_LINK)"
    fi 
}

# ------------------------------------------------------------------
# Starting


MSG="'$(whoami)' runs '$0 $*' on '$(hostname):$(pwd)'"
log 1 "$MSG"
# logger "$MSG"

# ------------------------------------------------------------------
# Options section
while :
do
    if [ -z "$1" ]; then
	    break
    fi

    log 3 "Check option for '$1'"

    case "$1" in
        
	--sh_trace|--sh-trace)
	    set -x
	    shift
	    ;;
	
	--version)
        echo $0 VERSION=$VERSION
        exit 2
	    ;;
	
	--debug|-v)
	    shift
	    DEBUG=`expr $DEBUG + 1`
	    log 1 "DEBUG=$DEBUG"
	    ;;

	--jrr_debug|--jrr-debug)
	    shift
	    JRR_DEBUG="$JRR_DEBUG -v"
	    log 1 "setting JRR_DEBUG=$JRR_DEBUG"
	    ;;

	--all-lines|--all_lines)
	    shift
	    ALL_LINES="--all-lines"
	    log 1 "setting ALL_LINES=$ALL_LINES"
	    ;;

	# --jrr_log|--jrr-log)
	#     shift
	#     JRR_LOG=$1
	#     shift
	#     log 1 "setting JRR_LOG=$JRR_LOG"
	#     ;;


	-\?|--help)
	    usage
	    exit 2
	    ;;

	
	 '--')
	    break
	    ;;

	*)
	    break
	    ;;
    esac
done

# ------------------------------------------------------------------
# Fix parameters for command use


# ------------------------------------------------------------------
# Command section
# Output usage - if no commands given
if [  $# -lt 1 ]; then
    usage
    exit 2
fi

while :
do

    log 3 "cmdline parameters left $#"
    if [  $# -lt 1 ]; then
	    break
    fi

    CMD=$1
    shift

    log 2 "CMD=$1"
    case "$CMD" in


        version) 
	        echo "$0 - $VERSION"
	        ;;
        
        kill-ffpmeg|kill-streamer) 
	        kill_streamer
	        ;;
        
        status)
            # (set -x; ps -ef | grep -e jrr -e ffmpeg -e python )

            P=$(ps -ef | grep 'jrr.sh daemon'  | grep -v grep)
            ISTAT2=$?
            echo "jrr.sh: status=$ISTAT2/$P"            
            
            P=$(ps -ef | grep jrr.py  | grep -v grep)
            ISTAT3=$?
            echo "jrr.py: status=$ISTAT3/$P"

	        P=$(ps -ef | grep ffmpeg | grep -v grep)
            ISTAT1=$?
            echo "ffmpeg: status=$ISTAT1/$P"
            
            if [ $ISTAT3 != 0  ]; then
                exit $ISTAT3
            fi
            if [ $ISTAT2 != 0  ]; then
                exit $ISTAT2
            fi
            if [ $ISTAT1 != 0 ]; then
                exit $ISTAT1
            fi
	        ;;
        
        daemon)
	        kill_streamer
            do_kill
            log 1 "User '$(whoami)' launching järviradioradio daemon"
            CMD=".venv/bin/python ./jrr.py $JRR_DEBUG radio $ALL_LINES"
            log 1 "User '$(whoami)' runs CMD='$CMD' in directory $(pwd) with PATH='$PATH'"
            trap shutdown SIGTERM
            $CMD 2>&1 &
            CHILD_PID=$!
            log 1 "Wait for CHILD_PID=$CHILD_PID"
            wait $CHILD_PID
            log 1 "järviradioradio '$CMD' - exits STATUS='$ISTAT'"
            # hopefully systemd is happy with this
            exit 0
	        ;;

        stop)
            sudo systemctl stop jrr
            # Continue with daemon stop
            kill_streamer
            do_stop
            ;;
        
        start)
            sudo systemctl start jrr
            ;;
        
        daemon-stop)
            kill_streamer
            do_stop
            ;;
        
        
        kill)
            sudo systemctl stop jrr
            # Continue with daemon stop
            kill_streamer
            do_stop
            sleep 1
            do_kill
            ;;
            
        daemon-kill)
            kill_streamer
            do_stop
            sleep 1
            do_kill
            ;;
        
        activate-pending)
            activate_pendig
            ;;

        true)
            ;;

	    
	    *)
	        usage
	        echo  "Unknown action: $CMD"
	        exit 3
	        ;;

    esac

done

exit 0
