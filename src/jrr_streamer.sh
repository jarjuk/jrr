#!/bin/bash

# ------------------------------------------------------------------
# traps

# set -eou pipefail
set -eE

trap 'err_report $? $LINENO' ERR 
# trap 'err_report $? $LINENO' EXIT
trap terminator TERM

err_report() {
    if [ $1 != 0 ]; then
        echo "$0, exiting error $1 from line $2"
        log 1 "$0, exiting error $1 from line $2"
        exit $1
    else 
        echo "$0, exiting normally from line $2"
    fi
    exit $1
}

terminator() {
    pkill -TERM -P $!
    log 1 "Terminated"
    exit 0
}


# ------------------------------------------------------------------
# Default configs

VERSION=0.1
# 1=warning
DEBUG=1
TS_FORMAT="+%Y%m%d-%T"

# output device, one from list-devices, default  none
AUDIO_OUT="" 
SOUND_DIR=$HOME/tmp

DURATION=60
LEFT_FREQ="1000"
RIGHT_FREQ="440"
VOLUME=1.0
# override
FILE=""

# filter_complex string to add for stero/mono
MONO_OR_STEREO_CMD=""

# Left and Right channel gains
RGAIN=1.0
LGAIN=1.0
GAIN=4.0

# Firmware update configs
LOCAL_REPO=$HOME/jrr/
PENDING_LINK=$LOCAL_REPO/src.next


# ------------------------------------------------------------------
# Subrus

log() {
    local LEVEL=$1
    local MSG=$2
    if [ $DEBUG -ge $LEVEL ]; then
        	echo $(date $TS_FORMAT): $0'|'$MSG 1>&2
    fi
}

error_msg() {
    local MSG=$1
    logger "$MSG"
    log 1 "$MSG"
}

usage() {
    echo 
    echo usage: $(basename $0)
    echo $0 - $VERSION
    echo ""
    echo "Generate sine waves"
    echo ""
    echo "Usage:"
    echo "$0 [options]  -- <commands>"
    echo "options:"
    echo "--sh_trace"
    echo "--version             : print out version number && exit 0"
    echo "--mono                : pan stereo streams to one mono stream"
    echo "--stereo              : streo streams (default)"
    echo "--device AUDIO_OUT    : Set audio AUDIO_OUT one from 'list-devices', defaults $AUDIO_OUT"
    echo "--gain GAIN           : Volume gain, default $GAIN"
    echo "--rgain RGAIN         : Volume on right channel, default $RGAIN"
    echo "--lgain LGAIN         : Volume on left channel, default $LGAIN"
    echo "--left FREQ           : Set left ch frequency, default $LEFT_FREQ"
    echo "--right FREQ          : Set right ch frequency, default $RIGHT_FREQ"
    echo "--volume VOLUME       : Set output VOLUME"
    echo "--duration DURATION   : Set duration of generated sound file to DURATION=$DURATION secs"
    echo "--file FILE           : Use sound FILE"
    echo "--debug|-v (multiple) : increment debug level"
    echo "-?|--help             : usage"
    echo ""
    echo "commands:"
    echo "alsa-devices          : list ALSA hw devices"
    echo "list-devices          : list audio devices"
    echo "gen                   : sine signal generator RIGHT=$RIGHT_FREQ Hz, LEFT=$LEFT_FREQ Hz, GAIN=$GAIN DURATION=$DURATION s"
    echo "sine                  : generate 'sine FILE'"
    echo "play                  : play FILE"
    echo "stream URL            : stream URL"
    echo "dmsg MSG              : send MSG to kernel /dev/kmsg"
    echo "wifi-setup SSID PASSWD: configure wifi SSID and PASSWORD"
    echo "fw-download U         : Download firmware from url U to LOCAL_REPO=$LOCAL_REPO"
    echo "fw-unpack U           : Unpack firmware package in LOCAL_REPO downloaded from url U"
    echo "                        forexample U=https://github.com/jarjuk/jrr/archive/refs/tags/jrr-0.0.0.zip"
    echo "fw-pending U          : Set symbolic link to fw unpacked into LOCAL_REPO fo remote repo url U"
    echo "firmware U            : Download, unpack and mark pending in LOCAL_REPO remote repo firmware url U"        
    echo ""
    echo "Examples:"
    echo ""
    echo
    echo "# generate sine wave LEFT_FREQ=$LEFT_FREQ, RIGHT_FREQ=$RIGHT_FREQ to sound FILE=$FILE w"
    echo "$0 sine"
    echo ""
    echo "# play sound FILE=$FILE"
    echo "$0 play"
    echo ""
    echo "# stream URL"
    echo "$0 stream https://jarviradio.radiotaajuus.fi:9000/jr"
    echo ""

}

init_audio_out() {
    # Try USB ADC card
    log 2 "Init audio starts"
    log 3 "Audio devices $(aplay -L | grep '^hw:')"
    AUDIO_OUT=$(aplay -L | grep '^hw:CARD=Audio') || : 
    log 3 "Found AUDIO_OUT=$AUDIO_OUT"    
    if [ -z "$AUDIO_OUT" ]; then
        log 3 "Trying aplay -L | grep '^hw:CARD=SE' for AUDIO_OUT"    
        AUDIO_OUT=$(aplay -L | grep '^hw:CARD=SE') || : 
    fi
    if [ -z "$AUDIO_OUT" ]; then
        log 3 "Trying aplay -L | grep '^hw:CARD=Headphones' for AUDIO_OUT"    
        AUDIO_OUT=$(aplay -L | grep '^hw:CARD=Headphones') || : 
    fi
    if [ -z "$AUDIO_OUT" ]; then
        log 1 "Could not set AUDIO_OUT from $(aplay -L | grep '^hw:' || : ) devices"
    fi
    log 2 "init_audio_out: done AUDIO_OUT='$AUDIO_OUT'"

}

wget_o() {
    local source=$1
    local dest=$2

    if [ -d $dest ]; then
        dest=$dest/$(basename $source)
    fi
    log 2 "wget_o: dest=$dest, source=$source"
    wget -O $dest $source
}

unpack() {
    local url=$1; shift
    local ddir=$1; shift
    
    local packed_file=$ddir/$(basename $url)

    log 2 "unpack: url=$url, ddir=$ddir"
    log 2 "unpack: checking packed_file=$packed_file"

    if [ ! -f $packed_file ]; then
       error_msg "No file packed_file=$packed_file to unpack "
       exit 1
    fi

    log 2 "unpack: 'unzip $packed_file -d $packed_file'"
    if [ $DEBUG -ge 3 ]; then
        unzip -l $packed_file 
    fi
    # -o overwrite, -d destination directory
    unzip -o $packed_file -d $ddir

    # cleanup zipfile after unpack
    rm -f $packed_file
    
}

pending() {
    local url=$1; shift
    local ddir=$1; shift
    log 2 "pending: url=$url, ddir=$ddir"

    local pkg_name=$(basename $url)
    local version="${pkg_name%.*}"
    log 2 "pending: pkg_name=$pkg_name, version=$version"    
    
    local un_packed_directory=$ddir/jrr-$version

    # Exepect to find unpackaged directrory
    if [ ! -d $un_packed_directory ]; then
        error_msg "No directory un_packed_directory=$un_packed_directory in: '$(ls -1 $ddir)'"
        exit 1
    fi

    local un_packed_directory_src=$un_packed_directory/src
    # Expect to see src -sub directory in 'un_packed_directory'
    if [ ! -d $un_packed_directory_src ]; then
        error_msg "No directory src direcotory under un_packed_directory=$un_packed_directory in: '$(ls -1 $un_packed_directory)'"
        exit 1
        
    fi

    rm -f $PENDING_LINK 
    ln -s $un_packed_directory_src $PENDING_LINK 
}


# Options - after functions


# ------------------------------------------------------------------
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
    
	--volume)
	    shift
	    VOLUME=$1; shift
	    ;;

	--gain)
	    shift
	    GAIN=$1; shift
	    ;;
    
	--mono)
	    shift
	    MONO_OR_STEREO_CMD=",pan=mono|c0=0.5*c0+0.5*c1"
	    ;;
    
	--stereo)
	    shift
	    MONO_OR_STEREO_CMD=""
	    ;;
    
	--rgain)
	    shift
	    RGAIN=$1; shift
	    ;;

	--lgain)
	    shift
	    LGAIN=$1; shift
	    ;;

	--device)
	    shift
	    AUDIO_OUT=$1; shift
        log 2 "Opiotion --device $AUDIO_OUT"
	    ;;

	--left)
	    shift
	    # LEFT_FREQ=$1; shift
	    LEFT_FREQ=$(($1+0)); shift
	    ;;
    
	--file)
	    shift
	    FILE=$1; shift
	    ;;
    
	--duration)
	    shift
	    DURATION=$1; shift
        log 1 "set DURATION=$DURATION"
	    ;;
    
	--right)
	    shift
	    # RIGHT_FREQ=$1; shift
	    RIGHT_FREQ=$(($1+0)); shift
	    ;;
    
	
	--debug|-v)
	    shift
	    DEBUG=`expr $DEBUG + 1`
	    log 1 "DEBUG=$DEBUG"
	    ;;


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

if [ -z "$AUDIO_OUT" -o  "$AUDIO_OUT" = "-" ]; then
    log 2 "Call init audio"
    init_audio_out
fi    
log 2 "Using AUDIO_OUT=$AUDIO_OUT"

if  [ -z "$FILE" ]; then
    FILE=$SOUND_DIR/sine-${LEFT_FREQ}l-${RIGHT_FREQ}r-${DURATION}s.wav
fi

# ------------------------------------------------------------------
# actions

# Output usage - if no commands given
if [  $# -lt 1 ]; then
    usage
    exit 2
fi

DURATION_CMD=""
if [ $DURATION -gt 0 ]; then
   DURATION_CMD=":d=$DURATION"
fi
log 3 "DURATION_CMD=$DURATION_CMD"

while :
do

    log 3 "cmdline parameters left $#"
    if [  $# -lt 1 ]; then
	    break
    fi

    CMD=$1
    shift

    case "$CMD" in


        version) 
	        echo "$0 - $VERSION"
	        ;;

        true)
            ;;

        list-devices) 
            aplay -l
            echo "------------------------------------------------------------------"
            echo "Hardware devices"
            aplay -L | grep "^hw:"
            echo "------------------------------------------------------------------"
            echo "ffmpeg sinks"
            ffmpeg -sinks
	        ;;
        
        alsa-devices) 
            echo "------------------------------------------------------------------"
            echo "Alsa Hardware devices"
            aplay -L | grep "^hw:"
	        ;;

        # gen-stereo)
        #     echo "Running in host '$(hostname)' on $(date)"
        #     echo "LEFT_FREQ=$LEFT_FREQ, RIGHT_FREQ=$RIGHT_FREQ, FILE=$FILE"            
        #     echo "AUDIO_OUT=$AUDIO_OUT"
        #     echo "RGAIN=$RGAIN"
        #     echo "LGAIN=$LGAIN"
        #     echo "DURATION_CMD=$DURATION_CMD"
        #     echo "MONO_OR_STEREO_CMD=$MONO_OR_STEREO_CMD"
        #     (set -x; ffmpeg \
        #         -hide_banner -nostdin -y \
        #         -f lavfi -i "sine=frequency=$LEFT_FREQ$DURATION_CMD" \
        #         -f lavfi  -i "sine=frequency=$RIGHT_FREQ$DURATION_CMD" \
        #         -filter_complex "join=inputs=2[joined];[joined]aeval=$LGAIN*val(ch)|$RGAIN*val(ch)${MONO_OR_STEREO_CMD}[aout]" \
        #         -map "[aout]" \
        #         -ac 2 \
        #         -f alsa hw:CARD=Audio,DEV=0)
        #     ;;
        

        play)
            log 1 "Playing '$(hostname)' on $(date) AUDIO_OUT=$AUDIO_OUT FILE=$FILE"
            # MONO_OR_STEREO_CMD=", pan=mono|c0=0.5*c0+0.5*c1"
             (set -x;
                  ffmpeg \
                 -hide_banner -nostdin \
                 -i $FILE \
                 -filter_complex "[0:a]volume=volume=$GAIN ${MONO_OR_STEREO_CMD}[aout]" \
                 -map "[aout]" -ac 2 \
                 -f alsa $AUDIO_OUT \
            ) >/dev/null  2>&1
            ;;

        stream)
            echo "Running in host '$(hostname)' on $(date)"
            URL=$1
            shift
            log 1 "AUDIO_OUT=$AUDIO_OUT, URL=$URL"
            (set -x;
                  ffmpeg \
                 -hide_banner -nostdin \
                 -i $URL \
                 -filter_complex "[0:a]volume=volume=$GAIN ${MONO_OR_STEREO_CMD}[aout]" \
                 -map "[aout]" -ac 2 \
                 -f alsa $AUDIO_OUT \
            )
            ;;
        
	    
        fplay)
            echo "Running in host '$(hostname)' on $(date)"
            echo "FILE=$FILE"
            echo "AUDIO_OUT=$AUDIO_OUT"
            (set -x; ffmpeg \
                    -f alsa $AUDIO_OUT \
                    -i $FILE)
            ;;


        gen2)
            echo "Running in host '$(hostname)' on $(date)"
            echo "LEFT_FREQ=$LEFT_FREQ, RIGHT_FREQ=$RIGHT_FREQ, FILE=$FILE"            
            echo "AUDIO_OUT=$AUDIO_OUT"
            echo "RGAIN=$RGAIN"
            echo "LGAIN=$LGAIN"
            echo "DURATION_CMD=$DURATION_CMD"
            (set -x; ffmpeg \
                -hide_banner -nostdin -y \
                -f lavfi -i "sine=frequency=$LEFT_FREQ$DURATION_CMD" \
                -f lavfi  -i "sine=frequency=$RIGHT_FREQ$DURATION_CMD" \
                -filter_complex "join=inputs=2[joined];[joined]aeval=$LGAIN*val(ch)|$RGAIN*val(ch)[aout]" -map "[aout]" \
                -f alsa $AUDIO_OUT)
            ;;

        gen)
            # Config command
            echo "DURATION_CMD=$DURATION_CMD"
            echo "LEFT_FREQ=$LEFT_FREQ, RIGHT_FREQ=$RIGHT_FREQ"            
            echo "AUDIO_OUT=$AUDIO_OUT"
            echo "GAIN=$GAIN"
            echo "FILE=$FILE"
            echo "MONO_OR_STEREO_CMD=$MONO_OR_STEREO_CMD"
            (set -x ; ffmpeg \
                -hide_banner -nostdin -y \
                 -f lavfi -i "sine=frequency=$LEFT_FREQ$DURATION_CMD" \
                 -f lavfi  -i "sine=frequency=$RIGHT_FREQ$DURATION_CMD"  \
                 -filter_complex "join, volume=volume=$GAIN ${MONO_OR_STEREO_CMD}[aout]" \
                 -map "[aout]" -ac 2 -f alsa $AUDIO_OUT \
                 )
            ;;
	    
        sine)
            echo "Running in host '$(hostname)' on $(date)"
            echo "LEFT_FREQ=$LEFT_FREQ, RIGHT_FREQ=$RIGHT_FREQ, FILE=$FILE"
            (set -x; ffmpeg -nostdin -y \
                    -filter_complex "aevalsrc=exprs=sin(2*PI*$LEFT_FREQ*t)|sin(2*PI*$RIGHT_FREQ*t):s=44100:d=$DURATION" \
                    -ac 2 \
                    $FILE)
            ls -ltr $FILE
            ;;
	    

        dmesg)
            MSG=$1; shift
            sudo bash -c "echo $MSG >/dev/kmsg"
            ;;
        
        wifi-setup)
            SSID=$1; shift
            PASSI=""
            if [  $# -ge 1 ]; then
                PASSI=$1; shift
            fi
            
            if [ -z "$PASSI" ]; then
                log 1 "Setup wifi SSID=$SSID"
                sudo nmcli dev wifi connect $SSID
            else
                log 1 "Setup wifi SSID=$SSID and PASSI=$PASSI"
                sudo raspi-config nonint do_wifi_ssid_passphrase $SSID $PASSI
            fi
            ;;

        fw-download)
            # VERSION=$1; shift
            URL=$1; shift
            log 2 "fw-download URL=$URL, LOCAL_REPO=$LOCAL_REPO"
            wget_o $URL $LOCAL_REPO
            ;;
        
        fw-unpack)
            URL=$1; shift
            # VERSION=$1; shift
            log 2 "fw-upack URL=$URL, LOCAL_REPO=$LOCAL_REPO"
            unpack $URL $LOCAL_REPO
            ;;
        
        fw-pending)
            URL=$1; shift
            log 2 "fw-pending URL=$URL, LOCAL_REPO=$LOCAL_REPO"
            pending $URL $LOCAL_REPO
            ;;

        firmware)
            URL=$1; shift
            wget_o $URL $LOCAL_REPO
            unpack $URL $LOCAL_REPO
            pending $URL $LOCAL_REPO
            ;;
        
        
	    *)
	        usage
	        echo  "Unknown action: $CMD"
	        exit 3
	        ;;

    esac

done



